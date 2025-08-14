# 导入FastAPI类
from fastapi import FastAPI

# 创建智能分析服务的FastAPI应用实例
app = FastAPI(
    title="IntelliScrape Analysis Service",
    description="负责对已采集的数据进行深度分析和报告生成。",
    version="1.0.0",
)

@app.get("/health", summary="健康检查", tags=["Monitoring"])
def health_check():
    """
    一个简单的健康检查端点，用于确认服务正在正常运行。
    """
    return {"status": "ok"}

# 在未来的开发步骤中，我们会在这里实现 /generate-report 等端点。
