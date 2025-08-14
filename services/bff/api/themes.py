from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Dict, Any

# 导入共享模块和数据库模型
from shared.db.session import get_db
from shared.models.core_models import StandardDataset, StandardField, RawAnalysisResult, CrawlConfig

# 导入Orchestrator的Celery应用实例以发送任务
from services.orchestrator.celery_app import celery_app

router = APIRouter(
    prefix="/themes",
    tags=["Theme Management"],
)

# --- Pydantic 模型 ---
class AnalyzeRequest(BaseModel):
    data_source_id: int
    theme_name: str

class WorkbenchField(BaseModel):
    """工作台中单个字段的表示"""
    name: str
    count: int
    sources_count: int
    selectors: Dict[str, int] # selector: count

class WorkbenchResponse(BaseModel):
    """GET /workbench 的响应模型"""
    existing_standard_fields: List[str]
    discovered_fields: List[WorkbenchField]
    recommendations: List[str]

class StandardizeField(BaseModel):
    field_name: str
    description: str = ""
    data_type: str # e.g., "String", "Integer", "Text"

class FieldNameMapping(BaseModel):
    field_name: str
    selector: str

class SourceConfigPayload(BaseModel):
    data_source_id: int
    # The payload from the frontend will use field_name for mapping
    mappings: List[FieldNameMapping]
    extra_fields: List[Dict[str, str]] # e.g., [{"field_name": "rating", "selector": ".rating"}]

class StandardizeRequest(BaseModel):
    theme_name: str
    description: str = ""
    fields_to_standardize: List[StandardizeField]
    source_configs: List[SourceConfigPayload]


# --- API 端点实现 ---
class AnalysisStatus(BaseModel):
    data_source_id: int
    status: str
    error_message: str | None = None

@router.get("/analysis_status", response_model=List[AnalysisStatus])
async def get_analysis_status(theme_name: str, db: Session = Depends(get_db)):
    """
    根据主题名称查询所有相关分析任务的最新状态。
    """
    results = db.query(
        RawAnalysisResult.data_source_id,
        RawAnalysisResult.status,
        RawAnalysisResult.error_message
    ).filter(RawAnalysisResult.theme_name == theme_name).all()

    if not results:
        return []

    # 返回每个数据源的最新状态
    # 注意：如果同一数据源有多个分析记录，这里可以增加逻辑来返回最新的一个
    return [AnalysisStatus(
        data_source_id=r.data_source_id,
        status=r.status,
        error_message=r.error_message
    ) for r in results]


@router.post("/standardize", status_code=201)
async def standardize_theme(request: StandardizeRequest, db: Session = Depends(get_db)):
    """
    接收标准化的最终配置，并在一个原子事务中更新所有相关的数据库表。
    """
    try:
        # 1. 查找或创建 StandardDataset
        dataset = db.query(StandardDataset).filter(StandardDataset.name == request.theme_name).first()
        if not dataset:
            # table_name 应该是一个安全、唯一的名称，这里用 theme_name 清理后的版本
            table_name = f"data_{request.theme_name.lower().replace(' ', '_')}"
            dataset = StandardDataset(
                name=request.theme_name,
                description=request.description,
                table_name=table_name
            )
            db.add(dataset)
            db.flush()  # 在提交前将更改同步到数据库，以获取新生成的dataset.id

        # 2. 创建新的 StandardField
        for field_data in request.fields_to_standardize:
            # 检查字段是否已存在，避免重复创建
            existing_field = db.query(StandardField).filter(
                StandardField.dataset_id == dataset.id,
                StandardField.field_name == field_data.field_name
            ).first()
            if not existing_field:
                # column_name 同样需要清理
                column_name = field_data.field_name.lower().replace(' ', '_')
                new_field = StandardField(
                    dataset_id=dataset.id,
                    field_name=field_data.field_name,
                    description=field_data.description,
                    data_type=field_data.data_type,
                    column_name=column_name
                )
                db.add(new_field)

        # 3. 创建一个 field_name -> field_id 的映射
        db.flush() # 确保所有新创建的StandardField都有ID
        all_fields_in_dataset = db.query(StandardField).filter(StandardField.dataset_id == dataset.id).all()
        name_to_id_map = {f.field_name: f.id for f in all_fields_in_dataset}

        # 4. 为每个数据源创建 CrawlConfig
        for source_config in request.source_configs:
            # (可选) 停用旧配置
            db.query(CrawlConfig).filter(
                CrawlConfig.data_source_id == source_config.data_source_id,
                CrawlConfig.standard_dataset_id == dataset.id
            ).update({"status": "inactive"})

            # 构建将要存储到数据库的 field_selectors_json
            # 它需要使用 standard_field_id
            db_mappings = []
            for mapping in source_config.mappings:
                field_id = name_to_id_map.get(mapping.field_name)
                if field_id:
                    db_mappings.append({
                        "standard_field_id": field_id,
                        "selector": mapping.selector
                    })

            final_selectors_json = {
                "mappings": db_mappings,
                "extra_fields": source_config.extra_fields
            }

            # 创建新配置
            new_crawl_config = CrawlConfig(
                data_source_id=source_config.data_source_id,
                standard_dataset_id=dataset.id,
                field_selectors_json=final_selectors_json,
                status="active",
                version=1 # 简化处理，版本管理可后续增强
            )
            db.add(new_crawl_config)

        db.commit()
        return {"message": f"Theme '{request.theme_name}' has been successfully standardized."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred during standardization: {e}")


@router.get("/{theme_name}/workbench", response_model=WorkbenchResponse)
async def get_workbench_data(theme_name: str, db: Session = Depends(get_db)):
    """
    为“标准化工作台”提供数据。
    它会聚合所有原始分析结果，并提供标准化建议。
    """
    # 1. 查询现有的标准数据集和字段
    dataset = db.query(StandardDataset).filter(StandardDataset.name == theme_name).first()
    existing_fields = []
    if dataset:
        existing_fields = [f.field_name for f in dataset.standard_fields]

    # 2. 查询所有已完成的原始分析结果
    results = db.query(RawAnalysisResult).filter(
        RawAnalysisResult.theme_name == theme_name,
        RawAnalysisResult.status == "completed"
    ).all()

    if not results:
        return WorkbenchResponse(
            existing_standard_fields=existing_fields,
            discovered_fields=[],
            recommendations=[]
        )

    # 3. 聚合所有来源的字段
    aggregated_fields: Dict[str, Dict[str, Any]] = {}
    sources_count = len(results)

    for result in results:
        if not result.raw_fields_json or "fields" not in result.raw_fields_json:
            continue

        # 使用set来确保每个来源只对一个字段名计数一次
        seen_fields_in_source = set()
        for field in result.raw_fields_json["fields"]:
            field_name = field.get("field_name")
            selector = field.get("selector")
            if not field_name or not selector:
                continue

            if field_name not in aggregated_fields:
                aggregated_fields[field_name] = {"count": 0, "selectors": {}}

            # 更新选择器计数
            aggregated_fields[field_name]["selectors"][selector] = aggregated_fields[field_name]["selectors"].get(selector, 0) + 1

            if field_name not in seen_fields_in_source:
                aggregated_fields[field_name]["count"] += 1
                seen_fields_in_source.add(field_name)

    # 4. 格式化输出并生成推荐
    discovered_list = []
    recommendations = []
    for name, data in aggregated_fields.items():
        # 如果字段已经是标准字段，则不在新发现列表中展示
        if name in existing_fields:
            continue

        discovered_list.append(WorkbenchField(
            name=name,
            count=data["count"],
            sources_count=sources_count,
            selectors=data["selectors"]
        ))
        # 推荐逻辑：如果一个字段在超过一半的数据源中出现，则推荐
        if data["count"] > sources_count / 2:
            recommendations.append(name)

    return WorkbenchResponse(
        existing_standard_fields=existing_fields,
        discovered_fields=discovered_list,
        recommendations=recommendations,
    )


@router.post("/analyze", status_code=202)
async def trigger_analysis(request: AnalyzeRequest):
    """
    接收一个数据源ID和主题名称，并触发一个后台分析任务。
    """
    try:
        # 使用Celery实例按名称发送任务到队列
        # 这是一种服务间解耦的推荐做法
        celery_app.send_task(
            "orchestrator.trigger_site_analysis",
            args=[request.data_source_id, request.theme_name]
        )
        return {"message": "Analysis task has been successfully triggered."}
    except Exception as e:
        # 如果Celery Broker（如RabbitMQ）连接失败，会抛出异常
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger analysis task. Could not connect to the message broker: {e}"
        )


class StandardDatasetResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

    class Config:
        orm_mode = True

@router.get("/", response_model=List[StandardDatasetResponse])
async def list_standard_datasets(db: Session = Depends(get_db)):
    """
    列出所有已创建的标准数据集。
    """
    datasets = db.query(StandardDataset).all()
    return datasets
