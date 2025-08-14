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

    # 数据库连接URL。
    # 这是一个关键配置，它告诉SQLAlchemy如何连接到我们的PostgreSQL数据库。
    # 格式: "postgresql://user:password@host:port/database"
    # 我们提供一个默认值，主要用于本地开发和测试。
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@postgres/db")

    # Celery配置
    # Broker URL，指向我们的消息中间件（例如Redis或RabbitMQ）
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    # Result Backend URL，用于存储任务的结果
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    class Config:
        # Pydantic的配置类，用于改变其行为
        # case_sensitive = True 表示环境变量的名称是大小写敏感的
        case_sensitive = True

# 创建一个全局的settings实例，应用的其他部分将从这里导入和使用配置。
settings = Settings()
