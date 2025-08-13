# 数据库表结构设计文档

| 版本 | 日期 | 作者 | 状态 |
| :---- | :---- | :---- | :---- |
| V1.0 | 2025年8月13日 | Jules | 定稿 |

## 1. 引言

本文档详细定义了 IntelliScrape 项目所使用的 PostgreSQL 数据库的核心表结构。这些表是系统所有功能的数据基础。

## 2. 表结构定义

### 2.1. `standard_datasets`
存储标准数据集的定义。每个数据集对应一张动态创建的数据表。

| 列名 | 数据类型 | 约束 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | 唯一标识符 |
| `name` | `VARCHAR(255)` | `UNIQUE NOT NULL` | 数据集的可读名称 (如 "公司财务报告") |
| `description` | `TEXT` | | 数据集的详细描述 |
| `table_name` | `VARCHAR(255)` | `UNIQUE NOT NULL` | 对应的物理数据表名 (如 "data_financial_reports") |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | 最后更新时间 |

### 2.2. `standard_fields`
存储每个标准数据集包含的标准字段。

| 列名 | 数据类型 | 约束 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | 唯一标识符 |
| `dataset_id` | `INTEGER` | `REFERENCES standard_datasets(id) ON DELETE CASCADE` | 关联的标准数据集ID |
| `field_name` | `VARCHAR(255)` | `NOT NULL` | 标准字段的可读名称 (如 "总收入") |
| `column_name` | `VARCHAR(255)` | `NOT NULL` | 在物理数据表中对应的列名 (如 "total_revenue") |
| `data_type` | `VARCHAR(50)` | `NOT NULL` | 该字段在物理表中的数据类型 (如 "NUMERIC(18, 2)") |
| `description` | `TEXT` | | 字段的详细描述 |

### 2.3. `data_sources`
存储数据来源的信息，通常是网站。

| 列名 | 数据类型 | 约束 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | 唯一标识符 |
| `name` | `VARCHAR(255)` | `NOT NULL` | 数据源的可读名称 (如 "XX财经门户") |
| `url` | `TEXT` | `NOT NULL` | 数据源的根URL |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | 创建时间 |

### 2.4. `raw_analysis_results`
存储由模式发现服务（Discovery Service）利用AI分析得出的原始字段和抓取规则。

| 列名 | 数据类型 | 约束 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | 唯一标识符 |
| `data_source_id` | `INTEGER` | `REFERENCES data_sources(id)` | 关联的数据源ID |
| `theme_name` | `VARCHAR(255)` | `NOT NULL` | 本次分析所使用的主题名称 |
| `status` | `VARCHAR(50)` | `NOT NULL` | 分析任务的状态 (`processing`, `completed`, `failed`) |
| `raw_fields_json`| `JSONB` | | 从LLM返回的原始JSON结果 |
| `error_message` | `TEXT` | | 如果分析失败，记录错误信息 |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | 创建时间 |

### 2.5. `crawl_configs`
存储经过“标准化”工作台确认后的，针对特定数据源和特定数据集的抓取配置。

| 列名 | 数据类型 | 约束 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | 唯一标识符 |
| `data_source_id` | `INTEGER` | `REFERENCES data_sources(id)` | 关联的数据源ID |
| `standard_dataset_id`| `INTEGER` | `REFERENCES standard_datasets(id)` | 关联的标准数据集ID |
| `version` | `INTEGER` | `NOT NULL DEFAULT 1` | 配置的版本号 |
| `status` | `VARCHAR(50)` | `NOT NULL` | 配置状态 (`active`, `inactive`) |
| `field_selectors_json`| `JSONB` | `NOT NULL` | 包含字段映射和选择器的JSON |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | 创建时间 |

### 2.6. `crawl_tasks`
存储用户创建的数据抓取任务。

| 列名 | 数据类型 | 约束 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | 唯一标识符 |
| `name` | `VARCHAR(255)` | `NOT NULL` | 任务的可读名称 (如 "每日财报采集") |
| `standard_dataset_id`| `INTEGER` | `REFERENCES standard_datasets(id)` | 关联的标准数据集ID |
| `data_source_ids` | `INTEGER[]`| `NOT NULL` | 本次任务要抓取的数据源ID数组 |
| `schedule_type` | `VARCHAR(50)` | | 调度类型 (`once`, `daily`, `weekly`) |
| `status` | `VARCHAR(50)` | `NOT NULL` | 任务状态 (`pending`, `running`, `completed`, `failed`) |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | 创建时间 |

## 3. 动态数据表

除了上述核心表之外，系统会为每一个在 `standard_datasets` 中定义的条目，动态地创建一张对应的物理数据表。
*   表名由 `standard_datasets.table_name` 决定。
*   表的列由 `standard_fields` 中与该数据集关联的所有字段决定，列名和数据类型分别由 `column_name` 和 `data_type` 决定。
*   此外，每张动态表都会包含一个 `extra_data` (`JSONB`) 列，用于存储在抓取配置中定义的、不属于任何标准字段的“特有字段”数据。
*   还会包含 `id`, `created_at`, `source_id` 等元数据列。
