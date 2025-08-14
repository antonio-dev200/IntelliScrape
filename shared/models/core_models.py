# 导入SQLAlchemy所需的各种类型和函数
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    Boolean,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 从我们定义的base模块中导入Base类
from .base import Base

class StandardDataset(Base):
    """
    标准数据集模型。
    定义了一个标准化的数据集合，例如“公司财务报告”。
    每个数据集都会在数据库中对应一张动态创建的物理数据表。
    """
    __tablename__ = "standard_datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, comment="数据集的可读名称")
    description = Column(Text, comment="数据集的详细描述")
    table_name = Column(String(255), unique=True, nullable=False, comment="对应的物理数据表名")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="最后更新时间")

    # 定义关系：一个数据集可以有多个标准字段
    # lazy="selectin" 告诉SQLAlchemy在加载StandardDataset时，
    # 使用一条额外的SELECT...IN...语句来预加载所有关联的StandardField，
    # 从而避免N+1查询问题。
    standard_fields = relationship(
        "StandardField",
        back_populates="dataset",
        lazy="selectin"
    )

class StandardField(Base):
    """
    标准字段模型。
    定义了属于某个标准数据集的标准字段。
    """
    __tablename__ = "standard_fields"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("standard_datasets.id"), nullable=False, comment="关联的标准数据集ID")
    field_name = Column(String(255), nullable=False, comment="标准字段的可读名称")
    column_name = Column(String(255), nullable=False, comment="在物理数据表中对应的列名")
    data_type = Column(String(50), nullable=False, comment="该字段在物理表中的数据类型")
    description = Column(Text, comment="字段的详细描述")

    # 定义关系：一个标准字段属于一个数据集
    # 同样为反向关系设置lazy="selectin"，保持一致性。
    dataset = relationship(
        "StandardDataset",
        back_populates="standard_fields",
        lazy="selectin"
    )

class DataSource(Base):
    """
    数据来源模型。
    存储数据来源的信息，通常是网站。
    """
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="数据源的可读名称")
    url = Column(Text, nullable=False, comment="数据源的根URL")
    description = Column(Text, comment="关于该数据源的详细备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

class RawAnalysisResult(Base):
    """
    原始AI分析结果模型。
    存储由模式发现服务分析得出的原始字段和抓取规则。
    """
    __tablename__ = "raw_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True, comment="关联的数据源ID")
    theme_name = Column(String(255), nullable=False, comment="本次分析所使用的主题名称")
    analysis_instructions = Column(Text, comment="(可选) 本次分析遵循的详细指令")
    status = Column(String(50), nullable=False, index=True, comment="分析任务的状态")
    raw_fields_json = Column(JSON, comment="从LLM返回的原始JSON结果")
    error_message = Column(Text, comment="如果分析失败，记录错误信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

class CrawlConfig(Base):
    """
    抓取配置模型。
    存储针对特定数据源和数据集的、经过确认的抓取配置。
    """
    __tablename__ = "crawl_configs"

    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True, comment="关联的数据源ID")
    standard_dataset_id = Column(Integer, ForeignKey("standard_datasets.id"), nullable=False, index=True, comment="关联的标准数据集ID")
    version = Column(Integer, nullable=False, default=1, comment="配置的版本号")
    status = Column(String(50), nullable=False, index=True, comment="配置状态 (active, inactive)")
    list_item_selector = Column(Text, comment="(可选) 列表页中每个条目的选择器")
    detail_link_selector = Column(Text, comment="(可选) 在列表条目中，详情页链接的选择器")
    field_selectors_json = Column(JSON, nullable=False, comment="包含详情页字段映射和选择器的JSON")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

class CrawlTask(Base):
    """
    数据抓取任务模型。
    存储用户创建的数据抓取任务。
    """
    __tablename__ = "crawl_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="任务的可读名称")
    standard_dataset_id = Column(Integer, ForeignKey("standard_datasets.id"), nullable=False, index=True, comment="关联的标准数据集ID")
    data_source_ids = Column(ARRAY(Integer), nullable=False, comment="本次任务要抓取的数据源ID数组")
    schedule_cron = Column(String(100), comment="(可选) CRON表达式，定义周期性执行计划")
    status = Column(String(50), nullable=False, index=True, comment="任务状态")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
