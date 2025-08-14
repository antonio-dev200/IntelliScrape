import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

# 导入共享模块和Celery应用
from shared.db.session import get_db
from shared.models.core_models import CrawlTask
from services.orchestrator.celery_app import celery_app

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/crawl-tasks",
    tags=["Crawl Task Management"],
)

# --- Pydantic 模型 ---
class CrawlTaskBase(BaseModel):
    name: str
    standard_dataset_id: int
    data_source_ids: List[int]
    schedule_cron: Optional[str] = None

class CrawlTaskCreate(CrawlTaskBase):
    pass

class CrawlTaskResponse(CrawlTaskBase):
    id: int
    status: str

    class Config:
        orm_mode = True

# --- API 端点实现 ---
@router.post("/", response_model=CrawlTaskResponse, status_code=201)
async def create_crawl_task(
    task_in: CrawlTaskCreate,
    db: Session = Depends(get_db)
):
    """
    创建一个新的数据抓取任务。
    如果任务没有设置周期性计划 (schedule_cron)，则会立即触发执行。
    """
    # 创建数据库记录
    new_task = CrawlTask(
        **task_in.dict(),
        status="pending" # 初始状态
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 如果是一次性任务，立即触发
    if not new_task.schedule_cron:
        try:
            celery_app.send_task(
                "orchestrator.execute_crawl_task",
                args=[new_task.id]
            )
            # 更新任务状态
            new_task.status = "in_progress"
            db.commit()
            db.refresh(new_task)
        except Exception as e:
            # 如果Broker连接失败，任务状态将保持pending
            logger.error(f"Failed to trigger crawl task {new_task.id}: {e}")


    return new_task

@router.get("/", response_model=List[CrawlTaskResponse])
async def list_crawl_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    列出所有已创建的数据抓取任务。
    """
    tasks = db.query(CrawlTask).offset(skip).limit(limit).all()
    return tasks
