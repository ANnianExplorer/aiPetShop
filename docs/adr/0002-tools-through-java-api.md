# ADR-0002 工具层走 Java `/api/v1`，不直连业务库

- 状态：Accepted
- 日期：2026-11-07
- 决策人：架构（本仓）

## 背景

Agent 需要读宠物档案、健康汇总、生活记录。最直接的写法是 Python 直连 MySQL——少一跳、SQL 随意写。但这会带来三个问题：

1. **权限模型被绕开**：Java 侧的 `@AuthCheck`、会话归属、数据隔离全部失效，Agent 成为越权后门；
2. **契约漂移**：同一份数据两套 SQL、两套字段映射，Java 改表 Agent 悄悄坏；
3. **审计断链**：谁在什么上下文读了什么，无法从业务侧追溯。

## 选项

| 选项 | 代价 | 风险 |
| --- | --- | --- |
| A. Python 直连 MySQL（只读账号） | 快，SQL 自由 | 越权、契约漂移、审计缺失；只读账号也难以约束"只能看自己的宠物" |
| B. 走 Java HTTP 接口 + 透传 `satoken`（本决定） | 多一跳、受限于已有端点 | 端点不够时要先在 Java 侧补（这是好事：补齐即被业务复用） |
| C. Agent 侧复制一份只读服务 | 独立性好 | 又是一套权限实现，违背"单一来源" |

## 决定

采用 **B**。`tools/client.py::BackendClient` 统一透传 `satoken`；`code != 0` 抛 `BackendError`，`40100` 抛 `Unauthorized`；工具里**不出现任何 SQL**。

## 后果

**变好**：权限只有一套；Java 改表只需维护自己的 VO；审计链完整（`tool_call_log` + 业务日志）。

**变差**：多一跳延迟（本地 ~2–5ms，可接受）；新增数据需求要同时改 Java 端点。

**连带约束**：
- 工具参数 schema 里禁止出现 `user_id`（网关用 `extra=forbid` 拒），身份只来自上下文；
- 分页/排序必须用 Java 的 `PageRequest` 语义（注意：`sortField` 当前未生效，工具侧不要依赖它）；
- 健康数值不经过 LLM 推断，直接取接口结构化字段。

## 验证方式

- `tests/test_gateway.py`：伪造 `user_id` 被拒；
- e2e：越权读他人会话 → 404；
- 桩 `tests/stub_java.py` 与真 Java 端点路径一一对应，切真后端不改工具代码。
