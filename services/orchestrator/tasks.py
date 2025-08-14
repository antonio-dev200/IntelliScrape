# 从同级目录的celery_app模块中导入我们创建的Celery应用实例
from .celery_app import app

# 在这里定义我们的Celery任务
# 使用 @app.task 装饰器来将一个普通的Python函数转换为Celery任务

@app.task
def example_task(x, y):
    """
    一个示例任务，用于演示。
    它接收两个数字并返回它们的和。
    """
    return x + y

# 在未来的开发步骤中，我们会在这里实现
# trigger_site_analysis 和 execute_crawl_task 等核心任务。
