# 智能分析服务 (Analysis Service) - 技术设计文档

| 版本 | 日期 | 作者 | 状态 |
| :---- | :---- | :---- | :---- |
| V1.0 | 2025年8月13日 | Jules | 草稿 |

## 1. 服务概述 (Service Overview)

**服务名称:** 智能分析服务 (Analysis Service)

**技术栈:** Python, FastAPI, Pandas, (LLM SDK)

**核心职责:**
*   对已经采集并存入数据库的结构化数据，提供按需的、智能化的深度分析。
*   利用大语言模型 (LLM) 的自然语言处理能力，将复杂的数据分析结果转化为易于理解的文本报告或摘要。
*   为前端提供专门的分析类API接口，独立于主数据流（采集、配置）之外。

## 2. 核心工作流 (Core Workflow)

#### **工作流示例：生成某公司季度财报摘要**

1.  **触发:** **BFF** 根据前端用户的请求，向本服务的 `POST /api/v1/generate-report` 端点发起一个API调用。
2.  **请求定义:** 请求体中清晰地定义了分析的目标和范围。
    ```json
    {
      "report_type": "quarterly_financial_summary",
      "standard_dataset_id": 1,
      "filters": {
        "company_name": "ExampleCorp",
        "report_date": {
          "start": "2025-01-01",
          "end": "2025-03-31"
        }
      }
    }
    ```
3.  **数据提取:**
    a.  服务根据 `standard_dataset_id` 确定目标数据表的名称 (如 `data_financial_reports`)。
    b.  根据请求中的 `filters` 动态构建一条SQL查询语句，从数据库中精确地提取出所需的数据子集。
    c.  **示例SQL:** `SELECT revenue, profit, costs FROM data_financial_reports WHERE company_name = 'ExampleCorp' AND report_date >= '2025-01-01' AND report_date <= '2025-03-31';`
4.  **数据预处理:**
    a.  服务将查询到的数据加载到 **Pandas DataFrame** 中，以便进行清洗、转换或初步的统计计算（如计算环比增长率、利润率等）。
5.  **Prompt工程:**
    a.  服务将预处理后的结构化数据（例如，转换为CSV或JSON字符串格式）与具体的分析指令结合，构建一个高质量的Prompt。
    b.  **Prompt示例:**
        ```
        作为一名资深的财务分析师，请根据以下提供的季度财务数据，为ExampleCorp公司生成一份简明扼要的业绩摘要。摘要应包括收入趋势、盈利能力分析，并指出任何值得关注的亮点或潜在风险。

        数据如下:
        [此处插入预处理后的CSV或JSON格式的数据]
        ```
6.  **调用LLM & 返回结果:**
    a.  服务将Prompt发送给**大语言模型 (LLM) API**，并同步等待其返回生成的自然语言文本。
    b.  服务将LLM返回的文本包装在一个JSON对象中，直接作为API响应返回给BFF。

## 3. API 接口定义 (API Endpoint Definition)

*   **`POST /api/v1/generate-report`**
    *   **描述:** 按需生成一份由AI驱动的数据分析报告。
    *   **请求体 (Request Body):** 定义报告类型和数据过滤条件的JSON对象（如上所示）。
    *   **成功响应 (Success Response):** `200 OK`
        ```json
        {
          "report_id": "rep-q1-2025-excorp-xyz",
          "generated_at": "2025-08-13T14:30:00Z",
          "report_content": "ExampleCorp在本季度表现出强劲的增长势头，收入同比增长15%。这主要得益于其新产品的成功上市。然而，由于市场营销费用增加，利润率略有下降..."
        }
        ```

## 4. 依赖关系 (Dependencies)
*   **上游服务 (Upstream Services):**
    *   BFF: 接收其API调用。
*   **外部服务 (External Services):**
    *   大语言模型 API (OpenAI, Gemini, etc.): 核心依赖，用于生成分析报告。
*   **数据存储 (Data Stores):**
    *   PostgreSQL (应用主数据库):
        *   **读:** 从各数据表中 (`data_*`) 读取已采集的数据。
