# 模式发现服务 (Discovery Service) - 技术设计文档

| 版本 | 日期 | 作者 | 状态 |
| :---- | :---- | :---- | :---- |
| V1.0 | 2025年8月13日 | Jules | 草稿 |

## 1. 服务概述 (Service Overview)

**服务名称:** 模式发现服务 (Discovery Service)

**技术栈:** Python, FastAPI, httpx, (LLM SDK, e.g., OpenAI, Gemini)

**核心职责 (Single Responsibility):**
*   **单一职责原则:** 本服务的唯一目标是，针对一个给定的数据源（如URL）和一个主题（如“公司财报”），调用外部大语言模型（LLM）进行分析，并以**原始、未加工**的形式将分析结果存入数据库。
*   **无状态:** 服务本身是无状态的。它接收请求，执行任务，然后将结果持久化。它不关心“标准化”，也不关心其他数据源的分析结果。

## 2. 核心工作流 (Core Workflow)

1.  **触发:** 服务通过其唯一的API端点 `POST /discover` 接收来自**任务编排服务 (Task Orchestrator)** 的HTTP请求。
2.  **数据准备与页面抓取:**
    a.  收到请求后，服务从请求体中解析出 `data_source_id`, `theme_name`, 以及可选的 `analysis_instructions`。
    b.  使用 `data_source_id` 查询 `data_sources` 表，获取该数据源的详细信息（主要是URL）。
    c.  在 `raw_analysis_results` 表中为本次分析创建一个新记录，并将初始状态设置为 `processing`。
    d.  **(核心变更)** 服务启动 **Playwright** 浏览器实例，访问目标URL，等待页面动态内容加载完毕，然后提取最终渲染完成的HTML内容。

3.  **Prompt工程:**
    a.  服务根据 `theme_name`, `analysis_instructions` 和上一步抓取到的HTML内容，动态构建一个高质量的 **Prompt**。
    b.  **Prompt 示例:**
        ```
        作为一名专业的数据抓取工程师，你的任务是分析以下HTML内容，并找出所有与主题相关的可抓取字段。

        分析主题: [来自请求的 theme_name]

        除了上述主题，请严格遵守以下详细指令：
        [来自请求的 analysis_instructions, 如果提供的话]

        HTML内容如下:
        ```html
        [此处为Playwright抓取到的完整HTML内容]
        ```

        请基于以上HTML内容，以JSON格式返回你的发现。JSON的根节点应该是一个名为 "fields" 的数组。数组中的每个对象都应包含以下三个键：
        1. "field_name": 字段的建议名称（使用英文snake_case命名法，例如 "revenue"）。
        2. "description": 对该字段的简短描述。
        3. "selector": 用于定位该字段数据的CSS选择器。

        请确保选择器尽可能精确和稳定。如果找不到任何相关字段，请返回一个空的 "fields" 数组。
        ```
4.  **调用LLM:**
    a.  服务将包含了完整HTML的Prompt发送给外部的**大语言模型 (LLM) API**。
    b.  服务将**同步等待**LLM返回结果。这是一个耗时操作，因此本服务必须能够处理长时间运行的HTTP请求。
5.  **结果持久化:**
    a.  收到LLM的响应后，服务会进行基本的格式验证，确保返回的是一个有效的JSON。
    b.  无论JSON内容如何，服务都会将LLM返回的**完整、原始的JSON字符串**存入 `raw_analysis_results` 表中对应记录的 `raw_fields_json` 字段。
    c.  同时，将该记录的状态更新为 `completed`。
    d.  如果在此过程中的任何步骤失败（如LLM调用失败、超时、返回格式错误），则将状态更新为 `failed`，并在日志中记录详细的错误信息。

## 3. API 接口定义 (API Endpoint Definition)

*   **`POST /discover`**
    *   **描述:** 异步触发对单个数据源的AI分析。此处的“异步”是指调用方（Orchestrator）不应期望在响应中获得分析结果，但服务本身会同步处理该请求。
    *   **请求体 (Request Body):**
        ```json
        {
          "data_source_id": 1,
          "theme_name": "公司财报",
          "analysis_instructions": "(可选) 请专注于季度财报，忽略年度总结。"
        }
        ```
    *   **成功响应 (Success Response):** `200 OK`
        ```json
        {
          "status": "Analysis started",
          "analysis_result_id": 123
        }
        ```
    *   **失败响应 (Error Response):** `500 Internal Server Error`

## 4. 依赖关系 (Dependencies)
*   **外部服务 (External Services):**
    *   大语言模型 API (OpenAI, Gemini, Claude, etc.): 核心依赖，用于执行智能分析。
*   **数据存储 (Data Stores):**
    *   PostgreSQL (应用主数据库):
        *   **读:** `data_sources` (获取URL)
        *   **写:** `raw_analysis_results` (创建记录、更新状态和结果)
