# ADR-0005 单向依赖分层 + 依赖全注入

- 状态：Accepted
- 日期：2026-11-07
- 决策人：架构（本仓）
- 设计说明：[sdd/pet-agent-sdd.md](../sdd/pet-agent-sdd.md)

## 背景

S1 的第一版是"能跑就行"：`service.py` 里把建会话、跑图、流式、落库、审计写在一个函数里，`repo.py` 一个文件两种实现，`llm.py` 直接 `import httpx`。
问题不是难看，而是四个具体后果：

1. 想换模型 → 动业务文件；
2. 想加工具 → 改网关 + 改 prompt + 改测试三处；
3. 想单测 L2 流程 → 必须起 HTTP；
4. `evals` 想复用路由逻辑 → 只能复制粘贴。

用户明确要求："不要图简单，也不要出现屎山代码。"

## 选项

| 选项 | 收益 | 代价 |
| --- | --- | --- |
| A. 保持单文件，按需拆 | 快 | 每次需求都在最贵的文件里改；测试只能端到端 |
| B. 分层 + 协议 + 注入（本决定） | 每层可替换、可单测；新增能力只动一层 | 初次搭建成本高；文件数量增加 |
| C. 引入 DDD 全套（领域事件、CQRS、仓储聚合） | 理论完备 | 对当前规模是过度设计 |

## 决定

采用 **B**：`api → runtime → graph → tools/storage/llm → domain` 单向依赖；跨层只通过 `Protocol`（`ChatModel`、`AgentRepository`）和 pydantic 模型通信；`create_app(settings, model, repo, http_client)` 全量注入，测试可换成桩。

## 后果

**变好**：
- `tests/test_repository_contract.py` 用一份契约测试两种存储实现；
- `evals` 直接复用 `classify()` 与 `ToolGateway`；
- 换模型 = 换 `ChatModel` 实现，业务代码零改动。

**变差**：
- 新增一个能力要动 2–3 个文件（接口 + 实现 + 装配），比"全塞一个文件"多几行；
- 需要自律：反向 import 必须靠 review 拦住（当前靠 README 的依赖方向约定）。

## 验证方式

- 45 个单测覆盖各层，且大部分不依赖 HTTP（`ScriptedModel` + `InMemoryRepository`）；
- 同一套 `create_app` 在测试里注入桩、在 `main.py` 里注入真实现；
- 重构后 `git diff` 删除 `app/{llm,service,repo,schemas}.py`，无残留引用。
