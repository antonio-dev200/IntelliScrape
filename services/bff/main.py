# 导入FastAPI类
from fastapi import FastAPI

# 创建BFF服务的FastAPI应用实例
# title 参数将显示在自动生成的API文档（如Swagger UI）的顶部
app = FastAPI(
    title="IntelliScrape BFF Service",
    description="为IntelliScrape前端提供服务和业务逻辑编排的后端。",
    version="1.0.0",
)

@app.get("/health", summary="健康检查", tags=["Monitoring"])
def health_check():
    """
    一个简单的健康检查端点。

    当外部监控系统（如Kubernetes, Consul）调用此端点时，
    返回一个成功的响应，表明服务正在正常运行。
    """
    return {"status": "ok"}

# 在未来的开发步骤中，我们会在这里通过 app.include_router()
# 来挂载更多来自 api/ 目录下的路由模块。
