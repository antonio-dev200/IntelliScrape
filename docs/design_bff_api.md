# API Gateway / BFF 服务- 技术设计文档

| 版本 | 日期 | 作者 | 状态 |
| :---- | :---- | :---- | :---- |
| V1.0 | 2025年8月13日 | Jules | 草稿 |

## 1. 服务概述 (Service Overview)

**服务名称:** API Gateway / BFF (Backend for Frontend)

**核心职责:**
*   为Web管理后台提供统一、安全的 RESTful API 端点。
*   封装核心业务逻辑，特别是“**主题配置与标准化**”工作流。
*   作为请求的协调者，与下游服务（如任务编排服务、智能分析服务）和数据库进行交互。
*   处理用户认证与授权（范围待定）。

## 2. 核心逻辑：主题标准化工作流 (Core Logic: Theme Standardization)

BFF 负责编排整个“主题配置与标准化”流程，该流程分为三个主要阶段：

#### **阶段一：发起分析 (Initiate Analysis)**
1.  **触发:** 前端通过调用 `POST /api/v1/themes/analyze` 发起请求，请求体中包含 `theme_name` 和 `data_source_ids` 数组。
2.  **分发:** BFF 收到请求后，会遍历 `data_source_ids` 列表。对于每一个 `data_source_id`，它会向**任务编排服务 (Task Orchestrator)** 发起一个异步的分析任务请求。
3.  **响应:** BFF 立即向前端返回 `202 Accepted` 状态码，表示任务已成功接收并正在后台处理。

#### **阶段二：加载与展现标准化工作台 (Load Standardization Workbench)**
1.  **触发:** 前端通过 `GET /api/v1/themes/{theme_name}/workbench` 请求特定主题的“标准化工作台”数据。
2.  **数据聚合:** BFF 执行以下操作：
    a.  从 `raw_analysis_results` 表中，查询指定 `theme_name` 且状态为“成功”的所有原始分析结果。
    b.  如果该主题已存在，则从 `standard_fields` 表中加载已有的标准字段。
    c.  **执行归并与推荐算法:** 这是BFF的核心智能。它会将来自多个数据源的原始字段进行聚合、去重，并根据名称相似度和出现频率，智能推荐可作为“标准字段”的候选项。同时，它也会尝试将新发现的字段与已存在的标准字段进行匹配。
3.  **响应:** BFF 将一个结构化的JSON对象返回给前端，该对象清晰地划分了“已有标准”、“推荐标准”、“各来源特有字段”等，供前端渲染工作台界面。

#### **阶段三：确认与生成配置 (Finalize Standardization)**
1.  **触发:** 管理员在前端完成所有字段的映射、提升和忽略操作后，前端将最终的标准化配置方案提交给 `POST /api/v1/themes/{theme_name}/standardize`。
2.  **原子化写入:** BFF 在一个**数据库事务**中执行所有写操作，以保证数据一致性：
    a.  创建或更新 `standard_datasets` 表中的主条目。
    b.  基于最终配置，创建或更新 `standard_fields` 表中的标准字段。
    c.  为每一个关联的数据源，在 `crawl_configs` 表中创建或更新其抓取配置，并将 `status` 设置为 `active`。
3.  **响应:** 成功后，向前端返回 `200 OK`，并附带更新后的主题摘要信息。

## 3. API 接口定义 (API Endpoint Definitions)

### 3.1 主题管理 (Theme Management)
*   **`POST /api/v1/themes/analyze`**
    *   **描述:** 批量触发对多个数据源的AI分析。
    *   **请求体 (Request Body):**
        ```json
        {
          "theme_name": "公司财报",
          "data_source_ids": [1, 2, 5]
        }
        ```
    *   **成功响应 (Success Response):** `202 Accepted`

*   **`GET /api/v1/themes/{theme_name}/workbench`**
    *   **描述:** 获取“标准化工作台”所需的所有数据。
    *   **路径参数:** `theme_name` (string, required)
    *   **成功响应 (Success Response):** `200 OK`，返回结构化JSON（详细结构待定）。

*   **`POST /api/v1/themes/{theme_name}/standardize`**
    *   **描述:** 提交最终的标准化配置。
    *   **路径参数:** `theme_name` (string, required)
    *   **请求体 (Request Body):** 包含字段映射、新增标准、忽略列表等信息的复杂JSON对象。
    *   **成功响应 (Success Response):** `200 OK`

### 3.2 抓取任务管理 (Crawl Task Management)
*   **`POST /api/v1/crawl-tasks`**
    *   **描述:** 创建一个新的抓取任务。
    *   **请求体 (Request Body):**
        ```json
        {
          "task_name": "每日财报采集",
          "standard_dataset_id": 1,
          "data_source_ids": [1, 5],
          "schedule_type": "daily"
        }
        ```
    *   **成功响应 (Success Response):** `201 Created`

*   **`GET /api/v1/crawl-tasks`**
    *   **描述:** 获取所有抓取任务的列表。
    *   **成功响应 (Success Response):** `200 OK`

## 4. 依赖关系 (Dependencies)
*   **下游服务 (Downstream Services):**
    *   任务编排服务 (Task Orchestrator): 用于分发异步任务。
    *   智能分析服务 (Analysis Service): 可能用于获取分析报告。
*   **数据存储 (Data Stores):**
    *   PostgreSQL (应用主数据库): 所有核心业务表的读写操作。
