# 文档地图（Pet-Agent）

> 这份索引回答一个问题：**每个阶段交付了什么，凭什么说它是对的。**

## 1. 文档类型约定

| 类型 | 目录 | 回答的问题 | 什么时候写 | 谁维护 |
| --- | --- | --- | --- | --- |
| **ADR**（架构决策记录） | `docs/adr/` | 为什么这样选，放弃了什么 | 做出不可逆或代价高的决定时 | 决策人 |
| **SPEC**（规格） | `docs/spec/` | 对外契约是什么，什么算"符合规格" | 动手前，随实现变更同步 | 实现人 |
| **SDD**（软件设计说明） | `docs/sdd/` | 系统怎么分层、模块怎么协作 | 架构成型时，重构时更新 | 架构负责人 |
| **REPORT**（交付/测试报告） | `docs/reports/` | 这一步跑了什么、输出是什么、剩什么风险 | 每个可验收里程碑 | 交付人 |
| **BACKLOG**（未完成清单） | `docs/BACKLOG.md` | 还差什么、卡在哪、什么算做完 | 每次交付后同步 | 交付人 |
| **方案/愿景** | `docs/*.md` | 产品与技术全景、路线图 | 立项时 | 架构负责人 |

规则：

1. **ADR 一旦接受不改内容**，推翻就写新 ADR 并把旧的标记为 `Superseded by ADR-XXXX`——决策史要能追溯，不能"事后修改成我当时就想到"。
2. **SPEC 写"可验证的断言"**（状态码、字段、顺序、上限），不写"应尽量"。
3. **REPORT 必须贴真实命令与真实输出**，不允许"已验证"三个字结案；没跑就说没跑。
4. **文档与代码同一次提交**，不给"下次补文档"留口子。

## 2. 现有文档

### 方案 / 总览

| 文档 | 内容 |
| --- | --- |
| [pet-agent-architecture.md](pet-agent-architecture.md) | Pet-Agent 总体方案：五条原则、分层架构、六大能力、12 张表、开源选型、四阶段路线图、成本与风险、§10 harness 选型、§11 GitHub 调研、§12 S1 落地、§13 Web 接入 |
| [BACKLOG.md](BACKLOG.md) | 未完成事项清单：P0 3 条 / P1 8 条 / P2 10 条 / P3 9 条 / 原项目卫生债 0 条（E1–E8、E13 已修），当前剩 8 条（P1 1 + P2 1 + P3 6），每条带现状、卡点、验收标准与估算 |

### SDD

| 文档 | 内容 |
| --- | --- |
| [sdd/pet-agent-sdd.md](sdd/pet-agent-sdd.md) | S1.5 运行时 + App 聊天页的软件设计说明：上下文、分层、依赖规则、模块职责、L1/L2 时序、数据模型、错误模型、配置、部署、扩展点 |

### SPEC

| 文档 | 版本 | 内容 |
| --- | --- | --- |
| [spec/agent-runtime-api.md](spec/agent-runtime-api.md) | v1.18 | `/healthz`、`/readyz`、`/metrics`、`POST /agent/chat`、事件续传、消息回读、会话列表、文档问答（上传/能力矩阵/删除）、记忆（含删除/导出）与用量、宠物画像、管理端只读与队列运维接口、任务退避重试与多副本语义的请求/响应/事件/错误码/不变量 |
| [spec/web-chat-ui.md](spec/web-chat-ui.md) | v1.2 | 对话页状态机、交互、持久化键、错误码→三语文案映射、布局约束、i18n 键、非目标 |

### ADR

| 编号 | 决策 | 状态 |
| --- | --- | --- |
| [ADR-0001](adr/0001-python-agent-runtime.md) | Agent 运行时用 Python 独立服务，不塞进 Spring Boot | Accepted |
| [ADR-0002](adr/0002-tools-through-java-api.md) | 工具层走 Java `/api/v1`，不直连业务库 | Accepted |
| [ADR-0003](adr/0003-sse-event-contract.md) | 对外用五种事件 + `id:` 游标的 SSE 契约 | Accepted |
| [ADR-0004](adr/0004-checkpoint-thread-id.md) | LangGraph checkpointer 的 `thread_id` 用 `run_id` | Accepted |
| [ADR-0005](adr/0005-layer-dependency-rules.md) | 单向依赖分层 + 依赖全注入 | Accepted |
| [ADR-0006](adr/0006-web-sse-client.md) | 前端用 `fetch + ReadableStream` 自研 SSE 客户端 | Accepted |
| [ADR-0007](adr/0007-observability-baseline.md) | 可观测基线：JSON 日志 + request_id + `/readyz`，不引入 APM | Accepted |
| [ADR-0008](adr/0008-dependency-lock-and-ci.md) | 依赖精确锁定 + CI 门禁 + 非 root 容器 | Accepted |
| [ADR-0009](adr/0009-event-stream-vs-task-queue.md) | 事件回放用 Redis Stream、旁路任务用 TaskQueue（RocketMQ 可选） | Accepted |

### PLAN

| 文档 | 范围 | 状态 |
| --- | --- | --- |
| [plans/s1.6-production-hardening.md](plans/s1.6-production-hardening.md) | S1.6 生产化加固：P0 工程基线 → P3 记忆扩展，每阶段带可执行验收 | P0、P1 已完成，P2 待启动 |
| [plans/s1.7-admin-workbench.md](plans/s1.7-admin-workbench.md) | S1.7 管理端「会话工作台」：权限模型、4 个只读接口、两个页面 | 已完成 |
| [plans/s1.8-p2-resilience.md](plans/s1.8-p2-resilience.md) | S1.8 P2 韧性与真机联调：真机落库、Redis 兼容、幂等键、熔断 | 已完成 |
| [plans/s1.9-task-queue.md](plans/s1.9-task-queue.md) | S1.9 任务队列：把记忆抽取/审计挪出请求路径，RocketMQ 作为生产实现 | S1.9-a、S1.9-b 已完成；RocketMQ 待启动 |
| [plans/s1.15-doc-rag.md](plans/s1.15-doc-rag.md) | S1.15 文档问答 RAG：上传/解析/切分/嵌入/检索/引用（BACKLOG A3） | 已完成 |
| [plans/s1.16-ops-metrics-memory.md](plans/s1.16-ops-metrics-memory.md) | S1.16 运维与数据自主：在途消息巡检 / `/metrics` / 记忆删除导出（B3·B5·B7） | 已完成 |
| [plans/s1.18-profile.md](plans/s1.18-profile.md) | S1.18 宠物画像：版本化快照 + 确定性 builder + 管理端画像页（C2） | 已完成 |
| [plans/s1.19-b4-b2-deskpet.md](plans/s1.19-b4-b2-deskpet.md) | S1.19 退避重试 / 多副本验证 / 桌宠档 A（B4·B2·C6） | 已完成 |
| [plans/s1.20-deskpet-v2.md](plans/s1.20-deskpet-v2.md) | S1.20 桌宠 v2：分层角色 + 部件动画 + 视线跟随 + 拖拽（C6 重做） | 已完成 |
| [plans/s1.21-image-to-pet.md](plans/s1.21-image-to-pet.md) | S1.21 图片生成桌宠：抠背景 + 卡通化 + 精灵图动效（C6 扩展） | 已完成 |
| [plans/s1.22-pet-engine.md](plans/s1.22-pet-engine.md) | S1.22 桌宠引擎：照 dsh-pet 源码重写编排/物理/状态机（C6 引擎版） | 已完成 |
| [plans/s1.23-auto-reconnect.md](plans/s1.23-auto-reconnect.md) | S1.23 断线自动重连：运行生命周期脱离 HTTP 连接 + `follow=1` 续传（B8） | 已完成 |
| [plans/s1.24-stale-run-reaper.md](plans/s1.24-stale-run-reaper.md) | S1.24 僵尸 run 收敛：启动收尸 + 定时巡检，条件更新防误杀（B3 收尾） | 已完成 |
| [plans/s1.25-citation-jump-links.md](plans/s1.25-citation-jump-links.md) | S1.25 引用回跳：`locator` 改为 App 路由 + 补齐帖子引用来源（C4） | 已完成 |
| [plans/s1.26-ci-docker-context.md](plans/s1.26-ci-docker-context.md) | S1.26 CI 修复：`docker build` 构建上下文写重 + 推标签重复触发（C8） | 已完成 |
| [plans/s1.27-memory-evals.md](plans/s1.27-memory-evals.md) | S1.27 记忆抽取评测：memory 套件 2→48 条、阈值 0.9、按缺陷修抽取规则（C3） | 已完成 |
| [plans/s1.28-prompt-version.md](plans/s1.28-prompt-version.md) | S1.28 提示词版本化：版本登记表 + 冻结哈希闸门 + `prompt_version` 进 meta/日志（D6） | 已完成 |
| [plans/s1.29-capacity-baseline.md](plans/s1.29-capacity-baseline.md) | S1.29 单实例容量基线：SSE 压测脚本 + 1/5/10/20 并发实测首 token/错误率/内存（C7） | 已完成 |
| [plans/s1.30-app-memory-entry.md](plans/s1.30-app-memory-entry.md) | S1.30 App「我的记忆」：按范围拉取合并 / 单条删除 / 聚合导出（B7 收尾） | 已完成 |
| [plans/s1.31-capacity-ceiling.md](plans/s1.31-capacity-ceiling.md) | S1.31 单实例容量上限：修正 requests&lt;level 的并发封顶缺陷，扫 30–150 并发（C7） | 已完成 |
| [plans/s1.32-browser-e2e.md](plans/s1.32-browser-e2e.md) | S1.32 浏览器 e2e：Playwright + 系统 Edge + 固定桩，三条真实链路一键跑（C9） | 已完成 |
| [plans/s1.33-admin-model-config.md](plans/s1.33-admin-model-config.md) | S1.33 管理员统一模型配置：加密存储 + 测试连接 + 热切换 + 管理端页（C10） | 已完成 |
| [plans/s1.34-memory-episodes.md](plans/s1.34-memory-episodes.md) | S1.34 情景记忆：规则抽取 + 按来源消息幂等 + 确定性召回 + API/导出 v2（C1 第一刀） | 已完成 |
| [plans/s1.35-chat-a11y.md](plans/s1.35-chat-a11y.md) | S1.35 对话页无障碍基线：状态播报 + 消息区语义 + 历史面板焦点闭环（D9） | 已完成 |
| [plans/s1.36-agent-error-i18n.md](plans/s1.36-agent-error-i18n.md) | S1.36 Agent 错误码三语化：稳定 code → `agentError.*` + `retry_after_s`（D8） | 已完成 |
| [plans/s1.37-admin-model-cost.md](plans/s1.37-admin-model-cost.md) | S1.37 管理端按模型分账：`by_model` + 可配置单价 + 工作台表格（D4） | 已完成 |

### REPORT

| 文档 | 里程碑 | 结论 |
| --- | --- | --- |
| [reports/2026-11-07-s1.5-runtime.md](reports/2026-11-07-s1.5-runtime.md) | S1.5 分层运行时 | 45 单测 / 23 评测 / 10 项真进程冒烟 全绿 |
| [reports/2026-11-07-web-chat.md](reports/2026-11-07-web-chat.md) | App 聊天页接入 | build 通过、20 前端单测、浏览器端到端走通 |
| [reports/2026-11-07-s1.6-p0.md](reports/2026-11-07-s1.6-p0.md) | S1.6 P0 工程基线 | ruff/pytest 59/evals/e2e 10-10 全绿；抓到 4 个真实缺陷；docker 未本机验证（无 docker） |
| [reports/2026-11-08-s1.6-p1.md](reports/2026-11-08-s1.6-p1.md) | S1.6 P1 配额/事件总线/记忆/用量 | 92 单测 + 23 评测 + e2e 10/10 + P1 冒烟 9/9 + Edge 浏览器端到端；Redis/MySQL 未真机联调 |
| [reports/2026-11-08-s1.7-admin.md](reports/2026-11-08-s1.7-admin.md) | S1.7 管理端会话工作台 | 101 单测 + 管理端冒烟 6/6 + vue-tsc/build 通过 + Edge 浏览器端到端；MySQL 版查询仅契约测试 |
| [reports/2026-11-08-s1.8-p2.md](reports/2026-11-08-s1.8-p2.md) | S1.8 P2 韧性与真机联调 | 122 单测（含 MySQL 契约）、四个冒烟 10/9/6/8 全绿、真机 MySQL 8.0.29 + Redis 5.0.14；抓到 5 个真实缺陷（RESP3、幂等维度、脚本清空文件等） |
| [reports/2026-11-08-s1.9-task-queue.md](reports/2026-11-08-s1.9-task-queue.md) | S1.9-a 旁路任务队列（TaskQueue） | 134 单测、四个冒烟 10/9/6/8、真机 Redis 队列收发闭环；抓到 3 个真实缺陷（冒烟脚本不自洽、签名不一致、最终一致误判为回归） |
| [reports/2026-11-08-s1.9b-deadletter.md](reports/2026-11-08-s1.9b-deadletter.md) | S1.9-b 启动补偿 + 死信重放 + 队列现场 | 142 单测、五个冒烟 10/9/6/8/8、真机"在途 1 条 → 重启回收 → 落库"闭环；修 3 个问题（import 顺序、未用 Any、不变量编号乱序） |
| [reports/2026-11-08-a2-session-list.md](reports/2026-11-08-a2-session-list.md) | BACKLOG A2 App 历史会话 | 146 单测、build/vitest 通过、真机隔离与排序验证、Edge 浏览器端到端；修 1 个真实缺陷（同秒会话排序） |
| [reports/2026-11-08-a1-real-model-smoke.md](reports/2026-11-08-a1-real-model-smoke.md) | BACKLOG A1 真实模型冒烟 | 真 key 13/13：L1 P50 929 ms / P95 1064 ms、L2 调 `search_logs` 且引用 7001、usage 与库里 `agent_run` 一致；顺带发现"强杀进程留下僵死 running"（登记 B3） |
| [reports/2026-11-08-s1.11-hygiene-debts.md](reports/2026-11-08-s1.11-hygiene-debts.md) | S1.11 卫生债 E1/E3/E4/E5 | 验证码改随机+dev 可配固定码（Java 单测 5 条）、管理端类型门禁改 `vue-tsc -b`（探针证明会报错，顺带修好"帖子图片/标签永远为空"）、社区分类改 code 比对、今日提醒改日期比较（前端单测 37 条） |
| [reports/2026-11-08-s1.12-e2-e6-e7.md](reports/2026-11-08-s1.12-e2-e6-e7.md) | S1.12 卫生债 E2/E6/E7 | 广播已读改独立表（未读 2→1→0，列表不重复）、`sortField` 白名单生效（升/降序与注入回落真机验证）、错误码映射 400/401/404（curl 实测状态码）；Java 10 单测、两端 build 通过 |
| [reports/2026-11-08-s1.13-e8-e13.md](reports/2026-11-08-s1.13-e8-e13.md) | S1.13 卫生债 E8/E13 | 仪表盘趋势/类型分布改聚合、热门帖作者改批量查（SQL 日志 1 次 GROUP BY、0 次逐日查询，数字与库内对账一致）；数据库口令移出仓库（环境变量 / `application-local.yml`，缺口令时首次查库报 `Access denied`，全仓库 grep 明文为 0） |
| [reports/2026-11-08-s1.14-e9-e12.md](reports/2026-11-08-s1.14-e9-e12.md) | S1.14 卫生债 E9/E10/E11/E12（清零） | 违规管理接真实接口（命中即 400 + 落记录）、管理端用户增改真落库、话题归属改 `post.topic_id`、App `as any` 清零与假数据下架；Java 27 单测、App 37 单测、三端构建通过、Edge 三页实点；抓到 `sensitive_word` 缺表导致发帖 500 |
| [reports/2026-11-08-s1.15-doc-rag.md](reports/2026-11-08-s1.15-doc-rag.md) | S1.15 文档问答 RAG（BACKLOG A3） | `doc_file`/`doc_chunk` + 解析/切分/嵌入/检索 + `search_docs` 工具 + App 附件入口；159 单测、`rag_smoke` 10/10、Edge 上传后提问带回引用；D1–D6 六个真缺陷（软删复活、处理器漏装配、迁移注释吞 DDL 等） |
| [reports/2026-11-08-s1.16-ops.md](reports/2026-11-08-s1.16-ops.md) | S1.16 运维与数据自主（B3·B5·B7） | 在途消息巡检回收（`claimed` ZSET + `attempt+1`）、6 个 Prometheus 指标、记忆删除/导出；181 单测、`ops_smoke` 11/11（含"造一条死掉的在途消息 → 巡检搬回 → 落库"真机闭环） |
| [reports/2026-11-08-s1.17-admin-console.md](reports/2026-11-08-s1.17-admin-console.md) | S1.17 管理端运维与图谱（B6） | 队列运维/长期记忆/知识图谱三页 + `DELETE /agent/admin/memory`、`GET /agent/admin/graph`；183 单测、Edge 实点三页；抓到 Java `LoginUserVO` 缺 `role` 与 vue-echarts `symbolSize` 回调失效两个真缺陷 |
| [reports/2026-11-08-s1.18-profile.md](reports/2026-11-08-s1.18-profile.md) | S1.18 宠物画像（C2） | 版本化 `profile_snapshot` + 确定性 builder + 记忆消费后重算 + 四接口 + 管理端画像页；203 单测、真机 `v2 facts=3`、Edge 实点；抓到画像与记忆并发导致空画像的顺序缺陷 |
| [reports/2026-11-08-s1.19-b4-b2-pet.md](reports/2026-11-08-s1.19-b4-b2-pet.md) | S1.19 退避重试 / 多副本 / 桌宠（B4·B2·C6） | 失败进 `:retry` ZSET 指数退避（5s→600s 封顶）+ `redrives` 有界重投（默认关）；双副本 `multi_replica_smoke` 8/8；桌宠档 A（纯函数状态机 + H5 组件）；208 单测、App 50 tests |
| [reports/2026-11-08-s1.20-deskpet-v2.md](reports/2026-11-08-s1.20-deskpet-v2.md) | S1.20 桌宠 v2（C6 重做） | 分层 SVG 角色（7 部件独立动画：呼吸/眨眼/耳抖/发丝/尾巴/手臂）+ 视线跟随 + 拖拽换位 + 单击跳跃与爱心 + 双击收起；App 59 tests（新增 petMotion 7 例、DeskPet 重写 5 例）、build 通过、真机 Edge 实点；D1–D4（trigger 坐标只读、jsdom 无 animate、首版 pointer-events、asar 提取失败） |
| [reports/2026-11-08-s1.22-pet-engine.md](reports/2026-11-08-s1.22-pet-engine.md) | S1.22 桌宠引擎（C6 引擎版） | canvas 2D + 29 段程序化动画；同构复刻 dsh-pet 的权重分档/播完回链/工作六态/睡觉三段/弹簧拖拽/落地挤压；全局挂件 + 登录页守卫；App 128 tests（引擎 45 / 外壳 10）、tsc 0、build 0、真机三态 + 帧差 4879；D1–D5（没读源码、C:\Users\XiaoNian 只读、CRLF 静默不命中、只挂首页、测试与契约打架） |
| [reports/2026-11-08-s1.21-image-pet.md](reports/2026-11-08-s1.21-image-pet.md) | S1.21 图片生成桌宠（C6 扩展） | 四角取色 + 边缘洪泛抠背景 → alpha 裁边 → 色阶量化 + 描边 → 512px 精灵图；存储可注入、localStorage 单键；App 85 tests（petImage 16 / petSpriteStore 10）、build 通过、真机上传→保存→首页生效；D1–D4（as const 字面量类型、vi.spyOn 拦不住 localStorage、i18n 脚本路径、dev 冷启动白屏） |
| [reports/2026-11-14-s1.23-auto-reconnect.md](reports/2026-11-14-s1.23-auto-reconnect.md) | S1.23 断线自动重连（B8） | 后端把 run 从 HTTP 连接里拆出来（`RunSupervisor` 托管 + `?follow=1` 挂到终态），前端 `[3s,3s,6s]` 续传、`after` 恒为已收最大 id；backend 202 passed + 1 skipped（MySQL 变体未开 DSN）、`reconnect_smoke` 5/5（真 uvicorn + 真 socket 掐线，续传等了 656 ms）、App 136 tests + tsc 0 + build 0；抓到内存仓储 `finish_run` 状态永停 `running` 的真缺陷 |
| [reports/2026-11-14-s1.24-stale-run-reaper.md](reports/2026-11-14-s1.24-stale-run-reaper.md) | S1.24 僵尸 run 收敛（B3 收尾） | 启动收尸 + 60s 定时巡检，判据是「开始时间 > 900s」；条件更新保证多副本下只收敛一次；backend 209 passed + 1 skipped、ruff 全绿；4 条不误杀/幂等/上线即收尸/配置护栏用例 |
| [reports/2026-11-14-s1.25-citation-jump-links.md](reports/2026-11-14-s1.25-citation-jump-links.md) | S1.25 引用回跳（C4） | `citation.locator` 变成 App 路由 + 新增 `search_posts` 工具；健康引用带周记录最大日期并高亮定位；backend 216 passed + 1 skipped、App 141 tests + tsc 0 + build 0、`e2e_smoke` 10/10（citation 已是 `/log/7001`） |
| [reports/2026-11-14-s1.26-ci-docker-context.md](reports/2026-11-14-s1.26-ci-docker-context.md) | S1.26 CI 真正跑通（C8） | 从 S1.6 起 34 次运行全红，唯一挂的是 `docker build`（上下文 `backend-agent/backend-agent` 不存在）；改成 `.` 后运行 #35 两个 job 全绿（53s） |
| [reports/2026-11-15-s1.27-memory-evals.md](reports/2026-11-15-s1.27-memory-evals.md) | S1.27 记忆抽取评测（C3） | memory 套件 2→48 条、阈值 1.0→0.9：加完用例先红 **35/47 = 74%**，量出 5 类真实缺陷（问句当名字 / 过敏值吞副词 / 偏好值带动词 / 裸「喜欢」误抽 / 否定句全漏），修规则后 **48/48 = 100%**；`pytest` 222 例 0 失败 1 跳过（MySQL 变体未开 DSN）、`ruff` 全绿 |
| [reports/2026-11-15-s1.28-prompt-version.md](reports/2026-11-15-s1.28-prompt-version.md) | S1.28 提示词版本化（D6） | `SYSTEM_PROMPT` 搬进 `app/graph/prompts.py` 版本登记表（当前 `2026-11-15.1`，270 字）+ 手写冻结 sha256；变异实验证明「原地改正文」会让 2 条单测红、还原即绿；run 的 meta 与日志带 `prompt_version`；`pytest` 229 例 0 失败 1 跳过、`evals` 69 条全绿、`ruff` 全绿 |
| [reports/2026-11-16-s1.29-capacity-baseline.md](reports/2026-11-16-s1.29-capacity-baseline.md) | S1.29 单实例容量基线（C7） | 新增 `scripts/load_baseline.py`（无新依赖、逐档重启、SSE 首 delta 计时）；20 并发 × 40 请求 **40/40 成功**、首 token P50 1151 / P95 1201ms（桩 900ms → 服务侧开销 301ms）、峰值工作集 97MB；**上限未触到**（20 并发是下界）；`pytest` 244 通过 + 1 跳过（不带 DSN）/ 256 通过（带真机 DSN）、`e2e_smoke` 10/10、`ruff` 全绿；抓到桩 `time.sleep` 阻塞事件循环与 venv 瘦启动器量错内存两个真问题 |
| [reports/2026-11-17-s1.30-app-memory.md](reports/2026-11-17-s1.30-app-memory.md) | S1.30 App「我的记忆」入口（B7 收尾） | 个人中心新增 `/my-memory`：通用+每宠并发拉取合并、范围筛选、二次确认删除、聚合导出 JSON；App 14 条新测试 → 全量 **155 tests**、`vue-tsc` 0、build 0、后端 `pytest` 244 passed + 1 skipped（未开 DSN）；**未做真机浏览器点击**（无浏览器环境），真机验收归入 C9 |
| [reports/2026-11-17-s1.31-capacity-ceiling.md](reports/2026-11-17-s1.31-capacity-ceiling.md) | S1.31 单实例容量上限（C7 收尾） | 每档 300 请求扫 30–150 并发：140 并发首 token P95 2994ms 达标、150 两次 3100/3202ms 超限（错误率 0%）；修复 `--requests` < 最大档位导致并发被封顶的协议缺陷（新增 4 条单测），`pytest` **248 passed + 1 skipped** |
| [reports/2026-11-18-s1.32-browser-e2e.md](reports/2026-11-18-s1.32-browser-e2e.md) | S1.32 浏览器 e2e（C9） | Playwright + 系统 Edge + 固定桩，一条命令起停五进程；三条真实链路 **3 passed (22.2s)**：App 登录→对话→引用回跳、管理员会话详情、429 提示+重试；App 155 tests + `vue-tsc` 0 + build 0，后端 `pytest` 249 例（248 通过 + 1 跳过，未开 DSN） |
| [reports/2026-11-18-s1.33-admin-model-config.md](reports/2026-11-18-s1.33-admin-model-config.md) | S1.33 管理员统一模型配置（C10） | 管理端可测试/保存/热切换；Key 加密且只回显末 4 位；`pytest` **258 例（257 通过 + 1 跳过）**、新增 9 例模型配置测试、`ruff` 全绿；管理端 `vue-tsc` 0 + build 0（2303 modules，18.21s）；MySQL DDL/页面点击未执行 |
| [reports/2026-11-19-s1.34-memory-episodes.md](reports/2026-11-19-s1.34-memory-episodes.md) | S1.34 情景记忆（C1 第一刀） | 写入 `memory_episode` 并带来源消息 id、按 `(user, source_message_id)` 幂等、确定性召回注入 system、列表/删除/导出 v2；`pytest` **283 passed + 1 skipped**（未开 DSN）、`ruff` 全绿；MySQL 变体与浏览器点击未执行 |
| [reports/2026-11-20-s1.35-chat-a11y.md](reports/2026-11-20-s1.35-chat-a11y.md) | S1.35 对话页无障碍基线（D9） | 回复生命周期播报、消息区 `aria-busy`、错误 `alert`、输入框名称、历史面板焦点闭环；App **161 tests**（17 文件）+ `vue-tsc -b` 0 + build 0；真实读屏人工验收未执行 |
| [reports/2026-11-21-s1.36-agent-error-i18n.md](reports/2026-11-21-s1.36-agent-error-i18n.md) | S1.36 Agent 错误码三语化（D8） | 14 个服务端 code + HTTP 状态 → `agentError.*`，`retry_after_s` 向上取整，未知 code 回退 message；三语 20 键；App **176 tests**（19 文件）+ `vue-tsc -b` 0 + build 0；后端 283 passed + 1 skipped、`ruff` 全绿（本轮无后端改动） |
| [reports/2026-11-21-s1.37-admin-model-cost.md](reports/2026-11-21-s1.37-admin-model-cost.md) | S1.37 管理端按模型分账（D4） | `/agent/admin/usage` 增 `by_model`，按 `PET_AGENT_MODEL_PRICES` 估算成本、未配置为 null；后端 **290 passed + 1 skipped**、`ruff` 全绿；管理端 `vue-tsc` 0 + build 0；MySQL 变体未开 DSN |

## 3. 新增文档怎么起头

ADR：

```markdown
# ADR-0007 标题（一句话说清决定）

- 状态：Proposed | Accepted | Superseded by ADR-XXXX
- 日期：YYYY-MM-DD
- 决策人：

## 背景（约束是什么，为什么现在必须决）
## 选项（至少两个，各自代价）
## 决定
## 后果（变好的、变差的、需要改的）
## 验证方式（怎么证明这个决定是对的）
```

SPEC：

```markdown
# 规格：<能力名> v1.0
## 范围 / 非目标
## 对外契约（请求、响应、事件、错误码）
## 不变量（必须永远成立的断言）
## 验收用例（可执行）
## 变更记录
```

REPORT：

```markdown
# 交付报告：<里程碑>
## 环境（版本、端口、依赖）
## 做了什么（文件级）
## 验证（命令 + 真实输出）
## 已知缺口与风险
## 结论（可交付 / 有条件交付 / 不可交付）
```
