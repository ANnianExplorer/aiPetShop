# ADR-0004 checkpointer 的 `thread_id` 用 `run_id` 而不是 `session_id`

- 状态：Accepted
- 日期：2026-11-07
- 决策人：架构（本仓）

## 背景

会话历史有**两个**可能的来源：LangGraph checkpointer 的持久化状态，和 MySQL 的 `agent_message`。

如果用 `thread_id = session_id`，同一个会话的每次 run 都读写同一份检查点，`messages` 又是 `operator.add` 累加——于是：

1. 第二轮把"历史消息"再喂一遍，图里的 `messages` 与库里**重复**；
2. 一旦引入 checkpointer 恢复，重试会重复执行工具；
3. 历史条数上限、裁剪逻辑要写两套（图内一套、库一套），必然漂移。

## 选项

| 选项 | 行为 | 风险 |
| --- | --- | --- |
| A. `thread_id = session_id` | 图内状态即历史 | 累加 reducer 与多轮喂入冲突；恢复即重放，容易重复计费/重复调工具 |
| B. `thread_id = run_id`（本决定） | 每次运行独立检查点，历史从库里读 | 不能跨 run 恢复"半截"状态（当前也不需要） |
| C. 不用 checkpointer | 少一个依赖 | 失去中断/恢复能力，S4 的写操作审批需要它 |

## 决定

采用 **B**：`thread_id = run_id`，历史真源是 MySQL（`repository.history(session_id, limit)`），在 `prepare` 节点组装进 `messages`。

## 后果

**变好**：
- 历史只有一份真源，前端回读、图内上下文、审计保持一致；
- 重试是"新 run"，天然幂等，不会重复执行上一次的工具；
- checkpointer 可以按 run 过期清理，不会越滚越大。

**变差**：
- 跨 run 的"继续执行"需要产品层显式发起新 run（当前没有该需求）；
- 每次 run 都要读一次历史（一次 SQL，可接受）。

## 验证方式

- `test_graph_l2.py`：回归断言"模型第一次被调用时 `messages[0]` 是 system、最后一条是本轮问题"——正是这条断言锁住了"历史只喂一次"；
- `test_repository_contract.py`：`history` 只含 user/assistant 且正序；
- 真 SSE 两轮对话：库里 4 条消息，`done.answer` 与气泡一致。
