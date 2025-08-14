import json
import logging
import pika
import requests
from celery.exceptions import MaxRetriesExceededError

# 导入共享模块和Celery应用实例
from shared.config import settings
from shared.db.session import SessionLocal
from shared.models.core_models import CrawlTask, CrawlConfig
from .celery_app import app

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.task(bind=True, name="orchestrator.trigger_site_analysis", max_retries=3, default_retry_delay=60)
def trigger_site_analysis(self, data_source_id: int, theme_name: str):
    """
    一个Celery任务，用于调用模式发现服务(Discovery Service)的API。
    包含自动重试逻辑。
    """
    logger.info(f"触发对 data_source_id: {data_source_id} 的站点分析，主题: {theme_name}")

    discovery_url = f"{settings.DISCOVERY_SERVICE_URL}/discover"
    payload = {"data_source_id": data_source_id, "theme_name": theme_name}

    try:
        response = requests.post(discovery_url, json=payload, timeout=10)
        response.raise_for_status()  # 如果响应状态码不是2xx，则抛出HTTPError
        logger.info(f"成功调用Discovery Service: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as exc:
        logger.error(f"调用Discovery Service失败: {exc}")
        try:
            # 如果请求失败，进行指数退避重试
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.critical(f"已达到最大重试次数，放弃对 data_source_id: {data_source_id} 的分析任务。")


@app.task(name="orchestrator.execute_crawl_task")
def execute_crawl_task(crawl_task_id: int):
    """
    一个Celery任务，用于执行一个抓取任务(Crawl Task)。
    它会为任务中定义的每个数据源查找有效的抓取配置，并将子任务分发到RabbitMQ队列。
    """
    logger.info(f"开始执行抓取任务，ID: {crawl_task_id}")
    db = SessionLocal()
    try:
        # 1. 查询抓取任务详情
        crawl_task = db.query(CrawlTask).filter(CrawlTask.id == crawl_task_id).first()
        if not crawl_task:
            logger.error(f"未找到 ID 为 {crawl_task_id} 的抓取任务。")
            return

        # 2. 准备连接到RabbitMQ
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()

        # 声明队列，确保它存在。durable=True保证队列在RabbitMQ重启后依然存在。
        extraction_queue = "extraction_queue"
        channel.queue_declare(queue=extraction_queue, durable=True)

        # 3. 遍历任务中定义的所有数据源
        for source_id in crawl_task.data_source_ids:
            # 查找该数据源针对此标准数据集的、最新的、已激活的抓取配置
            crawl_config = db.query(CrawlConfig).filter(
                CrawlConfig.data_source_id == source_id,
                CrawlConfig.standard_dataset_id == crawl_task.standard_dataset_id,
                CrawlConfig.status == "active"
            ).order_by(CrawlConfig.version.desc()).first()

            if crawl_config:
                # 4. 如果找到有效配置，将包含config_id的消息发布到队列
                message_body = json.dumps({"crawl_config_id": crawl_config.id})

                channel.basic_publish(
                    exchange='',
                    routing_key=extraction_queue,
                    body=message_body,
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # 使消息持久化
                    )
                )
                logger.info(f"已将 crawl_config_id: {crawl_config.id} 的抓取子任务发送到队列 '{extraction_queue}'。")
            else:
                logger.warning(f"对于 data_source_id: {source_id} 和 standard_dataset_id: {crawl_task.standard_dataset_id}，未找到有效的抓取配置。")

        # 5. 关闭RabbitMQ连接
        connection.close()

    except Exception as e:
        logger.error(f"执行抓取任务 {crawl_task_id} 时发生未知错误: {e}")
    finally:
        # 确保数据库会话被关闭
        db.close()
