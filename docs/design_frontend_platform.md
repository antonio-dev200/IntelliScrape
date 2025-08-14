# Web管理后台 - 前端设计文档

| 版本 | 日期 | 作者 | 状态 |
| :---- | :---- | :---- | :---- |
| V1.0 | 2025年8月13日 | Jules | 草稿 |

## 1. 概述 (Overview)

本文档旨在为 IntelliScrape 项目的Web管理后台提供技术架构和核心功能的设计方案。

### 1.1. 技术选型 (Technology Stack)
*   **核心框架:** Vue 3 (Composition API)
*   **构建工具:** Vite
*   **UI组件库:** Naive UI
*   **状态管理:** Pinia
*   **路由:** Vue Router
*   **API请求库:** Axios

## 2. 项目结构 (Project Structure)

前端项目将作为 monorepo 中的一个独立服务，存在于 `services/frontend` 目录下。

```
intelliscrape/
├── ... (其他目录)
└── services/
    ├── ... (所有后端服务)
    └── frontend/
        ├── public/
        ├── src/
        │   ├── api/             # 封装对BFF的API调用
        │   │   └── index.js
        │   ├── assets/          # 静态资源 (CSS, images)
        │   ├── components/      # 可复用的全局UI组件
        │   ├── layouts/         # 页面布局 (如带侧边栏的主布局)
        │   │   └── MainLayout.vue
        │   ├── router/          # 路由配置
        │   │   └── index.js
        │   ├── store/           # Pinia store模块
        │   │   ├── theme.js
        │   │   └── task.js
        │   └── views/           # 页面级组件
        │       ├── Dashboard.vue
        │       ├── ThemeList.vue
        │       ├── Workbench.vue
        │       └── TaskList.vue
        ├── .eslintrc.js
        ├── index.html
        ├── package.json
        ├── vite.config.js
        └── ...
```

## 3. 核心页面与功能 (Core Pages & Features)

基于PRD文档，MVP版本需要实现以下核心页面：

#### 3.1. 主题管理页 (`/themes`)
*   **视图组件:** `views/ThemeList.vue`
*   **核心功能:**
    1.  以列表形式展示所有已创建的**标准数据集 (Standard Datasets)**。
    2.  提供一个“**发起主题配置**”的入口按钮。点击后，弹出一个模态框（或跳转到新页面）。
    3.  在模态框中，管理员需要：
        *   输入**主题名称**。
        *   从一个多选列表中勾选所有相关的**数据来源**。
    4.  提交后，调用BFF的 `POST /api/v1/themes/analyze` 接口。
    5.  BFF会返回一个包含 `analysis_result_ids` 的响应。前端需要为每个ID启动一个**轮询 (Polling)** 机制。
    6.  前端会每隔几秒钟，调用BFF的 `GET /api/v1/analysis-results/{id}/status` 接口来查询任务状态。
    7.  一旦所有任务的状态都变为 `completed` 或 `failed`，前端停止轮询，并向用户显示最终结果（例如，全局成功提示或某个特定数据源的失败信息）。

#### 3.2. 标准化工作台 (`/themes/:id/workbench`)
*   **视图组件:** `views/Workbench.vue`
*   **核心功能:** 这是系统中最复杂的用户界面。
    1.  页面加载时，调用BFF的 `GET /api/v1/themes/{theme_name}/workbench` 接口获取数据。
    2.  界面需要清晰地分为几个区域：
        *   **已有标准字段区:** 展示该主题已经存在的标准字段。
        *   **新发现字段区:** 以卡片或列表形式，展示从各个数据源新发现的、待处理的字段。系统推荐的“标准字段”候选项应有明显标记。
        *   **映射操作区:** 用户可以通过拖拽或下拉菜单，将“新发现字段”映射到“已有标准字段”上。
    3.  用户可以执行以下操作：
        *   **采纳推荐:** 一键采纳系统推荐的标准化方案。
        *   **手动提升:** 将某个新发现的字段手动提升为新的标准字段。
        *   **字段映射:** 将新字段映射到已有标准上。
        *   **设为特有:** 将新字段标记为某个网站的特有字段。
    4.  完成所有操作后，点击“确认并生成配置”按钮，将最终的配置方案提交给BFF的 `POST /api/v1/themes/{theme_name}/standardize` 接口。

#### 3.3. 抓取任务管理页 (`/tasks`)
*   **视图组件:** `views/TaskList.vue`
*   **核心功能:**
    1.  以列表形式展示所有已创建的**抓取任务 (Crawl Tasks)**，包括其名称、关联的数据集、状态、调度计划（CRON表达式）等。
    2.  提供“**创建新任务**”的入口。
    3.  在创建任务的表单中，管理员需要：
        *   为任务命名。
        *   选择一个已配置好的**标准数据集**。
        *   从该数据集下已配置好的来源中，勾选本次任务要执行的网站。
        *   输入任务的**CRON调度表达式**。
    4.  提交后，调用BFF的 `POST /api/v1/crawl-tasks` 接口。

## 4. 状态管理 (State Management)

使用 **Pinia** 来管理全局状态。

*   `themeStore`:
    *   `state`: `themes`, `workbenchData`, `isLoading`
    *   `actions`: `fetchThemes`, `fetchWorkbenchData`, `runAnalysis`, `finalizeStandardization`
*   `taskStore`:
    *   `state`: `tasks`, `isLoading`
    *   `actions`: `fetchTasks`, `createTask`

## 5. API交互 (API Interaction)

在 `src/api/` 目录下创建模块，使用 **Axios** 封装所有对BFF的请求，并进行统一的错误处理和加载状态管理。
