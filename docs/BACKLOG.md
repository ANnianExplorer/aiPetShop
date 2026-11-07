# 未完成事项清单（Backlog）

- 状态：活文档（每次交付后更新；做完的条目移到对应 REPORT，并从本表删除）
- 更新：2026-11-08
- 基线：`main` @ `fef0913`，已完成到 **S1.9-b**（见 `docs/pet-agent-architecture.md` §12）

## 0. 怎么读这份文档

1. **只写"没做完"的**。做了的事在 `docs/reports/` 里，不在这里重复。
2. 每条都有**验收标准**：能写成命令或可观察现象，否则不算条目，是愿望。
3. 优先级按"卡不卡产品可用"分：P0 阻断、P1 该做、P2 值得做、P3 以后。
4. 估算是"一个人、熟悉代码"的量级，不是承诺。

统计：**P0 3 条（A1、A2 已交付）· P1 8 条 · P2 9 条 · P3 9 条 · 原项目卫生债 9 条**，原计划 42 条，其中 A1、A2、E1、E3、E4、E5 已完成（E1/E3/E4/E5 见 `docs/reports/2026-11-08-s1.11-hygiene-debts.md`），剩余 36 条。

---

## 1. P0：不做就没法叫"能用"

| # | 缺口 | 现状 | 依赖 / 卡点 | 验收标准 | 估算 |
|---|---|---|---|---|---|
| A1 | ~~**真实模型没跑过**~~ ✅ 已交付（2026-11-08） | 原状：全部验证基于 `tests/stub_llm.py`。现已有 `scripts/real_model_smoke.py` 用真 key 跑通 L1×3 + L2，见 `docs/reports/2026-11-08-a1-real-model-smoke.md` | — | 已验收：L1 P50 首 token 929 ms / P95 1064 ms、L2 调 `search_logs` 且引用 7001、`done.usage` 与 `agent_run` 一致（182/15、2286/108） | ✅ |
| A2 | ~~**App 没有会话列表**~~ ✅ 已交付（2026-11-08） | 原状：`ChatView.vue` 只用 `localStorage['petlumina-agent-session']` 记住最后一个会话；后端没有 `GET /agent/sessions`。现已有接口（分页 + 按最后消息时间倒序 + 本人隔离）与「历史会话」面板，见 `docs/reports/2026-11-08-a2-session-list.md` | — | 已验收：建 3 个会话、面板切换、刷新后仍在 | ✅ |
| A3 | **文件 / 图片 / 视频分析（RAG）** | `doc_file` / `doc_chunk` 表未建、无解析管道、无向量库；`Citation.locator` 的 `fileId#page`、`fileId#t=93s` 只是约定 | 需要存储（COS 已有）、解析（PDF/OCR/ffmpeg）、向量库（pgvector 优先） | 上传一张疫苗本照片 → 提问"下次疫苗什么时候" → 答案带可点回原图的引用；`doc_chunk` 有对应行 | 5–8 天 |

---

## 2. P1：该做，缺了用户会觉得"半成品"

| # | 缺口 | 现状 | 依赖 / 卡点 | 验收标准 | 估算 |
|---|---|---|---|---|---|
| B1 | **RocketMQ 生产实现（S1.9-c）** | 只有 `TaskQueue` 抽象 + 内存/Redis 实现；ADR-0009 定的是"MQ 在 Java 侧" | 本机无 broker、无 Docker；Java 需引 `rocketmq-spring-boot-starter` | 起一个 broker，Python 侧通过 `TaskQueue` 适配器收发；`tasks_smoke` 在 MQ 后端下 8/8 | 2–3 天 |
| B2 | **多副本韧性未验证** | 熔断状态在进程内；事件流 / 限流已走 Redis，但没起过两个实例 | 需要反向代理或两端口 + 压测脚本 | 起 2 个实例：同一用户的 SSE 续传在另一实例可读；限流合计 20/min 不被放大 2 倍 | 2 天 |
| B3 | **`processing` 泄漏扫描 + 僵死 run 收敛** | 队列只在启动时 `recover` 一次；**进程被强杀时，在途 `agent_run` 会永远停在 `running`**（A1 实测留下 `1794058693935000000`） | 需定期任务 + `XAUTOCLAIM` 或等价搬运；僵死 run 需先定策略（按 `create_time < now - stale_run_timeout_s` 收敛，还是外部巡检），多副本下不能无脑 cancel 别人的活 run | 消费者卡住 60s 后消息被另一 worker 接手、`processing` 不长期堆积；`running` 超过 15 分钟的运行被标记 `cancelled` 且管理端可见原因 | 1–1.5 天 |
| B4 | **死信运维只到"手动放回"** | 单 topic、最多 100 条、无自动重试策略、无告警 | 依赖 B3 的扫描器 | 死信 > N 时打 WARN 并可配置自动重试（指数退避）；批量重放（多 topic） | 1 天 |
| B5 | **可观测缺指标与追踪** | 只有 JSON 日志 + `/readyz`；无 `/metrics`、无 trace | 选型：Prometheus client + 可选 Langfuse（自建） | `/metrics` 暴露 `agent_run_total{status}`、`agent_run_latency_ms`、`agent_tokens_total`、`task_depth`；一次 run 能在 trace 里看到对应 span | 2–3 天 |
| B6 | **管理端缺"队列页 / 记忆页 / 知识图谱"** | 队列与记忆只有接口；图谱（G6）完全没做 | 前端工作量 | 队列页显示 depth/死信并可一键重放；记忆页可删除单条事实；图谱页至少渲染"宠物—事实—事件"三层 | 3–5 天 |
| B7 | **记忆不可删、不可导出** | 只有 `GET /agent/memory/me` | 隐私合规要求 | `DELETE /agent/memory/me?key=` 与 `GET /agent/memory/me/export`；删除后下一轮不再注入（有测试） | 1 天 |
| B8 | **前端没做自动重连** | `streamChat` 只有 `abort`；断网后靠用户点重试 | 已有 `replayRun` 与 `id:` 游标 | 断网 3s 后自动 `replayRun(afterSeq)` 续上，不重复追加已收到内容 | 1 天 |

---

## 3. P2：值得做，做之前要先定方案

| # | 缺口 | 现状 | 依赖 / 卡点 | 验收标准 | 估算 |
|---|---|---|---|---|---|
| C1 | **情景记忆 `memory_episode`** | 表建了，从未写入；无向量 | 依赖向量库选型（pgvector） | 一次"上周洗澡"的对话能被召回为情景片段，并带原消息 id | 3 天 |
| C2 | **用户画像 `profile_snapshot`** | 未建表、未实现 | 需要"从长期事实聚合画像"的规则 | 管理端能看"这只宠物的画像摘要"，且只由已确认事实生成 | 3 天 |
| C3 | **记忆抽取质量评测偏薄** | `evals` 里 `memory` 只有 2 条用例 | 需标注更多真实句式 | `memory` 套件 ≥40 条（含否定句"它不过敏"、多宠物、方言），阈值 ≥0.9 | 2 天 |
| C4 | **引用回跳只覆盖 log** | `kind==='log'` 才可点；post / health 没有 locator | 需要后端 VO 补定位字段 | 健康记录引用能跳到对应日期；帖子引用能跳到帖子详情 | 2 天 |
| C5 | **语音链路** | 无 | 参考 Open-LLM-VTuber（本地 ASR/TTS + 打断） | 浏览器录音 → 转写 → 走同一 `POST /agent/chat`；TTS 可关 | 5 天 |
| C6 | **桌宠** | 只有架构方案（§4 三档） | 资产管线（序列帧 → Live2D → VRM）+ 状态机 | A 档：App 内 H5 序列帧，`idle/happy/hungry/sleepy/worried` 五态；同台词 30 分钟不重复 | 8 天 |
| C7 | **压测与容量基线** | 无 | 依赖 B2 | 记录 20 并发 SSE 下的首 token P95、错误率、峰值内存；给出单实例上限 | 2 天 |
| C8 | **CI 未真正跑过** | `agent-ci.yml` 已写，本机无 docker | 推送后 GitHub Actions 状态未知 | Actions 上 `check` 与 `image` 两个 job 绿；首次跑通后把徽章贴到 README | 0.5 天 |
| C9 | **前端 e2e 自动化** | 全部靠手动开 Edge 点 | 需 Playwright + 固定桩数据 | 三条用例：登录→对话→看到引用；管理员→会话详情；429 → 提示 + 重试 | 2 天 |

---

## 4. P3：以后再说（先记着，别忘）

| # | 缺口 | 说明 |
|---|---|---|
| D1 | 多模态生成 | 桌宠形象由"部件库拼装"起步，生成式形象（单图→可动）属远期 |
| D2 | 规划层 L3（Plan-Execute） | 现在只有 L1/L2；L3 需要子任务编排与中断恢复，等真实需求出现再做 |
| D3 | 多租户 / 团队账号 | 现在一圈一人；多宠共享账号下的记忆归属需要重新设计 |
| D4 | 数据看板：成本按模型分账 | 现在只按用户 token 汇总 |
| D5 | 灰度与回滚 | 无 feature flag、无版本化 prompt |
| D6 | Prompt 版本管理 | `SYSTEM_PROMPT` 硬编码在 `app/graph/nodes.py`，改动无版本记录 |
| D7 | 备份与恢复演练 | MySQL/Redis 均无脚本化备份 |
| D8 | 国际化覆盖 | `chat.*` 已三语；Agent 错误码文案仍是中文硬编码（服务端返回 message） |
| D9 | 无障碍 | 对话页无 `aria-live`、无焦点管理 |

---

## 5. 原项目卫生债（S0，都已定位、未修）

这些不是 Agent 引入的，但会拖累"企业级"的说法。

| # | 位置 | 问题 | 影响 | 修法 |
|---|---|---|---|---|
| E2 | `controller/user/NotificationController.java:97-121` | 广播已读只插个人副本，`unread/count` 恒 ≥1 | 红点永远消不掉 | 计数排除已读副本；或加 `user_notification_read` 表 |
| E6 | `common/PageRequest` | `sortField`/`sortOrder` 从不生效 | 传了排序参数没效果 | Service 层拼 `orderBy`，或删字段别骗人 |
| E7 | `exception/GlobalExceptionHandler` | 全部返回 HTTP 200，靠 body `code` 区分 | 网关/监控无法按状态码告警 | 关键错误映射真实 HTTP 状态 |
| E8 | `service/admin/impl/DashboardServiceImpl.java:75-83` | 7 天趋势在 for 循环里每天发一次 `count()`（7 次 SQL），不是一次聚合 | 数据量大时仪表盘变慢 | 改成一次 `GROUP BY DATE(create_time)`；热门帖作者是否 N+1 未复核，复核后再补条目 |
| E9 | `pet-lumina-web/src/views/content/ViolationManage.vue` | 全本地 mock，`// TODO: call API`，无 api 模块 | 页面是假的 | 后端补违规接口，或先隐藏入口 |
| E10 | `pet-lumina-web` AddUser/EditUser | 提交只弹 toast；EditUser 预填硬编码"森林语者/138-xxxx-8888" | 管理端"能看不能改" | 接真实 create/update 接口 |
| E11 | `pet-lumina-app` 多页 | 41 处 `as any`（另有 1 处只是注释）、`currentPet.value!.id` 非空断言（`RecordHealthData.vue:187`、`AddPlan.vue:66`）、假数据残留（`WeeklyHealthDetail.vue:98-116`、`BentoDashboard.vue`、`UserInfo.vue:66-81`） | 类型形同虚设，改错要等运行时报错 | 先把 `as any` 换成真实类型（41 处有清单，可逐个清），再处理假数据 |
| E12 | `TopicController.java:172` + `PostServiceImpl.java:78-86` | `tags` 里搜 `"topic:<id>"` 的隐式约定，只有"从话题页发帖"会写 | 数据关联靠约定，易断 | 加 `post_topic` 关联表，或写清契约 |
| E13 | `backend/src/main/resources/application-dev.yml:6-10` | 数据库密码明文（`root/yzh521`）、COS 占位 | 泄露风险 | 改环境变量 + `.env.example` |

---

## 6. 里程碑映射

| 里程碑 | 覆盖本条目的 |
|---|---|
| S1.9-c | B1（RocketMQ）、B4（死信自动重试） |
| S2 记忆扩展 | B6（记忆页）、B7（可删/可导出）、C1、C2、C3 |
| S2.5 韧性 | B2、B3、B5、C7、C8 |
| S3 多模态 | A3、C4、C5 |
| S4 桌宠 | C6、D1 |
| S0 卫生债 | E1–E13（可随时插入，不占里程碑） |

## 7. 建议的下一步

1. ~~A2 会话列表~~ ✅ 2026-11-08 已交付（`GET /agent/sessions` + App「历史会话」面板）。
2. ~~A1 真实模型冒烟~~ ✅ 2026-11-08 已交付（真 key 跑通 L1×3 + L2，并抓到"僵死 run"问题，见 B3）。
3. ~~**E1 / E3 / E4 / E5 四个小修**~~ ✅ 已完成（2026-11-08）；下一批小修建议 E2 / E6 / E7。
