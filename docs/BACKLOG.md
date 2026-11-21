# 未完成事项清单（Backlog）

- 状态：活文档（每次交付后更新；做完的条目移到对应 REPORT，并从本表删除）
- 更新：2026-11-21
- 基线：`main` @ S1.37 提交（2026-11-21，见 `docs/reports/2026-11-21-s1.37-admin-model-cost.md`）

## 0. 怎么读这份文档

1. **只写"没做完"的**。做了的事在 `docs/reports/` 里，不在这里重复。
2. 每条都有**验收标准**：能写成命令或可观察现象，否则不算条目，是愿望。
3. 优先级按"卡不卡产品可用"分：P0 阻断、P1 该做、P2 值得做、P3 以后。
4. 估算是"一个人、熟悉代码"的量级，不是承诺。

统计：**P0 3 条（A1、A2、A3 已交付）· P1 8 条（B2/B3/B4/B5/B6/B7/B8 已交付，剩 1 条 B1）· P2 10 条（C1、C2、C3、C4、C6、C7、C8、C9、C10 已交付，剩 1 条 C5）· P3 9 条（D4、D6、D8 已交付，剩 6 条）· 原项目卫生债 0 条**，原计划 42 条 + 新增 C10，剩余 8 条（P1 1 + P2 1 + P3 6）。各批证据：E1/E3/E4/E5 见 `docs/reports/2026-11-08-s1.11-hygiene-debts.md`；E2/E6/E7 见 `docs/reports/2026-11-08-s1.12-e2-e6-e7.md`；E8/E13 见 `docs/reports/2026-11-08-s1.13-e8-e13.md`；E9/E10/E11/E12 见 `docs/reports/2026-11-08-s1.14-e9-e12.md`；A3 见 `docs/reports/2026-11-08-s1.15-doc-rag.md`；B5/B7 见 `docs/reports/2026-11-08-s1.16-ops.md`；B6 见 `docs/reports/2026-11-08-s1.17-admin-console.md`；C2 见 `docs/reports/2026-11-08-s1.18-profile.md`；B2/B4/C6 见 `docs/reports/2026-11-08-s1.19-b4-b2-pet.md`；B8 见 `docs/reports/2026-11-14-s1.23-auto-reconnect.md`；B3 收尾见 `docs/reports/2026-11-14-s1.24-stale-run-reaper.md`；C4 见 `docs/reports/2026-11-14-s1.25-citation-jump-links.md`；C8 见 `docs/reports/2026-11-14-s1.26-ci-docker-context.md`；C3 见 `docs/reports/2026-11-15-s1.27-memory-evals.md`；D6 见 `docs/reports/2026-11-15-s1.28-prompt-version.md`；C7 见 `docs/reports/2026-11-16-s1.29-capacity-baseline.md`；C7 上限见 `docs/reports/2026-11-17-s1.31-capacity-ceiling.md`；B7 App 入口见 `docs/reports/2026-11-17-s1.30-app-memory.md`；C9 见 `docs/reports/2026-11-18-s1.32-browser-e2e.md`；C10 见 `docs/reports/2026-11-18-s1.33-admin-model-config.md`；C1 见 `docs/reports/2026-11-19-s1.34-memory-episodes.md`；D8 见 `docs/reports/2026-11-21-s1.36-agent-error-i18n.md`；D4 见 `docs/reports/2026-11-21-s1.37-admin-model-cost.md`。

---

## 1. P0：不做就没法叫"能用"

| # | 缺口 | 现状 | 依赖 / 卡点 | 验收标准 | 估算 |
|---|---|---|---|---|---|
| A1 | ~~**真实模型没跑过**~~ ✅ 已交付（2026-11-08） | 原状：全部验证基于 `tests/stub_llm.py`。现已有 `scripts/real_model_smoke.py` 用真 key 跑通 L1×3 + L2，见 `docs/reports/2026-11-08-a1-real-model-smoke.md` | — | 已验收：L1 P50 首 token 929 ms / P95 1064 ms、L2 调 `search_logs` 且引用 7001、`done.usage` 与 `agent_run` 一致（182/15、2286/108） | ✅ |
| A2 | ~~**App 没有会话列表**~~ ✅ 已交付（2026-11-08） | 原状：`ChatView.vue` 只用 `localStorage['petlumina-agent-session']` 记住最后一个会话；后端没有 `GET /agent/sessions`。现已有接口（分页 + 按最后消息时间倒序 + 本人隔离）与「历史会话」面板，见 `docs/reports/2026-11-08-a2-session-list.md` | — | 已验收：建 3 个会话、面板切换、刷新后仍在 | ✅ |
| A3 | ~~**文件 / 图片 / 视频分析（RAG）**~~ ✅ 已交付（2026-11-08） | `doc_file`/`doc_chunk` + 解析管道 + hash 嵌入检索 + `search_docs` 工具 + App 附件入口；图片/视频因本机缺 `tesseract`/`ffmpeg` 降级为"不支持并给原因" | 见 `docs/reports/2026-11-08-s1.15-doc-rag.md`；`rag_smoke` 10/10 | 已完成 |

---

## 2. P1：该做，缺了用户会觉得"半成品"

| # | 缺口 | 现状 | 依赖 / 卡点 | 验收标准 | 估算 |
|---|---|---|---|---|---|
| B1 | **RocketMQ 生产实现（S1.9-c）** | 只有 `TaskQueue` 抽象 + 内存/Redis 实现；ADR-0009 定的是"MQ 在 Java 侧" | 本机无 broker、无 Docker；Java 需引 `rocketmq-spring-boot-starter` | 起一个 broker，Python 侧通过 `TaskQueue` 适配器收发；`tasks_smoke` 在 MQ 后端下 8/8 | 2–3 天 |
| B2 | ✅ **多副本韧性**（2026-11-08，S1.19） | 已交付：8099/8100 双副本，`scripts.multi_replica_smoke` 8/8（跨副本事件回放、同幂等键同 run、任务不重复消费、记忆共享、限流共享）；**熔断仍是进程内状态**（已知限制，写进 SPEC 6.10） | 剩余：熔断跨副本共享（Redis 计数） | 已达成：两个实例同时在线，8 项检查全过 | 2 天 |
| B3 | ✅ **`processing` 泄漏扫描 + 僵死 run 收敛** | 已全部交付：`claimed` ZSET + 巡检搬回（`attempt+1`，2026-11-08 S1.16）；僵尸 run 由 `app/runtime/janitor.py` 收敛（启动收尸 + 60s 定时巡检，2026-11-14 S1.24） | 无剩余 | 已达成：消费者卡住 60s 后消息被另一 worker 接手、`processing` 不长期堆积（`scripts.ops_smoke` 第 10–11 项）；`running` 超 15 分钟被标记 `cancelled` 且 `error` 写明原因（管理端 `AdminRunOut.error` 可见）；不误杀/幂等/上线即收尸/配置护栏 4 条用例 | 0.5 天 |
| B4 | ✅ **死信自动重试**（2026-11-08，S1.19） | 已交付：失败进 `:retry` ZSET 指数退避（`5s→600s` 封顶）、到期提升、`redrives` 有界自动重投（默认关闭）；**死信告警阈值仍未做** | 剩余：死信超阈值打 WARN / 接告警通道 | 已达成：退避/到期/上限三条用例 + 真机退避链；`TASK_DLQ_REDRIVE_INTERVAL_S` 控制是否自动重投 | 1 天 |
| B5 | ✅ **可观测缺指标**（2026-11-08，S1.16） | 已交付 `/metrics`（6 个指标）；**trace 未做**（Langfuse 仍是可选项） | 剩余部分需选型 Langfuse / OpenTelemetry | 已达成：`pet_agent_runs_total{route,status}`、`tokens_total{direction}`、`tool_calls_total{tool,ok}`、`queue_depth{topic}`、HTTP 两项；**待办**：一次 run 在 trace 里能看到对应 span | 2 天 |
| B6 | ✅ **管理端缺"队列页 / 记忆页 / 知识图谱"**（2026-11-08，S1.17） | 已交付三页：队列运维（现场 + 死信重放）、长期记忆（按用户查/删）、知识图谱（宠物—事实—事件三层力导向图）；后端补 `DELETE /agent/admin/memory` 与 `GET /agent/admin/graph` | 前端工作量 | 已达成：Edge 实点三页 + `test_admin.py` 两例（删记忆审计、三层图谱） | 已完成 |
| B7 | ✅ **记忆不可删、不可导出**（2026-11-08，S1.16） | 已交付：后端 `DELETE /agent/memory/me` 与 `GET /agent/memory/me/export`（S1.16）、管理端记忆页（B6，S1.17）、App「我的记忆」页（S1.30：通用+每宠合并展示 / 范围筛选 / 二次确认删除 / 聚合导出） | 隐私合规要求 | 已达成：删除后导出为空、下一轮不再注入（`test_memory_api.py` 5 例 + `scripts.ops_smoke`）；App 端证据见 `docs/reports/2026-11-17-s1.30-app-memory.md`（155 tests + tsc 0 + build 0）；**待办**：真机浏览器 e2e（归 C9）、宠物多时的后端聚合接口（当前 N+1 请求，≤3 只可接受） | 已完成 |
| B8 | ✅ **前端断线自动重连**（2026-11-14，S1.23） | 已交付：后端把 run 生命周期从 HTTP 连接里拆出来（`RunSupervisor` 托管执行 + `?follow=1` 挂到终态），前端 `resilientChat.ts` 按 `[3s,3s,6s]` 重连、`after` 恒为已收最大 id、界面显示「正在重连（第 N 次）」；顺带修掉内存仓储 `get_run` 状态永停 `running` 的缺陷 | 剩余：跨副本依赖 Redis 事件日志（已支持，见 B2）；无取消接口（另立需求） | 已达成：`test_reconnect.py` 5 例（关消费端不取消运行 / 游标续传不重不漏 / 跟随等到 done / 快照语义不变 / 幂等不二次执行）、`resilientChat.spec.ts` 8 例、全量 backend 202 passed + 1 skipped、App 136 tests + tsc 0 + build 0 | ✅ |

---

## 3. P2：值得做，做之前要先定方案

| # | 缺口 | 现状 | 依赖 / 卡点 | 验收标准 | 估算 |
|---|---|---|---|---|---|
| C1 | ✅ **情景记忆 `memory_episode`**（2026-11-19，S1.34） | 已交付第一刀：对话规则抽取 10 类事件（洗澡/驱虫/疫苗/体检/就医/绝育/美容/剪指甲/呕吐/腹泻）+ 相对时间归一到日、问句/否定/习惯不写；`source_message_id` 指回原消息，`(user_id, source_message_id)` 唯一保证队列重复投递幂等；召回用事件类型命中 + 字符重叠 + 90 天新鲜度（阈值 0.50，最多 3 条）注入 system；新增 `GET/DELETE /agent/memory/me/episodes`，导出升 v2 含 `episodes`。**未做**：向量语义召回、结构化日志/健康行回填、同一条消息多事件 | 向量库选型（pgvector）只剩语义召回这一层；结构化回填依赖日志/健康写路径接入 | 已达成：两轮对话「上周给豆豆洗澡了」→「上次洗澡是什么时候」能召回情景并带日期与来源消息 id（`test_api.py` 集成用例）；`pytest` 283 passed + 1 skipped、`ruff` 全绿；证据 `docs/reports/2026-11-19-s1.34-memory-episodes.md` | 已完成（首刀 0.5 天） |
| C2 | ✅ **用户画像 `profile_snapshot`**（2026-11-08，S1.18） | 已交付：版本化快照 + 确定性 builder + 记忆消费后重算 + 四接口 + 管理端画像页 | `routine`/行为趋势、人工修正、版本 diff、画像导出仍未做 | 已达成：`test_profile.py` 20 例、真机 `v2 facts=3`、Edge 实点画像页；**待办**：从日志聚合作息 | 已完成 |
| C3 | ✅ **记忆抽取质量评测**（2026-11-15，S1.27） | 已交付：`memory` 套件 2→48 条（`mem-ext-*` 28 / `mem-neg-*` 8 / `mem-dialect-*` 5 / `mem-multi-*` 4 / `turns` 3），`run_memory` 拆成 `extract`（事实集合全等 + `forbid`）/ `observe`（真跑 `MemoryService`，校验 `pets` 与 `ops`）/ `turns` 三种形状，阈值 1.0→0.9；先红后绿量出 5 类真实缺陷并修 `app/memory/extract.py`（问句当名字、过敏值吞副词、偏好值带动词、裸「喜欢」误抽、否定句全漏） | 剩余：真机日志抽样回填用例、阈值提到 0.95、同义值改成候选列表；方言只有粤/川渝/东北各 1–2 条且是手写标注 | 已达成：`memory 48/48 = 100%`、`routing 15/15`、`safety 6/6`、`pytest` 222 例（221 通过 + 1 跳过，MySQL 变体未开 DSN）、`ruff` 全绿；统计口径见 `docs/reports/2026-11-15-s1.27-memory-evals.md` | 已完成 |
| C4 | ✅ **引用回跳 locator 化**（2026-11-14，S1.25） | 已交付：`citation.locator` 改为 App 内路由（`/log/{id}`、`/post/{id}`、`/pet-detail/{id}`、`/weekly-health-detail?petId=…&date=…`）；新增只读工具 `search_posts` 补上帖子引用来源；前端 `citationRoute()` 不再按 kind 硬编码，老会话按 kind 兜底 | 未做：真机人工点一次（本机 Java 8080 未起） | 已达成：健康引用带周记录最大日期并高亮定位、帖子引用跳 `/post/{id}`；`test_citations.py` 7 例 + `e2e_smoke` 10/10 里 citation 已是 `/log/7001` | |
| C5 | **语音链路** | 无 | 参考 Open-LLM-VTuber（本地 ASR/TTS + 打断） | 浏览器录音 → 转写 → 走同一 `POST /agent/chat`；TTS 可关 | 5 天 |
| C6 | ✅ **桌宠（引擎版：canvas + 程序化动画）**（2026-11-08，S1.19 档 A → S1.20 分层 SVG → S1.21 图片生成 → S1.22 照 dsh-pet 重写引擎） | 已交付：①照 `dsh-pet` 源码同构的引擎——权重分档/播完回链/工作六态/睡觉三段/弹簧拖拽+甩出封顶+落地挤压/命中区保底；②29 段程序化动画 + 13 种道具 + 气泡 + 长按菜单（吃白饭/打盹/叫醒/去聊天/收起）；③全局挂件（换页面不丢）+ 登录页不渲染 + 位置归一化持久化；④图片生成形象沿用 S1.21 管线。**未做**：视频素材档、Live2D/VRM、音频 | 剩余：引入 dsh-pet 视频素材（需署名/非商用确认）、手动涂抹修正、音效与语音、余额/工作时长事件刷新 | 已达成：App 128 tests（引擎 45 + 外壳 10）、tsc 0、build 0、真机首页/对话页/登录页三态 + 帧差 4879 | 9 天 |
| C7 | ✅ **压测与容量基线**（2026-11-16，S1.29） | 已交付：`scripts/load_baseline.py`（无新依赖、逐档重启 app、SSE 首个 `delta` 计时、进程树峰值工作集、`/metrics` 对账）+ 16 条纯函数单测；桩 `tests/stub_llm.py` 的 `time.sleep` 改 `asyncio.sleep` 并把首 token 延迟/帧间隔/每帧字数参数化 | 剩余：L2（工具链最多 6 跳）与真模型长尾分布未量；单实例上限已扫（S1.31：首 token P95 口径 140 并发达标 / 150 超限） | 已达成：20 并发 × 40 请求 40/40 成功、错误率 0%、首 token P50 1151ms / P95 1201ms（桩固定 900ms → 服务侧开销 301ms）、峰值工作集 97MB；证据 `docs/reports/2026-11-16-s1.29-capacity-baseline.md`；S1.31 每档 300 请求扫到 150 并发：140 达标（首 token P95 2994ms）、150 两次 3100/3202ms，错误率 0%，证据 `docs/reports/2026-11-17-s1.31-capacity-ceiling.md` | 2 天 |
| C8 | ✅ **CI 真正跑通**（2026-11-14，S1.26） | 已交付：`docker build` 的构建上下文写重（`defaults.run.working-directory: backend-agent` + `docker build ... backend-agent` → 上下文变成 `backend-agent/backend-agent`）从 S1.6 起 34 次运行 34 次红，已改成 `.`；`on.push` 加 `branches: [main]` 避免推标签重复触发。CI 运行 #35 两个 job 全绿（53 秒） | 剩余：CI 仍只覆盖 `backend-agent`，前端三件套与 `backend/` 的 `mvn test` 未纳入 | 已达成：Actions 上 `lint + test + evals` 与 `docker build` 两个 job 绿（run #35，`conclusion=success`）；README 已贴徽章 | 0.5 天 |
| C9 | ✅ **前端 e2e 自动化**（2026-11-18，S1.32） | 已交付：Playwright + 系统 Edge（`channel: msedge`）+ 固定桩；`scripts/e2e-stack.ps1` 一条命令起停 stub_java/stub_llm/Agent/App/管理端；三条用例真实跑通（App 登录→对话→引用回跳、管理员会话详情、429 提示+重试） | 剩余：接入 CI；管理端 `npm run build` 在本机需把 `TEMP/TMP/ESBUILD_TMPDIR` 指向仓库内目录（环境问题，已记录） | 已达成：e2e `3 passed (22.2s)`、runner exit 0；App 155 tests + `vue-tsc` 0 + build 0；`pytest` 249 例（248 通过 + 1 跳过，未开 DSN） | 2 天 |
| C10 | ✅ **管理员统一模型配置**（2026-11-18，S1.33） | 已交付：管理端「模型配置」页 + `GET/PUT/POST /agent/admin/model-config*`；单行表 `agent_model_config` / memory JSON；Key 加密且只回显末 4 位；测试连接、保存前构建、热切换、env 回退 | 剩余：真机 MySQL DSN 验证、浏览器点击、KMS/私网地址白名单；页面 e2e 待 8080 空闲后补 | 已达成：`pytest` **258 例（257 通过 + 1 跳过）**、新增 9 例模型配置测试、`ruff` 全绿；管理端 `vue-tsc` 0 + build 0（2303 modules，18.21s）；证据 `docs/reports/2026-11-18-s1.33-admin-model-config.md` | 已完成 |

---

## 4. P3：以后再说（先记着，别忘）

| # | 缺口 | 说明 |
|---|---|---|
| D1 | 多模态生成 | 桌宠形象由"部件库拼装"起步，生成式形象（单图→可动）属远期 |
| D2 | 规划层 L3（Plan-Execute） | 现在只有 L1/L2；L3 需要子任务编排与中断恢复，等真实需求出现再做 |
| D3 | 多租户 / 团队账号 | 现在一圈一人；多宠共享账号下的记忆归属需要重新设计 |
| D4 | ✅ **数据看板：成本按模型分账**（2026-11-21，S1.37） | 已交付：`GET /agent/admin/usage` 增 `by_model`（模型、runs、prompt/completion/total tokens、`cost_usd`）；memory 与 MySQL 同口径，空模型归 `unknown`，分账合计可对回顶层总量；单价由 `PET_AGENT_MODEL_PRICES`（USD / 1M tokens）配置，未配置 `cost_usd=null`；管理端会话工作台新增「按模型分账」表。**剩余**：MySQL 查询未开 DSN 真库验证；价格是当前配置快照，不是财务结算账 | 无外部依赖，已本地完成 | 已达成：`pytest` **290 passed + 1 skipped**（未开 DSN）、`ruff` 全绿；管理端 `vue-tsc -b` 0 + `npm run build` 0；证据 `docs/reports/2026-11-21-s1.37-admin-model-cost.md` | 已完成（0.5 天） |
| D5 | 灰度与回滚 | 无 feature flag、无按用户/渠道切流；**提示词版本化已由 D6 交付（2026-11-15）**，`PROMPT_VERSION` 可直接当分流键，但还没有按比例/按用户的路由层 |
| D6 | ✅ **Prompt 版本管理**（2026-11-15，S1.28） | 已交付：`SYSTEM_PROMPT` 从 `app/graph/nodes.py` 搬到 `app/graph/prompts.py` 的版本登记表（`PROMPT_VERSIONS` 只增不改 + `FROZEN_SHA256` 手写冻结哈希；当前 `2026-11-15.1`，270 字，sha256 `a04df4e3…6806c9`），`nodes.SYSTEM_PROMPT` 名字不变；改正文不升版本 → 单测红（变异实验：改成「4 句以内」后 2 条红、还原即绿）；run 的 assistant `meta` 与 `run finished` 日志都带 `prompt_version`。剩余：管理端会话详情未透出 message `meta`（版本号只在库与日志里，界面看不到）；版本号靠人手写日期；拦不住「同时改正文+哈希且故意不升版本」。证据 `docs/reports/2026-11-15-s1.28-prompt-version.md`（`pytest` 229 例 0 失败 1 跳过、`evals` 69 条全绿、`ruff` 全绿） |
| D7 | 备份与恢复演练 | MySQL/Redis 均无脚本化备份 |
| D8 | ✅ **Agent 错误码三语化**（2026-11-21，S1.36） | 已交付：新增 `src/utils/agentError.ts`——14 个服务端 code + `http_<status>` → `agentError.*`，`rate_limited`/`circuit_open` 带 `retry_after_s` 时用 `*WithRetry`（向上取整）；`chatStream` 透出 `errorCode`/`retryAfterS`；`AgentRequestError.detail` 解析 `detail.retry_after_s` 与 `Retry-After`；对话页上传/发送/SSE 错误与「我的记忆」统一走 `translateAgentError`；`agentError` 20 键三语同步；SPEC 增 4.3.1 与 I46。剩余：管理端/Java 错误未纳入（当前范围只到 App Agent 链路）；服务端 `message` 仍中文兜底 | 未覆盖 `pet-lumina-web`、Java `/api/v1` 错误；翻译为手写，未做真机语言切换人工验收 | 已达成：`agentError.spec.ts` 8 例、`chatStream.spec.ts` 12 例、`ChatView.error.spec.ts` 4 例、`ChatView.a11y.spec.ts` 6 例、`MyMemory.spec.ts` 8 例；全量 `vitest` 176/176（19 文件）、`vue-tsc -b` 0、`npm run build` 0；后端 283 passed + 1 skipped、`ruff` 全绿（本轮无后端改动）；证据 `docs/reports/2026-11-21-s1.36-agent-error-i18n.md` | 已完成（0.5 天） |
| D9 | ✅ **对话页无障碍基线**（2026-11-20，S1.35） | 已交付：消息区 `role=region` + 名称 + `aria-busy` + 可聚焦；独立 `role=status` 播报区只报「开始回复 / 回复完成」，避免流式 delta 刷屏；错误条 `role=alert`；标题改 `h1`；输入框 `aria-label` + `aria-describedby` 指向免责说明；历史面板 `aria-modal`、打开聚焦、`Tab` 圈定、`Esc` 关闭、关闭还焦点；`chat.a11y.*` 三语。剩余：真实读屏人工验收；全站其余页面未覆盖（见 D10） | 读屏软件人工体验（NVDA/VoiceOver）需真机；`inert` 背景禁用、动效降级未做 | 已达成：`ChatView.a11y.spec.ts` 6/6；全量 `vitest` 161/161（17 文件）、`vue-tsc -b` 0、`npm run build` 0；证据 `docs/reports/2026-11-20-s1.35-chat-a11y.md` | 已完成（0.5 天） |
| D10 | 全站无障碍审计 | 对话页基线已由 D9 交付；设置、我的记忆、社区、管理端等页面未做系统审计（焦点顺序、对比度、表单错误播报、`prefers-reduced-motion`） | 需要先定审计清单与自动化工具；避免逐页零散改 | 关键页面键盘可走通、读屏可读、对比度达 WCAG AA；动效降级可关 | 3 天 |

---

## 5. 原项目卫生债（S0）——**已清零（2026-11-08）**

E1–E13 全部完成，本表不再列条目。证据分布：

| 批次 | 覆盖 | 报告 |
|---|---|---|
| S1.11 | E1 验证码、E3 管理端类型门禁、E4 社区分类、E5 今日提醒 | `docs/reports/2026-11-08-s1.11-hygiene-debts.md` |
| S1.12 | E2 广播已读、E6 `sortField`、E7 真实 HTTP 状态码 | `docs/reports/2026-11-08-s1.12-e2-e6-e7.md` |
| S1.13 | E8 仪表盘聚合、E13 数据库口令出仓库 | `docs/reports/2026-11-08-s1.13-e8-e13.md` |
| S1.14 | E9 违规管理、E10 管理端用户增改、E11 前端类型/假数据、E12 话题归属 | `docs/reports/2026-11-08-s1.14-e9-e12.md` |

遗留观察（不构成卫生债，随对应里程碑处理）：`init.sql` 未合并 v2.13–v2.15 的新表，全新环境需按顺序执行迁移脚本（已写进根 `README.md`）。

---

## 6. 里程碑映射

| 里程碑 | 覆盖本条目的 |
|---|---|
| S1.9-c | B1（RocketMQ）、B4（死信自动重试） |
| S2 记忆扩展 | ~~B6（记忆页/图谱页）~~ ✅ S1.17、B7 ✅、C1、C2、C3 |
| S2.5 韧性 | B2、B3、B5、C7、C8 |
| S3 多模态 | A3、C4、C5 |
| S4 桌宠 | C6、D1 |
| S0 卫生债 | E1–E13（可随时插入，不占里程碑） |

## 7. 建议的下一步

1. ~~A2 会话列表~~ ✅ 2026-11-08 已交付（`GET /agent/sessions` + App「历史会话」面板）。
2. ~~A1 真实模型冒烟~~ ✅ 2026-11-08 已交付（真 key 跑通 L1×3 + L2，并抓到"僵死 run"问题，见 B3）。
3. ~~**E1 / E3 / E4 / E5 四个小修**~~ ✅ 已完成（2026-11-08）。
4. ~~**E2 / E6 / E7 三个小修**~~ ✅ 已完成（2026-11-08）：广播已读改用 `notification_read` 表、`sortField` 白名单生效、错误码映射真实 HTTP 状态；下一批建议 E8 / E13（仪表盘 N+1、明文密码）。
5. ~~**E8 / E13**~~ ✅ 已完成（2026-11-08）：仪表盘趋势改一次 `GROUP BY`、宠物分布改聚合、热门帖作者改批量查；数据库口令移出仓库（环境变量 / `application-local.yml`，且在全仓库清掉了明文）。见 `docs/reports/2026-11-08-s1.13-e8-e13.md`。
6. ~~**E9 / E10 / E11 / E12**~~ ✅ 已完成（2026-11-08）：违规管理接真实接口、管理端新增/编辑用户真落库、话题归属改 `post.topic_id`、App `as any` 清零 + 假数据下架。见 `docs/reports/2026-11-08-s1.14-e9-e12.md`。**卫生债至此清零**，下一批建议 A3（文件/图片/视频 RAG）或 B1（RocketMQ）。
7. ~~**A3 文档问答 RAG**~~ ✅ 已完成（2026-11-08）：`doc_file`/`doc_chunk` + 解析/切分/嵌入/检索 + `search_docs` 工具 + App 附件入口，`rag_smoke` 10/10。见 `docs/reports/2026-11-08-s1.15-doc-rag.md`。
8. ~~**B3 / B5 / B7 运维三件套**~~ ✅ 已完成（2026-11-08）：在途消息巡检回收（`claimed` ZSET + `attempt+1`）、`/metrics` 六个指标、记忆删除/导出；`ops_smoke` 11/11。见 `docs/reports/2026-11-08-s1.16-ops.md`。
9. ~~**B6 管理端三页**~~ ✅ 已完成（2026-11-08）：队列运维（现场 + 死信重放）、长期记忆（查/删）、知识图谱（宠物—事实—事件）；Edge 实点三页，`pytest` 183 passed。见 `docs/reports/2026-11-08-s1.17-admin-console.md`。
10. ~~**C2 用户画像**~~ ✅ 已完成（2026-11-08）：`profile_snapshot` 版本化快照 + 确定性 builder + 记忆消费后重算 + 四接口 + 管理端画像页；`pytest` 203 passed、真机 `v2 facts=3`、Edge 实点。见 `docs/reports/2026-11-08-s1.18-profile.md`。
11. ~~**B4 死信自动重试 / B2 多副本 / C6 桌宠**~~ ✅ 已完成（2026-11-08，S1.19）：退避 `5s→600s` 封顶 + `redrives` 有界重投（默认关）；双副本 `multi_replica_smoke` 8/8；桌宠档 A（纯函数状态机 + H5 组件）。`pytest` 208 passed、App 50 tests。见 `docs/reports/2026-11-08-s1.19-b4-b2-pet.md`。下一批建议 **B3 僵死 run 收敛**、**C1 `memory_episode` 情景记忆** 或 **B1 RocketMQ**。
12. ~~**C1 情景记忆（第一刀）**~~ ✅ 已完成（2026-11-19，S1.34）：写入 `memory_episode` 并带来源消息 id、按来源消息幂等、确定性召回注入 system、列表/删除/导出 v2；`pytest` 283 passed + 1 skipped、`ruff` 全绿。见 `docs/reports/2026-11-19-s1.34-memory-episodes.md`。**剩余**：向量语义召回（S2）、结构化日志/健康行回填。
13. ~~**D4 成本按模型分账**~~ ✅ 已完成（2026-11-21，S1.37）：`by_model` + `PET_AGENT_MODEL_PRICES` + 管理端表格；`pytest` 290 passed + 1 skipped、管理端 `vue-tsc` 0 + build 0。见 `docs/reports/2026-11-21-s1.37-admin-model-cost.md`。下一批建议 **B1 RocketMQ**（需先有 broker）或 **C5 语音链路**（均需外部依赖/多日预算）；无外部依赖的小切片只剩 **D7 备份恢复脚本**、**D10 全站 a11y 审计**。
