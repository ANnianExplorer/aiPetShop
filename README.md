<div align="center">

# PetLumina - 宠物生活管理平台

<p align="center">
  <img src="https://img.shields.io/badge/Vue-3.5-4FC08D.svg" alt="Vue 3" />
  <img src="https://img.shields.io/badge/Spring_Boot-2.7-6DB33F.svg" alt="Spring Boot" />
  <img src="https://img.shields.io/badge/Vite-6.0-646CFF.svg" alt="Vite" />
  <img src="https://img.shields.io/badge/TypeScript-5.7-blue.svg" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-4.3-38B2AC.svg" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Element_Plus-2.8-409EFF.svg" alt="Element Plus" />
  <img src="https://img.shields.io/badge/Vant-4.9-07C160.svg" alt="Vant" />
  <img src="https://img.shields.io/badge/MyBatis--Plus-3.5-red.svg" alt="MyBatis-Plus" />
  <img src="https://img.shields.io/badge/Sa--Token-1.39-orange.svg" alt="Sa-Token" />
  <img src="https://img.shields.io/badge/ECharts-5.5-AA344D.svg" alt="ECharts" />
  <img src="https://img.shields.io/badge/Python-3.12-3776AB.svg" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.162-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LangGraph-1.2-1C3C3C.svg" alt="LangGraph" />
</p>

**四端架构：移动端 App + Web 管理后台 + 后端服务 + AI Agent 运行时**

</div>

## 项目概述

PetLumina 是一个面向宠物主人的智能生活管理与社区互动平台，采用四端分离架构：

| 端 | 路径 | 技术栈 | 说明 |
|---|---|---|---|
| **移动端 App** | `pet-lumina-app/` | Vue 3.5 + Vant 4 + Tailwind CSS 3 + Pinia | 宠物主人使用的移动 Web App |
| **Web 管理后台** | `pet-lumina-web/` | Vue 3.5 + Element Plus 2.8 + ECharts 5 + Tailwind CSS 4 | 管理员使用的 Web 后台 |
| **后端服务** | `backend/` | Spring Boot 2.7 + MyBatis-Plus 3.5 + Sa-Token 1.39 + Redis | 业务真源：RESTful API + 数据库 |
| **AI Agent 运行时** | `backend-agent/` | Python 3.12 + FastAPI + LangGraph 1.2 | 对话编排、工具调用、长期记忆、旁路任务 |

> Agent 不直接读业务表：它带着用户的 `satoken` 调 `backend/` 的 `/api/v1`，权限模型只有一份。
> 设计与决策记录见 [`docs/`](./docs/README.md)（ADR / SPEC / SDD / REPORT 四类文档）。

## 页面预览

### 移动端 App

<div align="center">

| 登录页 | 首页 | 宠物详情 |
|:---:|:---:|:---:|
| <img src="./image/app/登录页.png" width="240" /> | <img src="./image/app/首页.png" width="240" /> | <img src="./image/app/宠物详情页面.png" width="240" /> |

| 生活记录 | 宠物社区 | 饮食健康 |
|:---:|:---:|:---:|
| <img src="./image/app/生活记录页面.png" width="240" /> | <img src="./image/app/宠物社区页面.png" width="240" /> | <img src="./image/app/饮食健康页面.png" width="240" /> |

| 个人中心 | 新增提醒 | 话题详情 |
|:---:|:---:|:---:|
| <img src="./image/app/个人中心页面.png" width="240" /> | <img src="./image/app/新增提醒页面.png" width="240" /> | <img src="./image/app/话题详情页面.png" width="240" /> |

</div>

### Web 管理后台

<div align="center">

| 数据概览 | 用户管理 | 宠物管理 |
|:---:|:---:|:---:|
| <img src="./image/web端/数据概览.png" width="400" /> | <img src="./image/web端/用户管理.png" width="400" /> | <img src="./image/web端/宠物管理.png" width="400" /> |

| 帖子详情 | 健康数据 | 话题管理 |
|:---:|:---:|:---:|
| <img src="./image/web端/帖子详情.png" width="400" /> | <img src="./image/web端/健康数据.png" width="400" /> | <img src="./image/web端/话题管理.png" width="400" /> |

| 添加宠物 | 违规管理 | 系统设置 |
|:---:|:---:|:---:|
| <img src="./image/web端/添加宠物.png" width="400" /> | <img src="./image/web端/违规管理.png" width="400" /> | <img src="./image/web端/系统设置.png" width="400" /> |

</div>

## 核心功能

### 移动端 App (pet-lumina-app)

| 模块 | 能力说明 |
|---|---|
| **首页仪表盘** | 宠物状态 Bento 卡片、今日提醒、社区动态流、未读通知红点 |
| **宠物管理** | 宠物档案详情、头像上传、健康评分、喂食记录、健康记录列表 |
| **生活记录** | 图文记录宠物日常、标签分类、图片轮播、分享功能 |
| **宠物社区** | 话题浏览与发布、帖子详情、评论互动、点赞收藏、用户关注 |
| **健康管理** | 健康数据录入、周度指标追踪、健康计划制定、趋势可视化 |
| **日程提醒** | 提醒创建与管理、通知中心、通知详情查看、已读/未读状态 |
| **个人中心** | 用户资料编辑、头像 COS 上传、宠物档案管理、账号安全设置 |
| **认证系统** | 登录、注册、密码重置、验证码校验 |
| **UI 交互** | 果冻动画、玻璃态面板、胶囊导航栏、卡片悬浮/呼吸/脉动常驻动效 |
| **AI 对话** | 首页「问 Lumina」入口 → 全屏对话页：SSE 流式输出、工具调用提示、引用可点回原记录、断线按游标续传 |

### Web 管理后台 (pet-lumina-web)

| 模块 | 能力说明 |
|---|---|
| **数据概览** | 用户/宠物/帖子统计、活跃趋势折线图、宠物类型分布饼图、热门帖子/话题 |
| **用户管理** | 搜索筛选、角色/状态过滤、查看详情(宠物+帖子)、禁用/启用、新增/编辑用户 |
| **宠物管理** | 全局宠物列表、搜索筛选、添加/编辑宠物、宠物详情(健康记录+主人信息)、删除 |
| **帖子管理** | 帖子列表、作者筛选、帖子详情(真实数据)、审核控制台、删除 |
| **评论管理** | 评论列表、评论者信息、搜索、删除 |
| **生活记录** | 记录列表、类型筛选、搜索、删除 |
| **话题管理** | 话题 CRUD、类别筛选、新建/编辑对话框 |
| **健康数据** | 健康记录列表、宠物ID/心情筛选、详情抽屉(趋势图+历史表) |
| **通知管理** | 通知列表、发布/编辑/取消发布/删除、状态切换 |
| **违规管理** | 敏感词库管理、违规记录审核、添加/删除敏感词 |
| **系统设置** | 版本信息、功能开关、系统配置 |
| **个人中心** | 管理员资料、安全设置、登录历史 |
| **UI 交互** | 果冻动画、毛玻璃面板、胶囊侧边栏/导航栏、卡片悬浮效果、Element Plus 中文 |
| **会话工作台** | 全部 Agent 会话：意图/路由、每轮运行轨迹（步骤/耗时/token）、引用、账号长期记忆、全局用量趋势 |

### 后端 API (backend)

| 模块 | 接口数 | 说明 |
|---|---|---|
| **认证** | 6 | 登录/注册/验证码/密码重置/登出/当前用户 |
| **用户** | 6 | 资料查询/更新/头像COS上传/密码/分页列表 |
| **宠物** | 6 | CRUD + 用户宠物列表 |
| **帖子** | 7 | CRUD + 点赞/收藏 + 作者筛选 |
| **评论** | 3 | 添加/删除/分页列表 |
| **话题** | 7 | CRUD + 关注/帖子列表 |
| **关注** | 3 | 关注/粉丝/关注列表 |
| **健康** | 8 | 数据录入/计划/周报/Dashboard |
| **提醒** | 6 | CRUD + 完成状态切换 |
| **通知** | 5 | 列表/详情/未读数/标记已读/广播机制 |
| **生活记录** | 5 | CRUD + 分页列表 |
| **文件上传** | 2 | 通用上传/图片上传(含魔数校验) |
| **管理端** | 16 | 用户/宠物/帖子/评论/话题/记录/健康/通知管理 + Dashboard + 违规管理 |

### AI Agent 运行时 (backend-agent)

| 能力 | 落地方式 | 说明 |
|---|---|---|
| **三层调度** | 规则路由 → L1 直答 / L2 ReAct（≤6 步工具）/ L3 规划 | 寒暄不花 token，查数据才走工具 |
| **工具调用** | 工具网关六道防线：白名单、通道、每轮预算、参数校验、副作用隐藏、审计摘要 | 参数里出现 `user_id` 一律拒绝，身份只从 token 来 |
| **长期记忆** | `memory_fact`（事实，带置信度）+ 规则抽取 + 三态算子（ADD/UPDATE/NOOP） | 记"名字/过敏/体重"这类低风险事实，不猜 |
| **旁路任务** | `TaskQueue`（内存 / Redis 两实现）+ 死信重放 + 启动补偿 | 记忆抽取与审计写库移出响应路径，崩溃不丢 |
| **韧性** | 用户级配额（429 + `Retry-After`）、用户维度幂等键、LLM/后端双熔断 | 重试不重复执行、不重复计费 |
| **可观测** | 单行 JSON 日志 + `x-request-id` + `/readyz` 四检 + `/metrics`（HTTP/run/工具/token/队列深度 6 组指标） | 一条请求从 `run started` 到 `run finished` 能串起来；告警可直接抓 `/metrics` |
| **契约** | SSE 五事件（route/tool/delta/done/error）+ `id:` 游标续传 | 断网重连不重放已计费内容 |
| **文档问答（RAG）** | `doc_file`/`doc_chunk` + 解析（文本/PDF/OCR/视频抽帧）+ 切分/嵌入 + `search_docs` 工具 | 上传疫苗本/体检报告后，回答带 `citation.kind=doc` 可回跳；缺 OCR/ffmpeg 时明确降级并给原因 |

## 技术架构

### 后端

| 技术 | 版本 | 用途 |
|---|---|---|
| Spring Boot | 2.7.18 | 核心框架 |
| MyBatis-Plus | 3.5.9 | ORM (BaseMapper + IService + 逻辑删除) |
| Sa-Token | 1.39.0 | 认证授权 (角色权限 + 路由拦截) |
| Redis + Redisson | - | 缓存 (验证码/限流/Session) |
| Jackson | 2.13.5 | JSON 序列化 (Long→String 防精度丢失 + Date 格式化) |
| 腾讯云 COS | - | 文件存储 (用户头像/宠物图片/帖子图片) |
| MySQL | 8.0+ | 数据库 |
| 雪花算法 | - | ID 生成 (Long 类型，前端需处理精度) |

### 移动端 App

| 技术 | 版本 | 用途 |
|---|---|---|
| Vue 3 | 3.5 | 核心框架 (Composition API + `<script setup>`) |
| Vite | 6.0 | 构建工具 |
| TypeScript | 5.7 | 类型系统 |
| Vant | 4.9 | 移动端 UI 组件库 |
| Tailwind CSS | 3.4 | 样式方案 (Material Design 3 色彩令牌) |
| Pinia | 2.3 | 状态管理 |
| Vue Router | 4.5 | 路由 (Hash 模式) |
| Axios | - | HTTP 请求 |
| Material Symbols | - | 图标库 |

### Web 管理后台

| 技术 | 版本 | 用途 |
|---|---|---|
| Vue 3 | 3.5 | 核心框架 |
| Vite | 6.0 | 构建工具 |
| TypeScript | 5.7 | 类型系统 |
| Element Plus | 2.8 | UI 组件库 (表格/分页/标签/弹窗) |
| Tailwind CSS | 4.3 | 样式方案 (毛玻璃效果 + 果冻动画) |
| ECharts | 5.5 | 图表 (折线图/饼图/柱状图) |
| vue-echarts | 7.0 | ECharts Vue 封装 |
| Pinia | 2.3 | 状态管理 |
| Vue Router | 4.5 | 路由 (Hash 模式) |
| Material Symbols | - | 图标库 |
| Plus Jakarta Sans + Noto Sans SC | - | 字体 |

### 通用组件库 (pet-lumina-web/src/components/)

| 组件 | 说明 |
|---|---|
| `charts/TrendLineChart` | 折线趋势图 (统一 echarts 注册 + PetLumina 主题) |
| `charts/DonutChart` | 环形饼图 |
| `charts/BarChart` | 柱状图 |
| `common/PageHeader` | 标准页面标题 |
| `common/StatCard` | 统计卡片 |
| `common/SearchBar` | 搜索栏 |

### Agent 运行时 (backend-agent)

| 技术 | 版本 | 用途 |
|---|---|---|
| Python | 3.12 | 运行时 |
| FastAPI + Uvicorn | 0.162 / 0.54 | HTTP + SSE |
| LangGraph + checkpoint | 1.2 / 4.3 | 图编排与检查点（`thread_id = run_id`） |
| httpx | 0.28 | 调用 LLM 与业务后端（共享连接池） |
| Pydantic v2 | 2.14 | 工具参数校验（`extra=forbid`） |
| aiomysql | 0.3 | 会话 / 消息 / 运行 / 记忆落库 |
| redis-py | 8.1（RESP2） | 事件存储、限流、旁路任务队列 |
| ruff | 0.17 | lint 门禁 |
| pytest + pytest-asyncio | 9.2 / 1.4 | 181 项契约测试（含真机 MySQL 契约；不带 DSN 为 171） |

## 快速开始

### 环境要求

- Node.js 18+
- Java 8+
- MySQL 8.0+
- Redis 6.0+（Agent 用 Redis 5 亦可，客户端已固定 RESP2）
- Python 3.12+（仅 AI Agent 运行时需要）

### 后端启动

```bash
cd backend

# 1. 创建数据库并执行初始化脚本
mysql -u root -p < sql/init.sql

# 2. (可选) 导入开发种子数据
mysql -u root -p petlumina < sql/seed.sql

# 2.1 按序执行增量脚本（全新库也必须跑，否则缺少 Agent 表、话题归属列、违规词表）
mysql -u root -p petlumina < sql/v2.10-agent.sql
mysql -u root -p petlumina < sql/v2.11-agent-memory.sql
mysql -u root -p petlumina < sql/v2.12-agent-idempotency.sql
mysql -u root -p petlumina < sql/v2.13-notification-read.sql
mysql -u root -p petlumina < sql/v2.14-post-topic.sql
mysql -u root -p petlumina < sql/v2.15-violation.sql
mysql -u root -p petlumina < sql/v2.16-doc-rag.sql

# 3. 配置环境变量 (COS 密钥等)
export COS_SECRET_ID=your_id
export COS_SECRET_KEY=your_key
export COS_BUCKET=your_bucket
export COS_REGION=ap-shanghai
export COS_HOST=https://your-cdn.com

# 4. 配置数据库口令（二选一，仓库里不放明文口令）
#    方式 A：环境变量
export PETLUMINA_DB_USERNAME=root
export PETLUMINA_DB_PASSWORD=your_password
#    方式 B：本地私有文件（已被 .gitignore 忽略）
cp application-local.yml.example application-local.yml   # 然后改成你的口令

# 5. 启动（工作目录必须是 backend/，否则读不到 application-local.yml）
mvn spring-boot:run
```

**种子数据账号：**

| 角色 | 手机号 | 密码 |
|---|---|---|
| 管理员 | 13800000001 | 123456 |
| 普通用户 | 13800000002 ~ 13800000007 | 123456 |

### 移动端启动

```bash
cd pet-lumina-app
npm install
npm run dev        # http://localhost:5173
```

### 管理后台启动

```bash
cd pet-lumina-web
npm install
npm run dev        # http://localhost:3000
```

### AI Agent 服务启动

```bash
cd backend-agent

# 1. 建虚拟环境并装依赖（Python 3.12）
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt      # Linux/macOS: .venv/bin/python

# 2. 建 Agent 自己的表（3 个脚本按序执行）
mysql -u root -p petlumina < ../backend/sql/v2.10-agent.sql
mysql -u root -p petlumina < ../backend/sql/v2.11-agent-memory.sql
mysql -u root -p petlumina < ../backend/sql/v2.12-agent-idempotency.sql

# 3. 配置（复制后改 LLM key 与后端地址；不配 key 则只有 /healthz 可用）
cp .env.example .env

# 4. 启动（默认 :8099）
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8099
```

关键环境变量（全部带 `PET_AGENT_` 前缀，完整清单见 `backend-agent/README.md`）：

| 变量 | 默认 | 说明 |
|---|---|---|
| `PET_AGENT_ENV` | `dev` | 生产会强制校验密钥、禁用 header 鉴权 |
| `PET_AGENT_LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | — / — / `deepseek-chat` | OpenAI 兼容接口 |
| `PET_AGENT_BACKEND_BASE_URL` | `http://localhost:8080/api/v1` | 业务真源（透传用户 `satoken`） |
| `PET_AGENT_REPO_BACKEND` | `memory` | `memory`（重启即空）/ `mysql` |
| `PET_AGENT_EVENT_BACKEND` / `RATE_LIMIT_BACKEND` / `TASK_BACKEND` | `memory` / `memory` / `off` | 生产切 `redis` |

健康检查：`GET http://127.0.0.1:8099/healthz`（存活）与 `/readyz`（依赖就绪，含两项熔断状态）。

## 项目结构

三端业务概览：

```text
ai-PetShop/
├── backend/                         # Spring Boot 后端
│   ├── sql/                         # 数据库脚本 (init.sql + seed.sql + update.sql)
│   └── src/main/java/com/petlumina/backend/
│       ├── annotation/              # 自定义注解 (@AuthCheck, @RateLimiter)
│       ├── aop/                     # AOP 切面 (权限校验, 限流)
│       ├── common/                  # 通用类 (BaseResponse, PageRequest, DeleteRequest)
│       ├── config/                  # 配置 (CORS, JsonConfig, MyBatis-Plus, Redis)
│       ├── constant/                # 常量 (UserConstant, CosConstant)
│       ├── controller/
│       │   ├── user/                # 用户端 API (Auth/User/Pet/Post/Comment/Topic/
│       │   │                        #   Follow/Health/Reminder/Notification/Log/File)
│       │   └── admin/               # 管理端 API (User/Pet/Post/Comment/Log/Health/
│       │                            #   Notification/Dashboard)
│       ├── service/
│       │   ├── user/                # 用户端 Service + Impl
│       │   └── admin/               # 管理端 Service + Impl
│       ├── model/
│       │   ├── entity/              # 数据库实体 (16个)
│       │   ├── dto/                 # 请求 DTO
│       │   └── vo/                  # 响应 VO
│       ├── mapper/                  # MyBatis-Plus Mapper
│       ├── manager/
│       │   ├── cos/                 # 腾讯云 COS 管理 (CosManager)
│       │   └── auth/                # Sa-Token 权限实现
│       ├── exception/               # 异常处理 (BusinessException, GlobalExceptionHandler)
│       └── utils/                   # 工具类 (ThrowUtils)
│
├── pet-lumina-app/                  # 移动端 Vue App
│   └── src/
│       ├── api/                     # 接口请求层 (12个模块)
│       ├── components/              # 业务组件 (home/community/wellness/lifelog/profile)
│       ├── composables/             # 组合函数 (useToast)
│       ├── layout/                  # 布局 (MainLayout 胶囊导航栏)
│       ├── stores/                  # Pinia 状态 (user store)
│       ├── router/                  # 路由配置 (25+ 路由)
│       ├── types/                   # TypeScript 类型定义
│       ├── utils/                   # 工具函数 (format 日期格式化)
│       └── views/                   # 页面组件 (auth/home/community/wellness/
│                                    #   lifelog/pet/profile/schedule)
│
├── pet-lumina-web/                  # 管理后台 Vue App
│   └── src/
│       ├── api/                     # 接口请求层 (12个模块)
│       ├── assets/styles/           # 全局样式 (glass-panel, jelly 动画, depth 系统)
│       ├── components/
│       │   ├── charts/              # 图表组件 (TrendLineChart, DonutChart, BarChart)
│       │   └── common/              # 通用组件 (PageHeader, StatCard, SearchBar)
│       ├── layout/                  # 布局 (Sidebar 胶囊侧边栏, Header 胶囊导航)
│       ├── stores/                  # Pinia 状态 (admin store)
│       ├── router/                  # 路由配置 (20+ 路由)
│       ├── types/                   # TypeScript 类型定义
│       ├── utils/                   # 工具函数 (format 日期格式化)
│       ├── composables/             # 组合函数 (usePagination)
│       └── views/                   # 页面组件 (dashboard/user/pet/content/
│                                    #   health/notification/topic/settings/profile/violation)
│
└── image/                           # 项目截图
    ├── app/                         # 移动端截图 (11张)
    └── web端/                       # 管理后台截图 (9张)
```

完整结构（含 Agent 运行时与文档体系）：

```text
ai-PetShop/
├── backend/                         # Spring Boot 业务真源（13 个用户端 Controller + 8 个管理端）
│   └── sql/                         # init.sql / seed.sql / update.sql
│                                    # + v2.10-agent.sql / v2.11-agent-memory.sql / v2.12-agent-idempotency.sql
│
├── backend-agent/                   # Python Agent 运行时
│   ├── app/
│   │   ├── api/                     # 路由 / 依赖注入 / 可观测中间件 / 应用装配
│   │   ├── graph/                   # LangGraph 图：route → prepare → agent ↔ tools
│   │   ├── runtime/                 # Runner（SSE 事件）+ 事件存储（内存 / Redis Stream）
│   │   ├── tools/                   # 工具规格 / 注册表 / 网关六道防线 / 业务客户端
│   │   ├── storage/                 # 仓储协议 + 内存实现 + MySQL 实现（同一套契约测试）
│   │   ├── memory/                  # 事实抽取规则 / 三态算子 / 记忆服务
│   │   ├── tasks/                   # 旁路任务队列（内存 / Redis）+ 消费者 + worker
│   │   ├── llm/                     # ChatModel 协议 / OpenAI 兼容实现 / 脚本化桩
│   │   ├── core/                    # 错误模型 / ID 生成 / 日志 / 熔断 / 限流 / Redis 客户端
│   │   └── domain/                  # 领域模型 / 事件 / 意图路由
│   ├── tests/                       # 181 项契约级测试 + 本地桩（Java / LLM）
│   ├── evals/                       # 23 条评测用例 + 三套阈值门禁
│   ├── scripts/                     # 5 个真进程冒烟脚本
│   ├── Dockerfile                   # 多阶段构建 + 非 root
│   └── requirements.txt             # 精确锁定（意图见 requirements.in）
│
├── docs/                            # 文档地图：ADR / SPEC / SDD / PLAN / REPORT
│   ├── adr/                         # 9 条架构决策（为什么这么选）
│   ├── spec/                        # 对外契约（HTTP/SSE 与前端 UI）
│   ├── sdd/                         # 分层与依赖规则、部署、质量属性
│   ├── plans/                       # 每一步的计划与完成情况
│   └── reports/                     # 每次交付的测试报告（贴真实输出）
│
├── .github/workflows/
│   ├── deploy.yml                   # App 构建 → GitHub Pages
│   └── agent-ci.yml                 # Agent：ruff + pytest + evals + 镜像构建
│
├── pet-lumina-app/                  # 移动端（27 路由）
├── pet-lumina-web/                  # 管理后台（19 路由）
└── image/                           # 项目截图
```

## 质量门禁与文档

Agent 侧的验收是"可复现命令"，不是口头结论：

```powershell
cd backend-agent
$env:PET_AGENT_TEST_MYSQL_DSN = "mysql://root:yourpwd@127.0.0.1:3306/petlumina"
.venv\Scripts\python -m pytest            # 181 passed（含真机 MySQL 契约）
.venv\Scripts\python -m evals.run         # routing 15/15、safety 6/6、memory 2/2
.venv\Scripts\python -m scripts.e2e_smoke          # 10/10（SSE / 续传 / 越权）
.venv\Scripts\python -m scripts.p1_smoke           # 9/9（配额 / 记忆 / 用量）
.venv\Scripts\python -m scripts.admin_smoke        # 6/6（管理端权限与查询）
.venv\Scripts\python -m scripts.idempotency_smoke  # 8/8（同 key 不重复执行）
.venv\Scripts\python -m scripts.tasks_smoke        # 8/8（死信重放 / 队列现场）
.venv\Scripts\python -m scripts.real_model_smoke   # 13/13（需真 key：L1 首 token / L2 工具 / usage 一致）
.venv\Scripts\ruff.exe check .            # All checks passed
```

前端：

```bash
cd pet-lumina-app && npm run build && npm test    # vue-tsc + vitest（37 例：SSE / 聊天流 / 分类 / 提醒日期）
cd pet-lumina-web && npm run typecheck && npm run build   # 管理端 vue-tsc -b（真检查，不是空转）

cd backend && mvn test                            # 后端单测 27 例（仪表盘/排序/验证码/用户管理/发帖话题）
```

文档入口：[`docs/README.md`](./docs/README.md)（四类文档职责 + 索引），
面向决策的背景见 [`docs/pet-agent-architecture.md`](./docs/pet-agent-architecture.md)，
**还差什么**见 [`docs/BACKLOG.md`](./docs/BACKLOG.md)（原 42 条，剩 27 条；卫生债 E1–E13 已清零）。

## 更新日志

### v2.10 (2026-11-08)

**AI Agent 运行时 + 管理端会话工作台**

- 新增 `backend-agent/`：Python 3.12 + FastAPI + LangGraph，独立进程（:8099），业务权限仍由 `backend/` 判定
- 对话链路：SSE 五事件（route/tool/delta/done/error）+ `id:` 游标续传；L1 直答 / L2 ReAct 分层，寒暄不花 token
- 工具网关六道防线：白名单、通道限制、每轮预算、参数校验（拒绝伪造 `user_id`）、副作用默认隐藏、审计只存摘要
- 长期记忆：规则抽取事实（名字/过敏/体重等）+ 三态算子（ADD/UPDATE/NOOP），管理端可查"这个账号记住了什么"
- 工程基线：单行 JSON 日志 + `x-request-id`、`/readyz` 四检、依赖精确锁定、多阶段非 root 镜像、CI（ruff + pytest + evals + build）
- 韧性：用户级配额（429 + `Retry-After`）、用户维度幂等键（重试只执行一次）、LLM/后端双熔断
- 旁路任务：`TaskQueue`（内存 / Redis）+ 启动补偿 + 死信重放 + 队列现场接口
- App：首页「问 Lumina」入口 + 全屏对话页（流式、工具提示、引用回跳、历史会话恢复）+ **历史会话面板**（`GET /agent/sessions`，列表切换与刷新恢复）
- 管理端：会话工作台（会话列表 / 详情：对话流 + 运行轨迹 + 长期记忆 / 全局用量）
- 文档体系：9 条 ADR、2 份 SPEC、1 份 SDD、5 份 PLAN、9 份 REPORT（见 `docs/README.md`）
- 验收：181 单测、23 条评测、7 个真进程冒烟（10/9/6/8/8/10/11）+ 真实模型冒烟 13/13（L1 P50 929 ms / P95 1064 ms）、`ruff` 全绿

### v2.7 (2026-06-03)

**日期格式化 + 通知详情**
- 新增 `utils/format.ts` 前端日期格式化工具 (formatDate / formatDateShort)
- App 通知详情弹窗 (点击通知查看完整内容)
- 首页提醒日期格式修复 (yyyy-MM-dd → yyyy-MM-dd HH:mm:ss)
- 通知列表/帖子详情等页面日期显示统一格式化

### v2.6 (2026-06-03)

**通知系统完善 + 搜索筛选修复**
- 管理端: 发布/取消发布/编辑/删除通知，状态标签
- 用户端: 通知列表、未读红点、通知详情、标记已读
- 广播机制: 管理员发布 user_id=0 广播，用户端查询个人+广播
- 用户/宠物/评论/生活记录/帖子搜索筛选修复
- Element Plus 中文语言包

### v2.5 (2026-06-03)

**宠物管理全面升级 + 大数修复**
- Web PetDetail/AddPet/EditPet 去掉假数据，改为 API 真实数据
- App PetDetail/AddPet 新增 hero 卡片、类型选择、分组表单
- JavaScript 大数字精度丢失全局修复 (request.ts JSON 解析)
- PetEditRequest 新增 type 字段

### v2.4 (2026-06-03)

**图片上传全链路 + COS 路径分类**
- 新增 CosConstant 统一管理 COS 路径 (avatar/user, pet/image, post/image 等)
- FileController 新增魔数校验 + category 参数
- CosManager 启用 HTTPS + 自定义域名
- 四个页面 (AddUser/EditUser/AddPet/EditPet) 接入 COS 上传
- App 头像上传改用 userApi.updateAvatar (COS + 存库)

### v2.3 (2026-06-03)

**用户端果冻动画与玻璃态 UI**
- 12 个常驻动画 (呼吸/浮动/光泽/脉动/摇摆)
- 三层玻璃面板系统 + 三层深度阴影
- 果冻按钮 (btn-jelly) + 卡片悬浮 (card-lift)
- 底部导航胶囊样式 + 未高亮透明度优化

### v2.2 (2026-06-03)

**管理后台 UI 全面升级**
- 11 个新页面 (AddUser/EditUser/AddPet/EditPet/PetDetail/PostDetail/RecordDetail/SystemSettings/PersonalCenter/ViolationManage)
- 可复用组件库 (charts/ + common/)
- 侧边栏胶囊样式 + 渐变白背景
- 后端 QueryWrapper SQL 字段名修复 (驼峰→下划线)
- 后端大数字 JSON 精度丢失修复

### v2.1 (2026-06-03)

**后端目录重构 + Web 管理后台**
- controller/service 按 user/ 和 admin/ 子目录重构
- 新建管理端 API (8个 Controller + DashboardService)
- 从零搭建 pet-lumina-web 项目
- 毛玻璃 + Material Design 3 设计风格

### v2.0 (2026-06-02)

**后端开发与前后端联调**
- Spring Boot 后端全部业务模块 (12个 Controller, 55个接口)
- Sa-Token 认证 + 角色权限
- MySQL 建表脚本 + 开发种子数据
- 前端 API 层 + 20+ 页面接入真实 API

### v1.0 (2026-05-01)

**基础工程搭建**
- Vue 3 + Vite + TypeScript 项目初始化
- Tailwind CSS 设计系统 (Material Design 3 色彩)
- 全部移动端页面开发 (7大模块)
- HBuilder APK 打包适配

---

<div align="center">
  <p>内部项目 | 持续迭代中</p>
</div>
