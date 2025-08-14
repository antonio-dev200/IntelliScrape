from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Table, MetaData, select, text, column
from typing import List, Dict, Any

# 导入共享模块
from shared.config import settings
from shared.db.session import get_db
from shared.models.core_models import StandardDataset

# 创建FastAPI应用实例
app = FastAPI(
    title="IntelliScrape Analysis Service",
    description="负责对已采集的数据进行深度分析和报告生成。",
    version="1.0.0",
)

engine = create_engine(settings.DATABASE_URL)

# --- Pydantic 模型 ---
class ReportFilter(BaseModel):
    column: str
    operator: str # e.g., "eq", "gt", "lt", "like"
    value: Any

class ReportRequest(BaseModel):
    standard_dataset_id: int
    columns: List[str]
    filters: List[ReportFilter] = []

# --- API 端点 ---
@app.post("/generate-report", summary="根据动态条件查询数据并生成报告")
async def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    根据指定的数据集、列和过滤器，安全地动态查询数据。
    本端点的实现严格遵循安全准则，避免使用f-string拼接SQL。
    """
    # 1. 获取动态表名
    dataset = db.query(StandardDataset).filter(StandardDataset.id == request.standard_dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="StandardDataset not found.")

    table_name = dataset.table_name
    metadata = MetaData()

    try:
        # 2. 安全地引用表和列
        dynamic_table = Table(table_name, metadata, autoload_with=engine)

        # 验证请求的列是否存在于表中
        selectable_columns = []
        for col_name in request.columns:
            if col_name not in dynamic_table.c:
                raise HTTPException(status_code=400, detail=f"Column '{col_name}' not found in table '{table_name}'.")
            selectable_columns.append(column(col_name))

        # 3. 使用SQLAlchemy Core Expression Language构建查询
        stmt = select(*selectable_columns)

        # 4. 安全地应用过滤器
        for f in request.filters:
            if f.column not in dynamic_table.c:
                raise HTTPException(status_code=400, detail=f"Filter column '{f.column}' not found in table '{table_name}'.")

            table_column = dynamic_table.c[f.column]

            if f.operator == "eq":
                stmt = stmt.where(table_column == f.value)
            elif f.operator == "gt":
                stmt = stmt.where(table_column > f.value)
            elif f.operator == "lt":
                stmt = stmt.where(table_column < f.value)
            elif f.operator == "like":
                stmt = stmt.where(table_column.like(f"%{f.value}%"))
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported filter operator: '{f.operator}'.")

        # 5. 执行查询
        result = db.execute(stmt).mappings().all()

        # 在真实场景中，这里会将结果发送给LLM进行分析和报告生成。
        # 目前，我们只返回查询到的原始数据。
        return {
            "message": "Data successfully queried. Report generation would proceed from here.",
            "data": result
        }

    except Exception as e:
        # 处理表不存在等数据库错误
        raise HTTPException(status_code=500, detail=f"An error occurred while querying data: {str(e)}")


@app.get("/health", summary="健康检查", tags=["Monitoring"])
def health_check():
    """
    一个简单的健康检查端点，用于确认服务正在正常运行。
    """
    return {"status": "ok"}
