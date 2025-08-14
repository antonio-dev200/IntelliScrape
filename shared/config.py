# 导入os库用于读取环境变量
import os
# 导入pydantic的BaseSettings用于类型安全的配置管理
from pydantic import BaseSettings

class Settings(BaseSettings):
    """
    应用配置类。

    使用pydantic的强大功能，这个类会自动从环境变量中读取和验证配置。
    这确保了我们的配置是类型安全的，并且与环境分离。
    """

    # --- 核心基础设施 ---
    # 数据库连接URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@postgres/db")

    # RabbitMQ 连接URL (用于Pika和Celery Broker)
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")

    # --- Celery 配置 ---
    # Broker URL, 指向我们的消息中间件。我们统一使用RabbitMQ。
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", RABBITMQ_URL)
    # Result Backend URL，用于存储任务的结果。可以继续使用Redis或数据库。
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

    # --- 服务间通信 ---
    # 模式发现服务 (Discovery Service) 的内部URL
    DISCOVERY_SERVICE_URL: str = os.getenv("DISCOVERY_SERVICE_URL", "http://discovery_svc:8000")

    # --- 外部服务 ---
    # 大语言模型 (LLM) 的 API Key 和基础URL
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "your_llm_api_key_here")
    LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL")


    class Config:
        # Pydantic的配置类，用于改变其行为
        # case_sensitive = True 表示环境变量的名称是大小写敏感的
        case_sensitive = True

# 创建一个全局的settings实例，应用的其他部分将从这里导入和使用配置。
settings = Settings()
