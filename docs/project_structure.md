# 项目结构设计文档

| 版本 | 日期 | 作者 | 状态 |
| :---- | :---- | :---- | :---- |
| V1.0 | 2025年8月13日 | Jules | 定稿 |

## 1. 引言 (Introduction)

本文档旨在为 IntelliScrape 项目定义一个清晰、可扩展且易于维护的目录结构。

该结构是根据项目的微服务架构量身定制的，旨在取代 `AGENTS.md` 中提到的通用项目结构，为后续的高效开发和未来部署奠定坚实的基础。

## 2. 核心设计原则 (Core Principles)

*   **服务隔离 (Service Isolation):** 每个微服务（BFF, Orchestrator等）都拥有自己独立的目录，包含其自身的业务逻辑、API定义和测试。这使得各服务可以独立开发、测试和演进。
*   **代码共享 (Shared Code):** 跨多个服务使用的通用代码，特别是数据库模型（Models）和数据库会话管理（Session），将被提取到一个独立的、可共享的库中，以遵循“不要重复自己”（DRY）的原则。
*   **配置外化 (Externalized Configuration):** 应用程序的配置（如数据库连接字符串、API密钥）与代码分离，存放在专门的 `config/` 目录中，便于在不同环境（开发、测试、生产）中使用不同的配置。
*   **职责清晰 (Clear Separation of Concerns):** 整个目录树的结构清晰地反映了系统的不同组成部分：服务、共享库、文档、脚本等。

## 3. 建议的目录结构 (Proposed Directory Structure)

```
intelliscrape/
├── .gitignore
├── AGENTS.md
├── README.md
├── requirements.txt         # 所有服务的Python依赖
├── config/                  # 配置文件目录
│   ├── default.py
│   └── production.py
├── docs/                    # 所有项目文档
│   ├── ... (PRD, 架构图, 各服务设计文档)
│   └── project_structure.md # 本文档
├── scripts/                 # 自动化脚本
│   ├── run_dev.sh
│   └── deploy.sh
├── shared/                  # 跨服务共享的Python包
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py       # 数据库会话管理
│   └── models/
│       ├── __init__.py
│       ├── base.py          # SQLAlchemy Base
│       └── core_models.py   # 核心业务模型
└── services/                # 所有微服务的根目录
    ├── __init__.py
    ├── bff/                 # API网关/BFF服务
    │   ├── __init__.py
    │   ├── main.py          # FastAPI应用入口
    │   ├── api/             # API路由模块
    │   └── tests/           # 针对BFF的单元测试
    ├── orchestrator/        # 任务编排服务
    │   ├── __init__.py
    │   ├── celery_app.py    # Celery应用入口
    │   ├── tasks.py         # Celery任务定义
    │   └── tests/
    ├── discovery_svc/       # 模式发现服务
    │   ├── __init__.py
    │   ├── main.py
    │   └── tests/
    ├── extractor_svc/       # 数据提取服务
    │   ├── __init__.py
    │   ├── consumer.py      # 消息队列消费者主程序
    │   └── tests/
    └── analysis_svc/        # 智能分析服务
        ├── __init__.py
        ├── main.py
        └── tests/
```

## 4. 目录说明 (Directory Explanations)

*   `config/`: 存放应用配置。可以使用 [Dynaconf](https://www.dynaconf.com/) 等库来加载和管理不同环境的配置。
*   `docs/`: 存放所有项目文档。
*   `scripts/`: 存放用于开发、部署、维护的shell或Python脚本。
*   `shared/`: 这是一个可安装的Python包，包含了所有服务都需要依赖的通用代码。
    *   `shared/db/`: 负责数据库连接和会话管理。
    *   `shared/models/`: 定义所有核心的SQLAlchemy数据模型。
*   `services/`: 这是所有微服务代码的存放位置。
    *   `services/<service_name>/`: 每个子目录代表一个独立的微服务。它有自己的入口文件 (`main.py` 或 `consumer.py`) 和自己的测试 (`tests/`)。
*   `requirements.txt`: 一个位于项目根目录的全局依赖文件。在单体仓库（Monorepo）的初期阶段，使用单一的依赖文件可以简化环境管理。

## 5. 设计优势 (Benefits)

*   **高可扩展性:** 当需要添加新服务时，只需在 `services/` 目录下创建一个新目录即可，对现有服务无任何影响。
*   **高可维护性:** 清晰的职责边界使得开发者可以快速定位到需要修改的代码，降低了认知负荷。
*   **独立测试:** 可以为每个服务编写和运行独立的测试套件，便于持续集成。
*   **面向未来:** 这种结构非常适合未来的容器化部署（如使用Docker和Kubernetes），每个服务可以拥有自己的Dockerfile，并被构建为独立的镜像。
