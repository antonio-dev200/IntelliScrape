from fastapi import FastAPI
from .api import themes, tasks

# 创建BFF服务的FastAPI应用实例
app = FastAPI(
    title="IntelliScrape BFF Service",
    description="为IntelliScrape前端提供服务和业务逻辑编排的后端。",
    version="1.0.0",
)

# --- 挂载路由 ---
# 将来自不同模块的路由挂载到主应用上
app.include_router(themes.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")


@app.get("/health", summary="健康检查", tags=["Monitoring"])
def health_check():
    """
    一个简单的健康检查端点。

    当外部监控系统（如Kubernetes, Consul）调用此端点时，
    返回一个成功的响应，表明服务正在正常运行。
    """
    return {"status": "ok"}
