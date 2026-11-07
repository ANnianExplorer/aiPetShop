# 文档地图（Pet-Agent）

> 这份索引回答一个问题：**每个阶段交付了什么，凭什么说它是对的。**

## 1. 文档类型约定

| 类型 | 目录 | 回答的问题 | 什么时候写 | 谁维护 |
| --- | --- | --- | --- | --- |
| **ADR**（架构决策记录） | `docs/adr/` | 为什么这样选，放弃了什么 | 做出不可逆或代价高的决定时 | 决策人 |
| **SPEC**（规格） | `docs/spec/` | 对外契约是什么，什么算"符合规格" | 动手前，随实现变更同步 | 实现人 |
| **SDD**（软件设计说明） | `docs/sdd/` | 系统怎么分层、模块怎么协作 | 架构成型时，重构时更新 | 架构负责人 |
| **REPORT**（交付/测试报告） | `docs/reports/` | 这一步跑了什么、输出是什么、剩什么风险 | 每个可验收里程碑 | 交付人 |
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

### SDD

| 文档 | 内容 |
| --- | --- |
| [sdd/pet-agent-sdd.md](sdd/pet-agent-sdd.md) | S1.5 运行时 + App 聊天页的软件设计说明：上下文、分层、依赖规则、模块职责、L1/L2 时序、数据模型、错误模型、配置、部署、扩展点 |

### SPEC

| 文档 | 版本 | 内容 |
| --- | --- | --- |
| [spec/agent-runtime-api.md](spec/agent-runtime-api.md) | v1.0 | `/healthz`、`POST /agent/chat`、事件续传、消息回读的请求/响应/事件/错误码/不变量 |
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

### REPORT

| 文档 | 里程碑 | 结论 |
| --- | --- | --- |
| [reports/2026-11-07-s1.5-runtime.md](reports/2026-11-07-s1.5-runtime.md) | S1.5 分层运行时 | 45 单测 / 23 评测 / 10 项真进程冒烟 全绿 |
| [reports/2026-11-07-web-chat.md](reports/2026-11-07-web-chat.md) | App 聊天页接入 | build 通过、20 前端单测、浏览器端到端走通 |

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
