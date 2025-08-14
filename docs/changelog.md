# 变更日志 (Changelog)

## 2025-08-13

### 设计阶段 (Design Phase)

- **初始化项目文档 (v1.0):**
  - 导入了初始的产品需求文档 (PRD) 和系统架构设计文档。

- **详细技术设计 (v2.0):**
  - 为所有核心后端服务创建了详细的技术设计文档:
    - `design_bff_api.md`
    - `design_orchestrator.md`
    - `design_discovery_svc.md`
    - `design_extractor_svc.md`
    - `design_analysis_svc.md`
  - 设计了全新的、面向微服务的项目目录结构 (`project_structure.md`)。
  - 创建了详细的数据库表结构设计文档 (`database_schema_design.md`)。
  - 创建了前端Web管理平台的设计文档 (`design_frontend_platform.md`)。

- **设计方案精细化 (v2.1 - Based on Review Reports):**
  - **Discovery Service:** 明确使用 **Playwright** 代替 `httpx` 来处理动态网页，并更新了技术栈和工作流描述。
  - **Database Schema:**
    - `crawl_configs` 表: 增加了 `list_item_selector` 和 `detail_link_selector` 字段以支持列表页抓取。
    - `crawl_tasks` 表: 使用 `schedule_cron` 字段替换了原有的 `schedule_type`，并重构了 `status` 字段的枚举值，使其状态机更严谨。
    - `data_sources` 表: 增加了 `description` 字段。
    - `raw_analysis_results` 表: 增加了 `analysis_instructions` 字段以支持复杂的AI分析指令。
    - 为所有需要频繁查询的字段（外键、状态字段）增加了**索引建议**。
  - **Orchestrator Service:** 移除了硬编码的服务URL，并增加了从外部配置加载的明确说明。
  - **BFF Service:**
    - 增加了对 `analysis_instructions` 字段的支持。
    - 新增了 `GET /api/v1/analysis-results/{id}/status` 接口以支持前端轮询。
    - 明确了 `table_name` 的生成规则。
    - 记录了关于“标准化服务化”的长期演进建议。
  - **Frontend:** 更新了前端设计，以支持对后台长任务的状态轮询。

- **工作流程与规范定义 (AGENTS.md):**
  - 在 `AGENTS.md` 中增加了多项开发规则，包括：
    - 详尽的中文注释要求。
    - “执行-验证”循环的开发流程。
    - “理解并澄清”的需求沟通模式。
    - “自动提交”以提高效率。
    - “维护变更日志”的元规则。

### 开发阶段 (Development Phase)

- **项目骨架搭建 (v3.0):**
  - **步骤1: 初始化项目结构.** 根据设计文档创建了完整的项目目录结构。
