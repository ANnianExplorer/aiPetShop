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
| [BACKLOG.md](BACKLOG.md) | 未完成事项清单：P0 3 条 / P1 8 条 / P2 9 条 / P3 9 条 / 原项目卫生债 13 条，每条带现状、卡点、验收标准与估算 |

### SDD

| 文档 | 内容 |
| --- | --- |
| [sdd/pet-agent-sdd.md](sdd/pet-agent-sdd.md) | S1.5 运行时 + App 聊天页的软件设计说明：上下文、分层、依赖规则、模块职责、L1/L2 时序、数据模型、错误模型、配置、部署、扩展点 |

### SPEC

| 文档 | 版本 | 内容 |
| --- | --- | --- |
| [spec/agent-runtime-api.md](spec/agent-runtime-api.md) | v1.3 | `/healthz`、`/readyz`、`POST /agent/chat`、事件续传、消息回读、记忆/用量、管理端只读接口的请求/响应/事件/错误码/不变量 |
| [spec/web-chat-ui.md](spec/web-chat-ui.md) | v1.0 | 对话页状态机、交互、持久化键、错误映射、布局约束、i18n 键、非目标 |

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
