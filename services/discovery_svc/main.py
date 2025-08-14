# 导入FastAPI类
from fastapi import FastAPI

# 创建模式发现服务的FastAPI应用实例
app = FastAPI(
    title="IntelliScrape Discovery Service",
    description="负责使用AI分析数据源并发现可抓取字段的服务。",
    version="1.0.0",
)

@app.get("/health", summary="健康检查", tags=["Monitoring"])
def health_check():
    """
    一个简单的健康检查端点，用于确认服务正在正常运行。
    """
    return {"status": "ok"}

# 在未来的开发步骤中，我们会在这里实现 /discover 端点。
