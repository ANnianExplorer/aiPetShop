# ADR-0001 Agent 运行时用独立的 Python 服务

- 状态：Accepted
- 日期：2026-11-07
- 决策人：架构（本仓）

## 背景

PetLumina 的业务后端是 Spring Boot 2.7.18 / Java 11，而 Agent 生态（LangGraph、评测、向量库、多模态解析）主要在 Python。用户已明确"可以有 python"。
硬约束：现有三端零改动可用；运行时不能拖慢业务接口；鉴权只有一个来源（Java 的 `satoken`）。

## 选项

| 选项 | 代价 | 风险 |
| --- | --- | --- |
| A. 在 Spring Boot 里用 Java 实现 Agent 循环 | 无新服务；复用现有鉴权/事务 | 图/检查点/中断/流式要自己造；生态薄，后期接 RAG/多模态成本高 |
| B. Python 独立服务（本决定） | 多一个部署单元、多一套配置 | 需明确边界，否则两套业务逻辑漂移 |
| C. 直接用现成 harness（AgentScope Runtime / OpenHands） | 少写循环 | 面向"能跑代码的沙箱 Agent"，我们的场景不需要沙箱；多租户/配额仍需自建 |

## 决定

采用 **B**：`backend-agent/` 作为独立 FastAPI 服务，只负责"想与说"（路由、图执行、工具编排、事件流），业务数据与鉴权仍归 Java。

## 后果

**变好**：Agent 侧可用 LangGraph / pydantic / 评测脚本；故障隔离（Agent 挂了不影响宠物管理）；可独立扩缩容。

**变差**：多一跳网络（工具调用经 Java）；需要 CORS、身份透传、超时与重试策略；部署多一个进程。

**连带约束**：
- 工具层**不允许**直连业务库（见 ADR-0002）；
- 身份只从 `satoken` 换（`auth_mode=backend`），不接受前端自报 `user_id`；
- 生产必须跟进：LLM 密钥走环境变量、CORS 收敛、SSE 网关不缓冲。

## 验证方式

- 现有三端 `git status` 无改动即可跑通（S1 落地时已验证）；
- `/healthz` 返回 `auth_mode: backend`；
- e2e：App → Runtime → Java 桩 → 回答带 citation。
