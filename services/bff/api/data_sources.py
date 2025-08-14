import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

# 导入共享模块
from shared.db.session import get_db
from shared.models.core_models import DataSource

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/data-sources",
    tags=["Data Source Management"],
)

# --- Pydantic 模型 ---
class DataSourceBase(BaseModel):
    site_key: str
    name: str
    url: str
    description: str | None = None

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceUpdate(DataSourceBase):
    pass

class DataSourceInDB(DataSourceBase):
    id: int

    class Config:
        orm_mode = True

# --- API 端点实现 ---
@router.post("/", response_model=DataSourceInDB, status_code=201)
def create_data_source(
    *,
    db: Session = Depends(get_db),
    source_in: DataSourceCreate
):
    """
    创建一个新的数据源。
    """
    # 检查site_key是否已存在
    existing_source = db.query(DataSource).filter(DataSource.site_key == source_in.site_key).first()
    if existing_source:
        raise HTTPException(
            status_code=400,
            detail=f"Data source with site_key '{source_in.site_key}' already exists.",
        )

    db_source = DataSource(**source_in.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.get("/", response_model=List[DataSourceInDB])
def list_data_sources(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    列出所有数据源。
    """
    sources = db.query(DataSource).offset(skip).limit(limit).all()
    return sources

@router.get("/{source_id}", response_model=DataSourceInDB)
def get_data_source(
    *,
    db: Session = Depends(get_db),
    source_id: int
):
    """
    获取单个数据源的详细信息。
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")
    return source

@router.put("/{source_id}", response_model=DataSourceInDB)
def update_data_source(
    *,
    db: Session = Depends(get_db),
    source_id: int,
    source_in: DataSourceUpdate
):
    """
    更新一个已存在的数据源。
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")

    update_data = source_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.delete("/{source_id}", response_model=DataSourceInDB)
def delete_data_source(
    *,
    db: Session = Depends(get_db),
    source_id: int
):
    """
    删除一个数据源。
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")

    db.delete(source)
    db.commit()
    return source
