# 数据提取服务 (Extractor Service) - 技术设计文档

| 版本 | 日期 | 作者 | 状态 |
| :---- | :---- | :---- | :---- |
| V1.0 | 2025年8月13日 | Jules | 草稿 |

## 1. 服务概述 (Service Overview)

**服务名称:** 数据提取服务 (Extractor Service)

**技术栈:** Python, Scrapy / Playwright, Pika (RabbitMQ client)

**服务类型:** 后台消费者 (Background Consumer)
*   本服务**不是**一个API服务。它作为一个或多个独立的后台进程运行，其唯一的任务就是消费消息队列中的指令。

**核心职责 (Single Responsibility):**
*   **单一职责原则:** 监听一个特定的消息队列 (`extraction_queue`)。对于队列中的每一条消息，它会根据消息内容加载一个抓取配置，执行网页抓取，并将提取到的结构化数据存入指定的数据库表中。

## 2. 核心工作流 (Core Workflow)

1.  **监听与接收:**
    *   服务启动后，会建立一个到 **RabbitMQ** (或 Kafka) 的持久连接，并开始监听 `extraction_queue`。
    *   当 **任务编排服务 (Task Orchestrator)** 向队列中推送了消息后，服务的一个消费者进程会接收到该消息。
    *   **消息格式:** `{"crawl_config_id": 123}`

2.  **配置加载:**
    *   消费者从消息中解析出 `crawl_config_id`。
    *   使用该ID查询 `crawl_configs` 表，获取完整的抓取配置，包括：
        *   关联的 `data_source_id` (用于获取目标URL)。
        *   关联的 `standard_dataset_id` (用于确定要写入哪张数据表)。
        *   核心的 `field_selectors_json`，其结构如下：
            ```json
            {
              "mappings": [
                {"standard_field_id": 1, "selector": ".title"},
                {"standard_field_id": 2, "selector": "#author"}
              ],
              "extra_fields": [
                {"field_name": "rating", "selector": ".review-rating"}
              ]
            }
            ```

3.  **页面抓取与解析:**
    *   服务使用 **Playwright** (或 Scrapy) 库来启动一个浏览器实例，并访问目标URL。选择Playwright可以确保对JavaScript动态渲染的页面有良好的兼容性。
    *   等待页面完全加载后，获取其完整的HTML内容。

4.  **数据提取与映射:**
    *   服务遍历 `field_selectors_json` 中的每一个字段映射。
    *   对于 `mappings` 中的每一个标准字段，它会在HTML上执行对应的CSS选择器，提取数据。
    *   对于 `extra_fields` 中的每一个特有字段，它也会执行相应的选择器来提取数据。
    *   所有提取出的数据会被组装成一个Python字典。

5.  **数据持久化:**
    *   服务根据 `standard_dataset_id` 确定目标数据表的名称（例如 `data_financial_reports`）。
    *   标准字段的数据被存入对应的列中。
    *   所有在 `extra_fields` 中定义的特有字段，其提取出的数据会被统一打包成一个JSON对象，存入名为 `extra_data` 的 `JSONB` 类型列中。
    *   服务执行数据库 `INSERT` 操作，将数据写入目标表。

6.  **消息确认:**
    *   只有当数据成功写入数据库后，服务才会向消息代理发送一个**确认 (ACK)**信号。这会告诉代理，该消息已被成功处理，可以从队列中安全删除。
    *   **错误处理:** 如果在抓取或写入数据库的任何环节发生可重试的错误（如网络超时），服务将不会发送ACK。这使得消息可以被重新投递给另一个消费者，实现了任务的自动重试和高可靠性。对于不可重试的错误（如无效的配置），服务会记录错误，发送ACK，并可能将该错误信息推送到一个专门的“死信队列”(Dead-Letter Queue)中，供人工排查。

## 3. 依赖关系 (Dependencies)
*   **数据存储 (Data Stores):**
    *   **PostgreSQL:**
        *   **读:** `crawl_configs`, `data_sources`, `standard_datasets`。
        *   **写:** 动态数据表 (e.g., `data_financial_reports`)。
    *   **RabbitMQ / Kafka:**
        *   **消费:** 从 `extraction_queue` 读取消息。
