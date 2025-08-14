import asyncio
import logging
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from playwright.async_api import async_playwright

# 导入共享模块
from shared.db.session import get_db
from shared.models.core_models import DataSource, RawAnalysisResult

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建模式发现服务的FastAPI应用实例
app = FastAPI(
    title="IntelliScrape Discovery Service",
    description="负责使用AI分析数据源并发现可抓取字段的服务。",
    version="1.0.0",
)

# --- Pydantic 模型 ---
class DiscoveryRequest(BaseModel):
    """/discover 端点的请求体模型"""
    data_source_id: int
    theme_name: str

# --- 模拟 LLM ---
async def mock_llm_analyze(html_content: str) -> dict:
    """
    一个模拟的LLM分析函数。
    在真实场景中，这里会调用一个外部的LLM API。
    """
    logger.info("模拟LLM分析开始...")
    # 模拟网络延迟和处理时间
    await asyncio.sleep(5)

    # 模拟LLM返回的结构化数据
    # 注意：这里的示例选择器是虚构的，仅用于演示
    mocked_result = {
        "fields": [
            {"field_name": "title", "selector": "h1.article-title", "description": "文章主标题"},
            {"field_name": "author", "selector": ".author-name", "description": "文章作者"},
            {"field_name": "publish_date", "selector": "span.publish-date", "description": "发布日期"},
            {"field_name": "content", "selector": "div.article-content", "description": "正文内容"},
        ],
        "confidence_score": 0.95
    }
    logger.info("模拟LLM分析完成。")
    return mocked_result

# --- 核心工作流 ---
async def run_discovery_workflow(request: DiscoveryRequest, db: Session):
    """
    执行模式发现的完整工作流。
    这个函数被设计为在后台任务中运行。
    """
    logger.info(f"开始处理 data_source_id: {request.data_source_id} 的发现任务。")

    # 1. 从数据库获取数据源信息
    data_source = db.query(DataSource).filter(DataSource.id == request.data_source_id).first()
    if not data_source:
        logger.error(f"未找到 ID 为 {request.data_source_id} 的数据源。")
        # 在后台任务中，我们不能直接返回HTTPException，只能记录日志。
        # 可以在raw_analysis_results中记录失败状态。
        return

    # 2. 在 raw_analysis_results 表中创建一条新记录，初始状态为 processing
    analysis_result = RawAnalysisResult(
        data_source_id=request.data_source_id,
        theme_name=request.theme_name,
        status="processing"
    )
    db.add(analysis_result)
    db.commit()
    db.refresh(analysis_result)
    logger.info(f"为 data_source_id: {request.data_source_id} 创建了 ID 为 {analysis_result.id} 的分析记录。")

    try:
        # 3. 使用 Playwright 访问目标URL，获取完整渲染后的HTML
        logger.info(f"正在使用 Playwright 访问 URL: {data_source.url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(data_source.url, wait_until="networkidle")
            html_content = await page.content()
            await browser.close()
        logger.info(f"成功获取 URL: {data_source.url} 的HTML内容。")

        # 4. 调用LLM进行分析
        llm_output = await mock_llm_analyze(html_content)

        # 5. 将LLM返回的原始JSON结果更新到记录中
        analysis_result.raw_fields_json = llm_output
        analysis_result.status = "completed"
        logger.info(f"分析成功完成，ID: {analysis_result.id}")

    except Exception as e:
        # 6. 如果过程中出现任何异常，记录错误信息并更新状态
        error_msg = f"处理过程中发生错误: {str(e)}"
        logger.error(error_msg)
        analysis_result.status = "failed"
        analysis_result.error_message = error_msg

    finally:
        # 7. 提交所有变更到数据库
        db.commit()
        logger.info(f"已提交对分析记录 ID: {analysis_result.id} 的最终状态更新。")


# --- FastAPI 端点 ---
@app.post("/discover", summary="触发一个数据源的模式发现", status_code=202)
async def discover(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    接收一个数据源ID和主题名称，启动一个后台任务来分析该网站。

    - **立即返回**: 确认请求已被接受。
    - **后台处理**: 实际的分析（包括访问网站、调用LLM）在后台异步执行。
    """
    # 快速检查数据源是否存在，以便立即给用户反馈
    data_source = db.query(DataSource).filter(DataSource.id == request.data_source_id).first()
    if not data_source:
        raise HTTPException(status_code=404, detail=f"Data source with id {request.data_source_id} not found.")

    # 将耗时的任务添加到后台
    background_tasks.add_task(run_discovery_workflow, request, db)

    return {"message": "Discovery process has been started in the background."}

@app.get("/health", summary="健康检查", tags=["Monitoring"])
def health_check():
    """
    一个简单的健康检查端点，用于确认服务正在正常运行。
    """
    return {"status": "ok"}
