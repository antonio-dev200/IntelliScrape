# 导入Celery类
from celery import Celery
# 导入我们的共享配置
from shared.config import settings

# 创建Celery应用实例
# 第一个参数是当前应用的模块名，这对于自动生成任务名称很重要。
# broker 参数指定了消息中间件的URL。
# backend 参数指定了用于存储任务状态和结果的后端的URL。
# 我们从全局的settings对象中读取这些URL，实现了配置与代码的分离。
celery_app = Celery(
    "orchestrator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["services.orchestrator.tasks"] # 自动发现任务的模块列表
)

# 可选的Celery配置
# 例如，设置时区，确保定时任务（Celery Beat）使用正确的时间。
celery_app.conf.update(
    timezone='Asia/Shanghai',
    enable_utc=True,
)

# 这是一个好习惯，定义一个可以被其他模块导入的 app 变量
app = celery_app
