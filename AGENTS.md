# AGENTS.md - AI 代理工作指南

欢迎！该文件旨在指导 AI 软件工程师（如我）如何更好地理解和参与本项目。请在此提供关键信息，以确保我能高效、准确地完成任务。

## 1. 项目概述 (Project Overview)

*   **项目名称:** (请填写项目名称)
*   **核心目标:** (请用一两句话描述该项目的核心业务目标和价值)
*   **技术栈:** (例如: Python 3.9, Flask, React, PostgreSQL)

## 2. 代码库结构 (Codebase Structure)

（请描述主要目录和文件的用途，帮助我快速定位代码。）

*   `src/`: 存放所有核心源代码。
*   `tests/`: 存放所有测试代码。
*   `docs/`: 存放所有文档，包括产品需求文档 (PRD)。
*   `scripts/`: 存放自动化脚本（例如：部署、数据迁移）。
*   `config/`: 存放配置文件。

## 3. 如何构建和运行 (How to Build and Run)

（请提供从零开始设置和运行本项目的确切命令。）

1.  **安装依赖:** `pip install -r requirements.txt`
2.  **数据库迁移 (如需要):** `python manage.py db upgrade`
3.  **运行开发服务器:** `python app.py`

## 4. 如何测试 (How to Test)

（请提供运行测试套件所需的确切命令。）

*   **运行所有单元测试:** `pytest tests/`
*   **运行特定测试文件:** `pytest tests/test_specific_feature.py`

## 5. 编码规范 (Coding Conventions)

（请列出项目遵循的编码风格和规范。）

*   **代码风格:** 请遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范。
*   **命名约定:**
    *   变量和函数名: `snake_case`
    *   类名: `PascalCase`
*   **注释:** 请为所有公共函数和复杂的逻辑块添加清晰的 Docstrings。

## 6. 必须的检查 (Mandatory Checks)

（在请求代码审查或提交之前，我必须运行并通过以下所有检查。）

*   **代码格式化:** `black .`
*   **代码 Linter:** `flake8 src/`

---
*最后更新于: 2024-01-01*
