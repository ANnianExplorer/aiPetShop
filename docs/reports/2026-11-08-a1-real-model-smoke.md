# 交付报告：A1 真实模型冒烟

- 日期：2026-11-08
- 范围：用真 key（OpenAI 兼容端点）跑通 L1 + L2，量首 token 延迟与 token 用量
- 结论：**通过**（13/13 检查）。此前全部验证都跑在 `tests/stub_llm.py` 上，这是第一次用真模型走完整链路。

## 1. 为什么必须先做这一条

桩模型的回答是写死的，它能证明"事件流接得对"，但证明不了三件事：

1. 我们喂给它的**工具 schema** 它认不认（桩是照着我们的假设写的）；
2. 真实的**首 token 延迟**是多少（用户唯一能感知的指标）；
3. `done.usage` 的 token 数与落库的 `agent_run` 是否一致（计费口径）。

桩全绿而真模型调不通，是这类项目最常见的自欺。

## 2. 环境

| 项 | 值 |
| --- | --- |
| 端点 | `https://api.deepseek.com/v1`（OpenAI 兼容） |
| 模型 | `deepseek-chat`（响应头返回的实际路由名 `deepseek-flash`） |
| 仓储 | MySQL 8.0.29（`petlumina`） |
| 鉴权 | `AUTH_MODE=backend`（stub_java `:8097` 提供 `/auth/current`） |
| key | 只经 `PET_AGENT_LLM_API_KEY` 环境变量注入，**未写入任何文件** |
| 脚本 | `backend-agent/scripts/real_model_smoke.py` |

## 3. 结果

### 3.1 L1 直答（3 轮，同一问题）

| 轮次 | 首 token | 总耗时（库内） | prompt / completion |
| --- | --- | --- | --- |
| 1 | 573 ms | 843 ms | 182 / 15 |
| 2 | 1064 ms | 1350 ms | 182 / 15 |
| 3 | 929 ms | 1132 ms | 182 / 14 |

- **P50 首 token = 929 ms，P95 = 1064 ms**（n=3，P95 即最大值；样本小，只作量级判断，不当作 SLA）
- 三轮回答：

```text
我是 Lumina，你的宠物管家，帮你看宠物的健康数据。
我是 Lumina，你的宠物管家，帮你看数据、记健康。
我是 Lumina，你的宠物管家，帮你看数据和健康记录。
```

- 路由判定稳定为 `L1`，**一轮工具都没调**（直答路径没有因为真模型而变化）
- 每轮 `prompt=182`：system 提示 + 工具 schema 的固定开销可见且稳定

### 3.2 L2 带工具（问"上次打疫苗是什么时候？"）

| 项 | 值 |
| --- | --- |
| 路由 | `L2` |
| 工具调用 | `search_logs`（1 次） |
| 引用 | `{"kind":"log","id":"7001","label":"疫苗记录","locator":"2026-09-01 10:20:00"}` |
| 首 token | 2926 ms |
| 总耗时 | 3368 ms（事件流）/ 3200 ms（库内 `latency_ms`，差异是网络与落库开销） |
| tokens | prompt 2286 / completion 108 |

回答（模型基于工具结果自行组织，未被提示词喂答案）：

```text
记录里最近一次是 2026-09-01 的「疫苗记录」，打的是猫三联第二针。要不要我帮你算算下一针该什么时候？
```

`prompt` 从 182 跳到 2286，是工具 schema + 一条日志结果 + 第二轮上下文的真实开销——这个数字以前只能靠估算。

### 3.3 落库核对（`agent_run`）

```text
(1794059091876000000, 'L2', 'succeeded', 2286, 108, 3200, 2026-11-07 21:44:51)
(1794059090251000000, 'L1', 'succeeded', 182, 14, 1132, 2026-11-07 21:44:50)
(1794059088351000000, 'L1', 'succeeded', 182, 15, 1350, 2026-11-07 21:44:48)
(1794059087126000000, 'L1', 'succeeded', 182, 15, 843, 2026-11-07 21:44:47)
```

与 SSE `done.usage` 完全一致：**同一次运行，前端看到的花费 = 库里记的花费**。

## 4. 脚本检查项（13/13）

| 检查 | 说明 |
| --- | --- |
| 模型已配置 / 不是本地桩 | `/healthz.model` 不是 `stub` |
| L1 全部成功、走直答路由、不调工具、有真实回答、有 token 计量 | 5 项 |
| L2 无错误、走工具路由、调用了 `search_logs`、带引用、引用指向 7001 | 5 项 |
| L2 prompt token 显著大于 L1 | 1 项（工具轮的真实开销） |

## 5. 顺带发现的真问题

**进程被强杀时，在途 run 会永远停在 `running`。**
本次重启 8099 时留下一条 `(1794058693935000000, 'L2', 'running', 0, 0, 0)`——`runner` 的 `finally` 只在进程活着时能把状态改成 `cancelled`，`Stop-Process -Force` 之后没有任何人收敛它。

影响：管理端的"运行轨迹"会显示一条永远不结束的运行；`usage_summary` 只统计 `succeeded`，所以不会多计费，但**数据看起来是错的**。

这条已登记进 BACKLOG（B3 细化），修法需要先定策略：启动时按 `create_time < now - stale_run_timeout_s` 收敛（默认 15 分钟），还是交给外部巡检。多副本下不能无脑 cancel 别人的活 run。

## 6. 未验证 / 边界

1. 样本只有 3 轮 L1，P95 不具备统计意义；
2. 只测了 `deepseek-chat` 一个模型，没有对比其它端点；
3. 未测流式中断（客户端提前断开）后的计费与状态；
4. 未测 429/5xx 重试路径在真端点上的表现（桩里模拟过）；
5. 成本未与账单核对，只核对了 token 数的内部一致性。

## 7. 复现

```powershell
cd backend-agent
$env:PET_AGENT_ENV="dev"; $env:PET_AGENT_REPO_BACKEND="mysql"
$env:PET_AGENT_MYSQL_DSN="mysql://root:yzh521@127.0.0.1:3306/petlumina"
$env:PET_AGENT_AUTH_MODE="backend"; $env:PET_AGENT_BACKEND_BASE_URL="http://127.0.0.1:8097/api/v1"
$env:PET_AGENT_LLM_BASE_URL="https://api.deepseek.com/v1"; $env:PET_AGENT_LLM_MODEL="deepseek-chat"
$env:PET_AGENT_LLM_API_KEY="<your-key>"          # 不要写进 .env 或仓库
.\.venv\Scripts\python -m uvicorn app.main:app --port 8099
# 另一个窗口
.\.venv\Scripts\python -m scripts.real_model_smoke --rounds 3
```
