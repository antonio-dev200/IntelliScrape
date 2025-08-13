# 任务编排服务 (Task Orchestrator) - 技术设计文档

| 版本 | 日期 | 作者 | 状态 |
| :---- | :---- | :---- | :---- |
| V1.0 | 2025年8月13日 | Jules | 草稿 |

## 1. 服务概述 (Service Overview)

**服务名称:** 任务编排服务 (Task Orchestrator Service)

**技术栈:** Python, Celery, RabbitMQ (或 Kafka)

**核心职责:**
*   管理所有后台异步任务的生命周期，包括触发、分发和状态监控（待定）。
*   作为系统的“工作引擎”，接收来自上游服务（主要是BFF）的指令，并将其转化为具体的、可执行的子任务。
*   解耦重量级任务（如AI分析、数据提取），使其与主应用（BFF）的请求-响应周期分离，提高系统的响应速度和弹性。

## 2. 核心工作流 (Core Workflows)

#### **工作流一：触发AI站点分析 (Triggering AI Site Analysis)**
1.  **触发:** BFF 为一个或多个数据源调用 `trigger_site_analysis` 这个Celery任务。
    *   **任务签名:** `trigger_site_analysis(data_source_id: int, theme_name: str)`
2.  **执行:**
    a.  任务执行器 (Celery Worker) 接收到该任务。
    b.  它向**模式发现服务 (Discovery Service)** 的API端点（例如 `POST /discover`）发起一个异步的HTTP API调用。请求体中包含 `data_source_id` 和 `theme_name`。
    c.  **职责分离:** 任务编排服务在此处的职责是“触发”，而不是“等待”。它发起调用后，该任务即告完成。实际的分析工作由模式发现服务独立完成，并将结果直接写入 `raw_analysis_results` 表。
3.  **错误处理:** 如果调用模式发现服务失败（如网络错误、服务宕机），该任务应支持自动重试机制。

#### **工作流二：执行数据采集任务 (Executing a Crawl Task)**
1.  **触发:**
    *   **定时调度:** 通过 Celery Beat 定时器，根据 `crawl_tasks` 表中定义的调度计划（如“每日执行”）自动触发。
    *   **手动触发:** 管理员在前端点击“立即执行”，BFF调用相应的Celery任务。
    *   **任务签名:** `execute_crawl_task(task_id: int)`
2.  **执行:**
    a.  任务执行器接收到 `task_id`。
    b.  查询 `crawl_tasks` 表，获取任务详情，包括其关联的 `data_source_ids` 列表。
    c.  遍历 `data_source_ids`，对每一个 `data_source_id`：
        i.  在 `crawl_configs` 表中查找其**最新**且**已激活 (active)** 的抓取配置。
        ii. **防御性检查:** 如果找不到有效的配置（可能已被禁用或删除），则记录一条警告日志，并安全跳过该数据源，确保整个采集任务不因此失败。
        iii. **分发子任务:** 如果找到有效配置，则将包含 `crawl_config_id` 的消息推送至一个专用的**消息队列**（例如 `extraction_queue`）。
3.  **解耦:** 任务分发到消息队列后，编排器的职责即告完成。后续的实际数据提取工作由**数据提取服务 (Extractor Service)** 的消费者来完成。

## 3. 任务定义 (Task Definitions)

```python
# src/orchestrator/tasks.py (示例)

from .celery_app import app
import httpx

DISCOVERY_SERVICE_URL = "http://discovery-svc/discover"

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def trigger_site_analysis(self, data_source_id: int, theme_name: str):
    """
    向模式发现服务发起一个异步的站点分析请求。
    """
    try:
        # 使用异步HTTP客户端发起请求
        with httpx.Client() as client:
            response = client.post(
                DISCOVERY_SERVICE_URL,
                json={"data_source_id": data_source_id, "theme_name": theme_name},
                timeout=10.0
            )
            response.raise_for_status()
    except httpx.RequestError as exc:
        # 请求失败，触发Celery的重试机制
        raise self.retry(exc=exc)

@app.task(bind=True)
def execute_crawl_task(self, task_id: int):
    """
    执行一个数据采集任务，将其分解为多个子任务并推送到消息队列。
    """
    # ... 伪代码 ...
    # 1. db.query(CrawlTask).filter_by(id=task_id).one()
    # 2. for source_id in task.data_source_ids:
    # 3.   config = db.query(CrawlConfig).filter_by(..., status='active').latest().one_or_none()
    # 4.   if config:
    # 5.     message_queue.publish('extraction_queue', {'crawl_config_id': config.id})
    # 6.   else:
    # 7.     log.warning(f"No active config for source {source_id}")
    pass
```

## 4. 依赖关系 (Dependencies)
*   **下游服务 (Downstream Services):**
    *   模式发现服务 (Discovery Service): 异步API调用。
*   **数据存储 (Data Stores):**
    *   PostgreSQL (应用主数据库): 读取 `crawl_tasks`, `crawl_configs` 等配置表。
    *   RabbitMQ / Kafka (消息队列): 向 `extraction_queue` 推送消息。
