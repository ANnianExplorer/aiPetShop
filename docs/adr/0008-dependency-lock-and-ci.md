# ADR-0008 依赖锁定 + CI 门禁 + 非 root 容器

- 状态：Accepted
- 日期：2026-11-07
- 决策人：架构（本仓）
- 计划：[s1.6-production-hardening.md](../plans/s1.6-production-hardening.md) P0

## 背景

`requirements.txt` 用的是 `>=` 范围。今天能装、三个月后装出来的是另一套依赖——线上排查时"我本地是好的"就是这么来的。
另外仓库里没有任何自动检查：lint/类型/测试/评测全靠人记得跑。

## 选项

| 选项 | 收益 | 代价 |
| --- | --- | --- |
| A. 保持 `>=`，靠 venv 快照 | 省事 | 不可复现；安全更新不可控 |
| B. `requirements.in`（意图）+ `requirements.txt`（精确锁定） | 可复现、可审计、可用 `pip-compile` 升级 | 升级需要一次显式操作 |
| C. Poetry / uv | 现代化依赖管理 | 团队要学新工具；本项目已有 venv 工作流 |

## 决定

采用 **B** 的轻量版：
1. `requirements.in` 保留人类意图（`>=`），`requirements.txt` 写 `==` 精确版本（由当前 venv `pip freeze` 收敛，仅直接依赖）；
2. `requirements-dev.txt` = 运行时 + `ruff` + `pytest`；
3. **CI 门禁**：`.github/workflows/agent-ci.yml` 依次跑 `ruff check` → `pytest` → `evals.run`，任一失败即红；
4. **容器**：多阶段构建（builder 装依赖 → runtime 只带 venv），非 root `appuser`，`HEALTHCHECK` 打 `/healthz`，`PYTHONUNBUFFERED=1`。

## 后果

**变好**：环境可重建；规范问题在 CI 就被拦；镜像不含构建工具，体积与攻击面都小。

**变差**：升级依赖要改两处（`.in` 和 `.txt`）；ruff 规则可能对历史代码报错，需要一次性 `--fix` + 人工复核。

**不做的事**：不引入 mypy 强制（当前 `Any` 使用集中在图状态与 FastAPI 依赖，收益低于改造成本，先记入 P2 观察）。

## 验证方式

- `ruff check .` → 0 error；
- `pytest` → 48 passed；
- `python -m evals.run` → 三套件达标；
- CI 文件在 push 后按上述顺序执行（本机无远端凭据，标记为"本地等价命令已验证"）。
