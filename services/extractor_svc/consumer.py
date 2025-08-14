import json
import logging
import pika
from pika.exceptions import AMQPConnectionError
import time
from sqlalchemy import (
    create_engine, Table, MetaData, inspect, Column, Integer, String, Text, JSON, orm
)
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

# --- 类型映射 ---
def get_sqlalchemy_type(type_string: str):
    """将字符串类型映射到SQLAlchemy类型。"""
    mapping = {
        "String": String,
        "Text": Text,
        "Integer": Integer,
    }
    return mapping.get(type_string, String) # 默认为String

# --- 动态表创建 ---
def create_dynamic_table_if_not_exists(dataset: StandardDataset) -> Table:
    """
    检查动态表是否存在，如果不存在，则根据StandardFields元数据创建它。
    返回一个SQLAlchemy的Table对象。
    """
    table_name = dataset.table_name
    metadata = MetaData()
    inspector = inspect(engine)

    if inspector.has_table(table_name):
        logger.info(f"表 '{table_name}' 已存在，直接加载。")
        return Table(table_name, metadata, autoload_with=engine)

    logger.info(f"表 '{table_name}' 不存在，开始创建...")

    # 定义表结构
    columns = [
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('extra_data', JSON)
    ]
    for field in dataset.standard_fields:
        col_type = get_sqlalchemy_type(field.data_type)
        columns.append(Column(field.column_name, col_type, nullable=True))

    dynamic_table = Table(table_name, metadata, *columns)

    # 执行DDL创建表
    try:
        metadata.create_all(engine)
        logger.info(f"成功创建表 '{table_name}'。")
        return dynamic_table
    except Exception as e:
        logger.error(f"创建动态表 '{table_name}' 时失败: {e}")
        raise

# --- 核心提取逻辑 ---
def extract_data(db: Session, crawl_config: CrawlConfig):
    """根据抓取配置，使用Playwright提取数据。"""
    # ... (此函数内容保持不变) ...
    logger.info(f"正在使用 Playwright 访问 URL: {crawl_config.data_source.url} (基于 config_id: {crawl_config.id})")
    data = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(crawl_config.data_source.url, wait_until="networkidle")

        selectors = crawl_config.field_selectors_json

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

        if extra_data:
            data['extra_data'] = extra_data

        browser.close()
    logger.info(f"数据提取完成。提取到 {len(data)} 个字段。")
    return data


def save_data_to_dynamic_table(db: Session, dynamic_table: Table, data: dict):
    """将提取的数据保存到动态创建的数据表中。"""
    logger.info(f"准备将数据存入动态表: '{dynamic_table.name}'")
    try:
        valid_data = {k: v for k, v in data.items() if k in dynamic_table.c}
        if not valid_data:
            logger.warning("没有有效的可插入数据。")
            return

        stmt = dynamic_table.insert().values(**valid_data)
        db.execute(stmt)
        db.commit()
        logger.info(f"成功将一条记录存入表 '{dynamic_table.name}'。")
    except Exception as e:
        db.rollback()
        logger.error(f"向动态表 '{dynamic_table.name}' 存入数据时失败: {e}")
        raise

# --- RabbitMQ 消费者回调 ---
def callback(ch, method, properties, body):
    """处理从RabbitMQ接收到的消息。"""
    logger.info("接收到一条新消息...")
    db = SessionLocal()
    dynamic_table = None
    try:
        payload = json.loads(body)
        config_id = payload.get("crawl_config_id")
        if not config_id:
            logger.error("消息格式错误，缺少 'crawl_config_id'。")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        logger.info(f"正在处理 crawl_config_id: {config_id}")
        crawl_config = db.query(CrawlConfig).options(
            # 预加载关联数据，避免N+1查询
            orm.joinedload(CrawlConfig.standard_dataset).joinedload(StandardDataset.standard_fields),
            orm.joinedload(CrawlConfig.data_source)
        ).filter(CrawlConfig.id == config_id).first()

        if not crawl_config:
            logger.error(f"未找到 ID 为 {config_id} 的抓取配置。")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # 1. 确保动态表和ORM模型存在 (关键步骤提前)
        dynamic_table = create_dynamic_table_if_not_exists(crawl_config.standard_dataset)

        # 2. 提取数据
        extracted_data = extract_data(db, crawl_config)

        # 3. 存储数据
        if extracted_data and dynamic_table is not None:
            save_data_to_dynamic_table(db, dynamic_table, extracted_data)

        # 4. 确认消息
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"消息处理完成并已确认。")

    except Exception as e:
        logger.error(f"处理消息时发生未知错误: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        db.close()

# --- 主函数 ---
def main():
    """主函数，设置并启动RabbitMQ消费者。"""
    # ... (此函数内容保持不变) ...
    while True:
        try:
            logger.info("正在连接到 RabbitMQ...")
            connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
            channel = connection.channel()

            queue_name = "extraction_queue"
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)
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
