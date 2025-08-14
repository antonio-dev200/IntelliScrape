import json
import logging
import pika
from pika.exceptions import AMQPConnectionError
import time
from sqlalchemy import create_engine, Table, MetaData, inspect
from sqlalchemy.orm import sessionmaker, Session
from playwright.sync_api import sync_playwright

# 导入共享模块
from shared.config import settings
from shared.models.core_models import CrawlConfig, StandardDataset, StandardField

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 数据库设置 ---
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 核心提取逻辑 ---
def extract_data(db: Session, crawl_config: CrawlConfig):
    """根据抓取配置，使用Playwright提取数据。"""
    logger.info(f"正在使用 Playwright 访问 URL: {crawl_config.data_source.url} (基于 config_id: {crawl_config.id})")
    data = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(crawl_config.data_source.url, wait_until="networkidle")

        # field_selectors_json 结构:
        # {"mappings": [{"standard_field_id": 1, "selector": ".title"}], "extra_fields": [{"field_name": "rating", "selector": ".rating"}]}
        selectors = crawl_config.field_selectors_json

        # 提取标准字段
        for mapping in selectors.get("mappings", []):
            field_id = mapping["standard_field_id"]
            selector = mapping["selector"]
            field_obj = db.query(StandardField).filter(StandardField.id == field_id).first()
            if field_obj and selector:
                try:
                    content = page.locator(selector).inner_text()
                    data[field_obj.column_name] = content.strip()
                except Exception:
                    logger.warning(f"未能使用选择器 '{selector}' 提取字段 '{field_obj.field_name}'。")

        # 提取特有字段
        extra_data = {}
        for extra_field in selectors.get("extra_fields", []):
            field_name = extra_field["field_name"]
            selector = extra_field["selector"]
            if field_name and selector:
                try:
                    content = page.locator(selector).inner_text()
                    extra_data[field_name] = content.strip()
                except Exception:
                    logger.warning(f"未能使用选择器 '{selector}' 提取特有字段 '{field_name}'。")

        # 将特有字段存入 'extra_data'
        if extra_data:
            data['extra_data'] = extra_data

        browser.close()
    logger.info(f"数据提取完成。提取到 {len(data)} 个字段。")
    return data

def save_data_to_dynamic_table(db: Session, dataset: StandardDataset, data: dict):
    """将提取的数据保存到动态创建的数据表中。"""
    table_name = dataset.table_name
    logger.info(f"准备将数据存入动态表: '{table_name}'")

    try:
        metadata = MetaData()
        # 使用inspect检查表是否存在
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            logger.error(f"错误：动态数据表 '{table_name}' 不存在于数据库中。")
            return

        dynamic_table = Table(table_name, metadata, autoload_with=engine)

        # 过滤掉data中不存在于表列的键
        valid_data = {k: v for k, v in data.items() if k in dynamic_table.c}

        if not valid_data:
            logger.warning("没有有效的可插入数据。")
            return

        stmt = dynamic_table.insert().values(**valid_data)
        db.execute(stmt)
        db.commit()
        logger.info(f"成功将一条记录存入表 '{table_name}'。")
    except Exception as e:
        db.rollback()
        logger.error(f"向动态表 '{table_name}' 存入数据时失败: {e}")
        raise

# --- RabbitMQ 消费者回调 ---
def callback(ch, method, properties, body):
    """处理从RabbitMQ接收到的消息。"""
    logger.info("接收到一条新消息...")
    db = SessionLocal()
    try:
        payload = json.loads(body)
        config_id = payload.get("crawl_config_id")
        if not config_id:
            logger.error("消息格式错误，缺少 'crawl_config_id'。")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        logger.info(f"正在处理 crawl_config_id: {config_id}")
        crawl_config = db.query(CrawlConfig).filter(CrawlConfig.id == config_id).first()

        if not crawl_config:
            logger.error(f"未找到 ID 为 {config_id} 的抓取配置。")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # 1. 提取数据
        extracted_data = extract_data(db, crawl_config)

        # 2. 存储数据
        if extracted_data:
            save_data_to_dynamic_table(db, crawl_config.standard_dataset, extracted_data)

        # 3. 确认消息
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"消息处理完成并已确认。")

    except Exception as e:
        logger.error(f"处理消息时发生未知错误: {e}")
        # 发生错误，拒绝消息，并且不重新入队，避免无限循环
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        db.close()

# --- 主函数 ---
def main():
    """主函数，设置并启动RabbitMQ消费者。"""
    while True:
        try:
            logger.info("正在连接到 RabbitMQ...")
            connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
            channel = connection.channel()

            queue_name = "extraction_queue"
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1) # 每次只取一条消息，处理完再取下一条
            channel.basic_consume(queue=queue_name, on_message_callback=callback)

            logger.info(f"[*] 等待消息在队列 '{queue_name}' 中。按 CTRL+C 退出。")
            channel.start_consuming()

        except AMQPConnectionError:
            logger.error("无法连接到 RabbitMQ。5秒后重试...")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("消费者被手动停止。")
            break
        except Exception as e:
            logger.critical(f"发生严重错误，消费者将重启: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
