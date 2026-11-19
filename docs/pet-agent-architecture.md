# PetLumina Pet-Agent 架构设计（v0.1 草稿）

> 目标：把现有的「宠物健康管理 + 社区」三端系统，升级为「有记忆、能动手、有形象」的宠物智能体平台。
> 读者：产品 / 后端 / 前端 / 算法。本文只给架构与取舍，不含实现代码。
>
> 配套文档见 [文档地图](README.md)：ADR（决策史）、SPEC（契约）、SDD（分层设计）、REPORT（交付证据）。

---

## 1. 一句话定位与五条设计原则

**不是给 App 加一个聊天框，而是给每条宠物加一个「有长期记忆的数字分身」。**

| 原则 | 含义 | 反例（要避免） |
| --- | --- | --- |
| 记忆优先于话术 | 智能体的价值 80% 来自「它记得」，20% 才是「它会说」 | 把历史消息全塞进 prompt 当记忆 |
| 事实与生成分离 | 健康/喂养等事实必须来自结构化表，LLM 只负责解释与建议 | 让模型凭空编「它昨天吃了 200g」 |
| 工具即边界 | 模型能做什么，由工具目录决定，不由 prompt 决定 | prompt 里写「你可以删除数据」 |
| 可追溯 | 每条结论都能点回证据（日志/记录/文件页码/视频时间戳） | 只回一段漂亮的话 |
| 摊销成本 | 快通道回答 90% 的问题，慢通道（规划/反思）只给 10% 的复杂请求 | 每句话都跑 planner + reflection |

---

## 2. 现状盘点

### 2.1 可直接复用的资产

| 资产 | 位置 | 对 Agent 的价值 |
| --- | --- | --- |
| 结构化宠物档案 | `pet`（name/breed/age/healthScore/todaySteps…） | 画像与人设的直接输入 |
| 健康时序数据 | `health_record`（心率/睡眠/体重/步数/心情）、`health_plan` | RAG 之外最重要的一路「数值上下文」 |
| 行为日志 | `log_entry`（feeding/walking/grooming/medical/other + tags） | 情景记忆（episodic memory）天然来源 |
| 提醒与执行 | `reminder` + `/reminder/complete/{id}` | 第一个真正可写的工具（Agent 能「动手」的最小闭环） |
| 社交内容 | `post`/`comment`/`topic`/`follow`/`like` | 知识图谱的实体与关系来源 |
| 鉴权与用户体系 | Sa-Token + `user.role` + `@AuthCheck` | 会话级隔离与后台权限的现成抓手 |
| 统一响应与大整数契约 | `BaseResponse` + `Long→String` | Agent 服务必须沿用，否则前端 ID 精度炸 |

### 2.2 缺口

| 缺口 | 影响 |
| --- | --- |
| 没有会话/消息/运行轨迹（trace） | 无历史、无回放、无评测，管理端无从下手 |
| 没有向量库与文档表 | 文件/照片/视频分析无处落地 |
| 没有长期记忆层 | 每次对话都从零开始，「像真的」无从谈起 |
| 没有工具注册与调用审计 | ToolCall 等于给模型裸奔的数据库连接 |
| 没有宠物形象资产与动画状态机 | 桌宠只能是个贴图 |

---

## 3. 总体架构

```
┌──────────────────────────── 通道层 (Channels) ────────────────────────────┐
│  App 聊天页   App 桌宠(H5 Sprite/Live2D/VRM)   管理后台   未来的微信/语音   │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ SSE / WebSocket（流式 token + 工具事件）
┌───────────────────────────────▼──────────────────────────────────────────┐
│                       Agent Runtime（独立服务，Python）                    │
│  路由 Router(快/慢) → Planner → Executor(ReAct loop) → Reflector          │
│  上下文装配 Context Builder：画像 + 短期记忆 + 检索片段 + 工具结果          │
│  工具网关 Tool Gateway：MCP 协议 + 权限 + 确认门 + 审计                    │
└──────┬──────────────────┬───────────────────┬────────────────────────────┘
       │                  │                   │
┌──────▼──────┐   ┌───────▼────────┐   ┌──────▼─────────────┐
│ 记忆层       │   │ 检索层 RAG      │   │ 工具层 Toolbox     │
│ 短期/长期/画像│   │ 向量+BM25+重排  │   │ pet/log/health/....│
└──────┬──────┘   └───────┬────────┘   └──────┬─────────────┘
       │                  │                   │ HTTP/MCP
┌──────▼──────────────────▼───────────────────▼────────────────────────────┐
│  既有 Spring Boot（业务真源）：MySQL 14 表 + Redis + COS + 管理端 API     │
│  新增存储：pgvector / Qdrant（向量）、Neo4j 或 AGE（图谱）、对象存储（原始文件）│
└──────────────────────────────────────────────────────────────────────────┘
```

**为什么 Agent Runtime 独立成服务**：模型调用、流式、重试、并发、评测迭代的节奏与 Java 业务完全不同；用 Python 能吃下 LangGraph / LlamaIndex / 各类解析库生态；Java 侧只保留「业务真源 + 权限 + 计费」。代价是多一个部署单元——用 Docker Compose 起步即可。

---

## 4. 六大能力设计

### 4.1 Agent Runtime：三层调度，不要一个巨大 ReAct

| 层 | 触发条件 | 形态 | 预算 |
| --- | --- | --- | --- |
| L1 直答 | 闲聊、已知事实、单工具查询 | 单次 LLM + 最多 1 轮工具 | ~1 次调用 |
| L2 ReAct | 需要 2~4 步工具串联（查记录→对比→给建议） | 最多 6 步循环，步间写 scratchpad | 3~6 次调用 |
| L3 Plan-Execute | 多目标、跨天、需要用户确认 | 生成 TODO 列表 → 逐项执行 → 汇总 | 8~15 次调用 |

**Reflection 只挂在两处**：①L3 每个步骤失败时；②回答涉及健康建议/写操作时做一次「证据自检」（我引用的记录 id 真的存在吗）。**不要**每轮都反思——那是烧钱的自我感动。

状态机（建议直接用 LangGraph 表达，节点即上表）：

```
route ─┬─> direct ─────────────────────────────> respond
       ├─> react ──(tool_call)*──> reflect? ────> respond
       └─> plan ─> [step1..stepN] ─> reflect ──> respond
```

**运行轨迹必须落库**（`agent_run` / `agent_step`）：管理端的回放、评测、成本分析全靠它，这也是出问题时的唯一证据链。

### 4.2 记忆系统：三层，各管一件事

| 层 | 存什么 | 存哪 | 生命周期 | 写入时机 |
| --- | --- | --- | --- | --- |
| 短期 | 最近 N 轮原文 + 滚动摘要 | Redis（会话级） | 会话结束 + 摘要转长期 | 每轮追加，超阈值触发摘要 |
| 长期-事实 | 「用户说它不吃三文鱼」「对鸡肉过敏」这类稳定断言 | `memory_fact` + 向量 | 长期，可被新证据推翻（带 confidence） | 对话后异步抽取（异步，不阻塞回答） |
| 长期-情景 | 「6/3 晚上呕吐一次」这类带时间的事件 | `memory_episode`（关联来源消息 id） | 长期，可衰减 | 当前从对话规则抽取；结构化日志/健康行回填未做 |

**关键取舍**：能被结构化表表达的事件（喂食、体重、就医）**不要**用 LLM 抽取，应直接写 `memory_episode` 并指回原表——这是本项目最大的优势，绝大多数宠物 App 没有这份数据。当前 S1.34 只做了对话抽取这一条路，结构化回填仍待接入。

**画像（User/Pet Profile）不是一段 prompt**，而是一份**带证据、带版本的结构化文档**：

```json
{
  "petId": "...", "version": 7, "updatedAt": "...",
  "traits": { "activityLevel": "low", "appetite": "picky", "anxiety": "separation" },
  "preferences": [{ "text": "喜欢被摸下巴", "confidence": 0.8, "evidence": ["msg:10231"] }],
  "routine": { "walkHours": [7, 19], "mealHours": [8, 18] },
  "riskFlags": [{ "text": "膝关节旧伤，避免跳跃", "source": "log:5521" }]
}
```

每次更新生成新版本，管理端可 diff——「用户画像」在后台应该是可审计的，不是黑箱。

### 4.3 多模态 RAG

```
文件上传统一入口 → 解析 → 归一化为「文档单元」→ 切块 → 向量化 → 入库
                                    │
照片 → EXIF/OCR/图像描述(多模态模型) ─┤
视频 → 抽帧(1fps/场景切换) + ASR 转写 ─┘  每块带 timestamp，回答可点回秒
```

| 模态 | 处理链 | 检索单元 | 引用形式 |
| --- | --- | --- | --- |
| PDF/Word/表格 | 文本抽取 + 表格转 markdown | 512~800 token 块，重叠 15% | `fileId#page` |
| 图片 | OCR（疫苗本/处方单）+ 图像描述 | 描述 + OCR 文本双通道 | `fileId` |
| 视频 | 抽帧 + faster-whisper/FunASR 转写 + 场景分段 | ASR 段落 + 关键帧描述 | `fileId#t=93s` |
| 健康数值 | **不走 RAG**，走结构化查询工具 | — | `health_record:{id}` |

检索：**混合检索**（向量 + BM25）→ rerank（bge-reranker 类）→ 取 top-k 进上下文；知识型问题可再叠一层图谱扩展（见 4.5）。

### 4.4 ToolCall

用 **MCP（Model Context Protocol）** 做工具协议：一次实现，App/后台/桌宠/未来渠道全部复用；第三方（如日历、地图）也能即插即用。

工具目录（第一版只放这些，宁少勿多）：

| 命名空间 | 工具 | 读写 | 是否需要确认 |
| --- | --- | --- | --- |
| `pet` | `get_pet_profile` / `list_pets` | R | 否 |
| `health` | `query_health_records(range)` / `add_health_record` | R/W | 写需确认 |
| `log` | `query_logs` / `create_log` | R/W | 写需确认 |
| `reminder` | `list_reminders` / `complete_reminder` / `create_reminder` | R/W | 写需确认 |
| `knowledge` | `search_docs` / `get_doc_chunk` | R | 否 |
| `community` | `search_posts` | R | 否 |
| `profile` | `update_profile_fact` | W | 需确认（画像变更要可见） |

**三条硬约束**：
1. 工具入参永远带 `userId`（从服务端会话注入，**不信模型填的**），越权直接拒绝；
2. 写工具两段式：`propose` → 用户在 App 点确认 → `commit`；
3. 每次调用写 `tool_call_log`（参数、耗时、结果摘要、run_id），管理端可查。

### 4.5 管理端：从「管数据」到「管 Agent」

新增四个页面：

| 页面 | 内容 | 复用 |
| --- | --- | --- |
| 会话工作台 | 会话列表（用户/宠物/渠道/耗时/成本/是否命中记忆）→ 右侧时间线回放（消息 + 工具调用 + 检索片段 + token 花费） | 现有 `el-table` + 抽屉 |
| 记忆管理 | 按用户/宠物查看 fact/episode，可编辑、可失效、可看证据 | 表格 + JSON 查看器 |
| 知识图谱 | 实体-关系图（用户-宠物-症状-食物-话题-工具），点击节点看关联会话 | G6 / Cytoscape.js |
| 评测与成本 | 评测集（20~200 条问题 + 期望要点）、回归通过率、token/会话、P95 延迟 | ECharts |

**知识图谱建模建议**（图谱展示的价值 = 能被追问，不是好看）：

```
(User)-[:OWNS]->(Pet)-[:HAS_RECORD]->(HealthRecord)
(Pet)-[:ATE]->(Food)-[:LINKED_TO]->(Symptom)
(Pet)-[:HAS_EVENT]->(LogEntry)-[:MENTIONS]->(Topic)
(User)-[:PREFERS]->(Topic)   (Pet)-[:FOLLOWS_PLAN]->(HealthPlan)
```

自动抽取用 LLM + 人工校验双轨：**先只抽「食物-症状」「药物-反应」两类**（医疗价值最高、噪声最可控），其余靠结构化表直接投影成图——比全自动抽取靠谱一个数量级。

### 4.6 App 桌宠：三档形态，按资产成本递进

| 档位 | 技术 | 成本 | 效果 | 建议 |
| --- | --- | --- | --- | --- |
| A 精灵图 | 序列帧 + CSS/Canvas 状态机 | 1 天 | 够萌，动作有限 | **MVP 首选** |
| B Live2D | `pixi-live2d-display` + 部件绑定 | 1~2 周（含美术） | 呼吸/眨眼/跟随/口型 | 第二阶段 |
| C 3D/VRM | three.js + VRM + 混合表情 | 3 周+ | 最强沉浸 | 长期 |

**形象生成流水线**（「根据宠物习性生成 app 宠物形象」的落地方式）：

1. 用户上传 3~5 张爱宠照片 → 抠图/统一视角 → 风格化成「Q 版」参考图；
2. 图生图产出**部件级素材**（身体/头/眼/耳/尾/嘴），或直接用 2D 骨骼（Live2D Cubism / Spine）绑定；
3. 用 `pet` 表 + 画像决定**外观参数**（毛色、体型、耳型）与**性格动画权重**（活泼→多跑动，胆小→多缩角落）；
4. 生成 `pet_avatar` 资产包（manifest：动作名 → 帧/参数），App 与桌宠共用。

**行为引擎**（这是「像真的」的关键，不是模型，是状态机）：

```
输入：时间、健康数据、提醒完成情况、聊天情绪、用户是否在线
状态：idle / happy / hungry / sleepy / worried / playing / working
规则优先，LLM 兜底：状态迁移用规则表（可测），台词才用 LLM（可生成）
```

台词生成带**节流**：同一状态 30 分钟内不重复、每天最多 N 条主动消息；用户静音/深夜自动降级为纯动画。桌宠主动打扰是留存神器，也是卸载第一原因。

DSH 桌面端已有的 `dsh-pet` 插件就是这套形态的现实样本（托盘常驻 + 余额/工作状态 + 每 300s 的「碎碎念」+ 桌面 helper 桥接），可以直接作为**行为引擎与气泡节流**的参考实现，把「碎碎念」换成「宠物状态播报」即可。

---

## 5. 数据模型增量（12 张新表）

```sql
-- 会话与消息
agent_session(id, user_id, pet_id, channel ENUM('app','desktop','admin'),
              title, status, last_active_at, token_in, token_out, cost, create_time)
agent_message(id, session_id, role ENUM('user','assistant','tool','system'),
              content MEDIUMTEXT, content_type, attachments JSON,
              tokens, latency_ms, create_time)
-- 运行轨迹（回放/评测的底座）
agent_run(id, session_id, message_id, route ENUM('direct','react','plan'),
          model, token_in, token_out, cost, latency_ms, status, error, create_time)
agent_step(id, run_id, seq, type ENUM('think','tool','observe','reflect'),
           name, input_json, output_json, latency_ms, error)
-- 记忆
memory_fact(id, user_id, pet_id, subject, predicate, object, confidence,
            evidence JSON, valid_from, valid_to, is_delete, create_time)
memory_episode(id, user_id, pet_id, session_id, kind, source_message_id, summary,
               detail, occurred_at, is_delete, create_time)
-- 画像（版本化）
profile_snapshot(id, user_id, pet_id, version, payload JSON, created_by, create_time)
-- 文档与检索
doc_file(id, user_id, pet_id, kind ENUM('pdf','doc','img','video','audio'),
         cos_key, mime, size, status ENUM('pending','parsed','failed'),
         meta JSON, create_time)
doc_chunk(id, file_id, seq, text MEDIUMTEXT, page, ts_start, ts_end,
          token_count, embedding_id)
-- 图谱
kg_entity(id, kind, name, props JSON, embedding_id)
kg_relation(id, from_id, to_id, kind, weight, evidence JSON, create_time)
-- 工具审计 + 反馈
tool_call_log(id, run_id, name, args JSON, result_digest, status, latency_ms, create_time)
agent_feedback(id, message_id, user_id, rating, reason, create_time)
```

索引要点：`agent_message(session_id, create_time)`、`agent_step(run_id, seq)`、`memory_fact(pet_id, subject)`、`doc_chunk(file_id, seq)`、`kg_relation(from_id, kind)`。

> 向量：起步用 **pgvector**（少一个组件），量级过千万再上 Qdrant。图谱：起步 Neo4j（可视化生态最成熟），若不想多一个库可用 PostgreSQL + Apache AGE。

---

## 6. 开源选型对照表

| 能力 | 推荐 | 备选 | 用法与取舍 |
| --- | --- | --- | --- |
| Agent 编排 | [LangGraph](https://github.com/langchain-ai/langgraph) | 自研状态机 / Dify | 图结构表达 ReAct/Plan 最直接，可持久化中断与恢复（HITL 确认门靠它） |
| 记忆层 | [mem0](https://github.com/mem0ai/mem0) | [Letta(MemGPT)](https://github.com/letta-ai/letta) | mem0 是「加在现有系统上的记忆抽取层」，侵入小；Letta 是「agent 即服务」，改造大 |
| 时序知识图谱 | [Graphiti](https://github.com/getzep/graphiti) | Neo4j 手写 | Graphiti 天生带「事实有效期」，适合宠物健康这种会变的事实 |
| 轻量图 RAG | [LightRAG](https://github.com/HKUDS/LightRAG) | [GraphRAG](https://github.com/microsoft/graphrag) | LightRAG 成本低、可增量；GraphRAG 全量建图贵，适合离线知识库 |
| 文档解析/RAG 引擎 | [RAGFlow](https://github.com/infiniflow/ragflow) | LlamaIndex | 想要「上传即用」的解析+引用，RAGFlow 现成；深度定制就用 LlamaIndex |
| 应用编排平台 | [Dify](https://github.com/langgenius/dify) | — | 适合后台运营同学自建提示词/工作流，与自研 runtime 可共存 |
| 语音（二期） | [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) | FunASR + faster-whisper | 前者给「语音对话+Live2D」全链路参考 |
| 桌宠/虚拟形象 | [airi](https://github.com/moeru-ai/airi) + [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) | [VPet](https://github.com/LorisYounger/VPet)（WPF 桌宠，行为/互动设计参考） | airi 有 VRM/Live2D + 记忆 + 语音的完整拼装方式 |
| 工具协议 | [MCP](https://modelcontextprotocol.io) | 自定义 JSON Schema | 标准化后 App/桌面/第三方共用一套工具 |
| 图谱可视化 | [G6](https://github.com/antvis/G6) / Cytoscape.js | AntV G6VP | G6 国内文档好、布局算法全 |

**不要直接拿来做产品骨架的**：Dify（做成产品后台可以，做运行时太黑箱）、GraphRAG（全量建图成本和延迟不适合对话）、VPet（WPF，桌面端可参考，不能进 App）。

---

## 7. 四阶段路线图（每阶段都有可验收产出）

| 阶段 | 范围 | 验收标准（硬指标） |
| --- | --- | --- |
| **S1 会话骨架**（2 周） | `agent_session/message/run/step` + 流式对话 + L1 直答 + 3 个只读工具（宠物档案/健康/日志）+ 管理端会话工作台 | App 能连续对话；后台能按会话回放每一步工具调用；P95 首 token < 1.5s |
| **S2 记忆与画像**（2~3 周） | 短期摘要 + fact 抽取 + episode 自动写入 + 画像 v1 + 记忆管理页 | 20 条「跨会话记忆」测试用例 ≥16 通过；画像每条含证据 id |
| **S3 多模态 RAG**（3 周） | 文件/图片/视频上传解析 + 混合检索 + 引用回跳 | 上传疫苗本照片问「下次疫苗什么时候」，答案给出引用位置；引用可点回原文件/时间戳 |
| **S4 编排与桌宠**（3 周） | Plan-Execute + HITL 确认门 + 写工具（提醒/记录）+ 桌宠 A 档 + 图谱页 | 端到端场景 3 条全通：①「它最近吃得少吗」→ 查数据 → 建议 → 建提醒；②「上周呕吐几次」→ 检索日志 → 图谱关联；③ 桌宠按健康状态变表情并播报 |

S1 之前必须先补的两件小事（否则后面全是返工）：
1. 管理端 `vue-tsc` 真正生效（`tsconfig.json` 的 `files: []` + `--noEmit` 导致 0 检查，实测 8 个类型错误）；
2. ID 契约统一（后端 `Long→String`，前端两套类型仍是 `number`）——Agent 的 `sessionId/petId` 会大量穿层，这个坑必须提前填。

---

## 8. 成本、风险与「先不做」清单

| 项 | 现状判断 | 对策 |
| --- | --- | --- |
| Token 成本 | L1/L2/L3 混用会让成本失控 | 路由前置（规则 + 小模型分类），画像与检索片段做预算裁剪（每次 ≤ 2k token） |
| 幻觉 | 模型爱编健康数值 | 数值只能来自工具结果，回答里没有 `evidence` 一律降级为「我不确定」 |
| 医疗合规 | 宠物医疗建议有风险 | 定位「观察 + 提醒 + 建议就医」，不诊断不开药；所有建议附免责 |
| 隐私 | 照片/病历属敏感数据 | COS 私有读 + 短时签名 URL；记忆删除要能级联到向量与图谱 |
| 桌宠打扰 | 主动消息 = 留存也是卸载源 | 节流 + 免打扰时段 + 一键静音；默认只播报，不弹窗 |
| 评测缺失 | 没有评测就没有迭代 | S1 就建 20 条评测集，每次改 prompt/模型跑回归，通过率进后台看板 |

**S1~S2 明确不做**：多 Agent 协作、自研向量库、全自动图谱抽取、语音对话、3D 形象、跨用户社交推理。

---

## 9. 三个待定决策

1. **Runtime 语言**：Python 独立服务（生态最好，多一个部署单元）vs Java 内嵌 Spring AI（少一个服务，生态弱）。建议前者。
2. **记忆归属**：记忆跟「用户」还是跟「宠物」？建议**主键为 (user, pet)**，多宠物用户各自独立人格。
3. **桌宠运行形态**：App 内 H5 悬浮宠物 vs 系统级桌面挂件。建议先 App 内（可控、可埋点），桌面端复用 `dsh-pet` 的桥接模式。

---

## 10. 引入 Harness：能，但要分清「哪一层的壳」

**先说结论**：可以，而且应该——但引入的是**执行引擎层**的 harness，不是把 DSH/OpenHands 这类「单用户桌面 harness」当成产品的多租户运行时。三层各管各的：

```text
产品壳（我们写）：鉴权 / 会话表 / 配额计费 / SSE 转发 / 管理端     ← Java 现有栈
Harness（用现成的）：循环 + 工具 + 上下文装配 + 中断 + 检查点 + 追踪  ← Python
沙箱（按需再加）：视频抽帧 / OCR / 代码执行                          ← 独立进程或 E2B
```

### 10.1 Harness 到底买到了什么

| 能力 | 自己写要付的成本 | harness 直接给 |
| --- | --- | --- |
| 工具调用循环 + 重试 + 参数校验 | 每加一个工具改一遍循环 | 统一 Tool 协议（MCP 直连） |
| 人类确认门（写操作/健康建议） | 手搓「挂起→存态→恢复」 | interrupt/resume + checkpointer |
| 断点续跑（App 关掉再回来） | 自己存中间态 | 每次 super-step 落检查点 |
| 上下文压缩 | 自己写摘要策略 | 内置裁剪/摘要钩子 |
| 可观测 | 打点全靠自觉 | trace = 树状，逐节点耗时/成本 |
| 评测回归 | 手写对比脚本 | 同一 trace 格式喂评测集 |

### 10.2 三条路线（按侵入度排）

| 路线 | 代表 | 适用 | 风险 |
| --- | --- | --- | --- |
| **A. 编排框架自建 harness**（推荐） | LangGraph + MCP + Langfuse | 要掌控 prompt/成本/多租户 | 需要自己写状态图（约 1~2 周） |
| B. 复用成熟 harness | [AgentScope Runtime](https://github.com/agentscope-ai/agentscope-runtime)、[OpenHands](https://docs.openhands.dev/) | 需要沙箱跑代码/媒体处理 | 事件流协议、状态存储、权限模型都要适配 |
| C. 纯自研 loop | 200 行 + MCP client | 只有 3~5 个只读工具 | 一旦加写工具/中断就欠债 |

**为什么 A 是默认**：本项目 90% 请求是 L1 直答，L2 最多 6 步——只需要「图 + 检查点 + 中断」，不需要沙箱。LangGraph 的 `interrupt()` 恰好覆盖 propose/commit 确认门，`checkpointer` 放 Redis 就能和 `agent_run/agent_step` 表对齐（harness 只存执行态，业务真源仍在 MySQL）。

### 10.3 什么时候才上 B 与沙箱

触发条件（任一）：① 需要跑 ffmpeg 抽帧 / OCR / 代码执行；② 需要并发跑多个 Agent 做批量生产；③ 桌面端要本地执行。此时把「重工具」下沉到 AgentScope Runtime 或 E2B 的独立容器，产品服务只做调度与审计。**S1~S2 不开**。

### 10.4 DSH 的定位（重要）

DSH 本身就是一个 harness（本仓库的会话就跑在它上面：skills / subagents / MCP / compaction / jobs）。它能直接用，但**只适合内部**：运营 Copilot、批量内容生产、评测标注、桌宠大脑调试。原因：它是单用户桌面会话模型，没有多租户隔离、配额、弹性伸缩，事件流也不是给 C 端 App 的。

正确姿势：**开发期用 DSH 造 skill/工具/评测集，产品期用 LangGraph 复刻同一套 prompt 与工具定义**（工具走 MCP，两边共用一份）。

### 10.5 引入 harness 的四个坑（必须提前设计）

1. **事件流映射**：harness 吐的是内部事件（node start/end、tool_call、token），要映射成 App 能消费的 SSE（`delta` / `tool` / `done` / `error` 四类），并保证断线可续（`Last-Event-ID`）。
2. **状态双写**：harness 的 checkpointer 只管执行态；`agent_message` 必须由产品层写，否则换 harness 就丢历史。
3. **工具越权**：harness 的工具默认高权限。必须过网关：白名单 + `userId` 服务端注入 + 写操作两段式 + `tool_call_log`。
4. **成本口径**：token 计量在 harness 内部，要回传到 `agent_run`，否则配额和看板两套账。

### 10.6 验收标准（S1 期间可验证）

- 用户提问 → 产生 `agent_run` + 至少 1 条 `agent_step`，且能与 Langfuse trace 一一对应；
- 触发写工具 → 图挂起、用户 30s 后确认 → 能 resume 且不重复执行；
- 断网重连 → 从上次 `Last-Event-ID` 续上，不重复计费。

---

## 11. GitHub 开源调研（2026-11 快照）

> 采集方式：GitHub REST `search/repositories`（匿名配额，★为查询当时数值，会变）。目的不是"列名单"，而是每个仓库回答一个问题：**我们哪个坑已经被别人填过、值不值得抄。**

### 11.1 按我们缺的能力分组

| 分组 | 仓库 | ★ | 可借鉴的具体点 | 结论 |
| --- | --- | --- | --- | --- |
| Harness/编排 | [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | 85k | 「SuperAgent harness」的分层：sandboxes / memories / tools / skill / subagents / message gateway | **抄分层**，不抄实现（我们不需要沙箱） |
| Harness/编排 | [deer-flow/llm-space](https://github.com/deer-flow/llm-space) | 2.1k | harness 步骤可视化、失败回放、评测面板 | **管理端会话工作台的原型**（对应 S1 后台页） |
| Harness/编排 | [ZHangZHengEric/Sage](https://github.com/ZHangZHengEric/Sage) | 1.2k | RSI harness：工具/skill/MCP/有状态执行的组织方式 | 参考工具注册与状态机划分 |
| Harness/编排 | [affaan-m/ECC](https://github.com/affaan-m/ECC) | 298k | agent 配置/技能/记忆的"清单化"组织（偏方法论集合） | 当**提示词与技能库**参考，不当运行时 |
| Harness/编排 | [ruvnet/ruflo](https://github.com/ruvnet/ruflo) | 81k | swarm 编排 + adaptive memory + 向量 RAG 的组合 | 只在 S4「多 Agent」阶段再看 |
| 记忆 | [mem0ai/mem0](https://github.com/mem0ai/mem0) | 68.5k | `add/search/get_all/delete` 四算子 + 事实抽取 + 更新/去重策略 | **S2 直接对标它的抽取与去重规则** |
| 记忆 | [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) | 59k | "会学习的记忆"：把反馈回灌进记忆选择 | 借鉴「记忆打分 + 衰减」而非全量引入 |
| 记忆 | [aiming-lab/SimpleMem](https://github.com/aiming-lab/SimpleMem) | 3.9k | 终身记忆（文本+多模态）的写入/检索分离 | 多模态记忆的结构参考（S3） |
| 记忆 | [TeleAI-UAGI/telemem](https://github.com/TeleAI-UAGI/telemem) | 493 | Mem0 替代：语义去重 + 视频推理记忆 | 视频记忆（S3 抽帧后打标）参考 |
| RAG/图谱 | [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | 93.7k | 深度文档解析 + 引用回跳 + 可视化切块 | **S3 的解析与引用体验直接对标** |
| RAG/图谱 | [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) | 40.6k | 轻量实体+关系图，增量构建，便宜 | **我们图谱的主选**（替代全量 GraphRAG） |
| RAG/图谱 | [1517005260/graph-rag-agent](https://github.com/1517005260/graph-rag-agent) | 2.4k | GraphRAG + LightRAG + Neo4j 的融合实现 + 自建评估框架 | 中文场景落 Neo4j 的实现参考 |
| RAG/图谱 | [raphaelmansuy/edgequake](https://github.com/raphaelmansuy/edgequake) | 2.3k | Rust 版 GraphRAG，性能与内存优化 | 量大后的性能参考（现在不用） |
| 桌宠 | [ayangweb/BongoCat](https://github.com/ayangweb/BongoCat) | 24.5k | Tauri 跨平台桌宠：透明窗口、点击穿透、托盘 | **桌面端外壳的首选参考**（若做系统级） |
| 桌宠 | [NanmiCoder/cc-haha](https://github.com/NanmiCoder/cc-haha) | 15.3k | 多 Agent 工作台 + "任务感知"桌宠（有活干才动） | 借鉴「状态驱动动画」而非定时轮播 |
| 桌宠 | [rullerzhou-afk/clawd-on-desk](https://github.com/rullerzhou-afk/clawd-on-desk) | 6.6k | 像素风桌宠监控 agent 运行状态 | 借鉴"低帧率序列帧 + 状态机"，成本极低 |
| 桌宠 | [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) | 14.6k | 本地语音 + Live2D + 语音打断的完整链路 | 语音二期直接参考 |
| 桌宠 | [guansss/pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) | 1.5k | PixiJS 的 Live2D 插件，表情/口型 API | **B 档桌宠的渲染层** |
| 桌宠 | [shinyflvre/Mate-Engine](https://github.com/shinyflvre/Mate-Engine) / [liupig/xiaokeai](https://github.com/liupig/xiaokeai) | 3.9k / 334 | VRM 桌宠（3D） | C 档再评估 |
| 桌宠 | [kiyotakali/Miru](https://github.com/kiyotakali/Miru) | 193 | 桌宠 + 长期记忆 + 主动陪伴 | 小而全的"陪伴逻辑"参考 |
| 桌宠 | [edison7009/EchoBird](https://github.com/edison7009/EchoBird) | 3.5k | Token 用量养成宠物 | 成长/数值设计参考（我们换成健康分） |
| 评测 | [claw-eval/claw-eval](https://github.com/claw-eval/claw-eval) | 906 | 人类验证任务 + 重复试验 + 通过率报告 | **S1 评测集的形态直接照这个来** |
| 图像->形象 | [pkhungurn/talking-head-anime-demo](https://github.com/pkhungurn/talking-head-anime-demo) | 2k | 单张图生成可动头部（眨眼/口型） | 「上传照片生成宠物形象」的技术下限 |

### 11.2 五条可执行结论

1. **记忆层对标 mem0，但表结构自己建**：mem0 的价值在「抽取什么、怎么去重、怎么失效」，不在它的库；我们已有 `memory_fact(valid_from/valid_to)`，直接按它的四算子设计服务接口。
2. **图谱用 LightRAG 思路，不用 GraphRAG 全量**：宠物健康知识是「小实体、强关系、要可解释」，LightRAG 的实体+关系+社区摘要成本低一个数量级；`graph-rag-agent` 的评估脚本可参考。
3. **harness 只抄分层不抄实现**：deer-flow 的 sandbox/memory/tool/skill/subagent/gateway 六件套正好映射我们的 S1→S4；`llm-space` 的「步骤检视 + 失败回放」就是管理端工作台的 MVP 形态。
4. **桌宠用状态机 + 序列帧起步**（clawd-on-desk 路线），渲染层二期换 pixi-live2d-display，外壳只在做系统级时用 Tauri（BongoCat）。别一开始就 VRM。
5. **评测从 S1 就建**（claw-eval 形态）：20 条用例、可重复、通过率进后台看板——没有这条，后面所有 prompt 调优都是玄学。

### 11.3 明确不借鉴

- `ECC`（298k）是 agent 配置/方法论集合，不是运行时，抄进来只会增加复杂度；
- `ruflo` 的 swarm 模型超出本阶段需求（我们 90% 是单 Agent 直答）；
- `RAGFlow` 整套部署（ES/Infinity + 重解析链）对 S3 之前的我们过重，先只抄"引用回跳"的交互。

---

## 12. S1 已落地（`backend-agent/`）

代码在 `backend-agent/`，与三端解耦（不改现有任何文件），技术栈 FastAPI + LangGraph 1.2.20 + aiomysql。

**S1.5 重构（按"别把 demo 当架构"的要求重做了一遍）**：单文件 `service.py` 那种写法已删除，改成
`domain → llm → tools → storage → graph → runtime → api` 的单向依赖分层，每层可单独替换：

| 层 | 关键约束 | 验收证据 |
| --- | --- | --- |
| `domain/` | 纯 Python；路由是确定性关键词分类，不吃模型 | `test_router.py` 15 条参数化 |
| `llm/` | 429/5xx 重试、坏 JSON 标 `parse_error`、usage 兜底 | `ScriptedModel` 让测试不依赖真模型 |
| `tools/` | schema 由 pydantic 生成；网关六道防线；写操作默认隐藏 | `test_gateway.py` 11 条（伪造 user_id、预算、审计 digest） |
| `storage/` | 内存/MySQL 共用一份契约测试 | `test_repository_contract.py` 7 条 |
| `graph/` | `route → prepare →(L1 结束 \| L2: agent ↔ tools)`，hop 硬上限 | `test_graph_l2.py` 5 条（含"模型第一次调用必须已带上下文"回归） |
| `runtime/` | 事件可续传、run 必有终态、用量=图内+流式 | `test_api.py` 12 条（续传三方式等价） |
| `api/` | 依赖全注入；身份只从 token 换 | 越权读他人会话 → 404 |

**三层证据（都能自己跑）**：

| 手段 | 命令 | 结果 |
| --- | --- | --- |
| 单测 | `.venv\Scripts\python -m pytest -q` | 245 项（不带 DSN 为 244 passed + 1 skipped） |
| 评测（阈值硬卡） | `.venv\Scripts\python -m evals.run` | routing 15/15、safety 6/6、memory 48/48 |
| 真进程冒烟 | `python -m scripts.e2e_smoke`（配 `tests/stub_java.py` + `tests/stub_llm.py`） | 10/10：L2 真的调了 `search_logs`、citation 指向记录 7001、续传等价、越权 404 |

**重构中抓到的真 bug（值得记一笔）**：L2 原来从 `route` 直接跳 `agent`，跳过了 `prepare`，
模型第一次被调用时 `messages` 是空的——测试用脚本模型看不出来，只有接真 SSE 才暴露。
现在 `route → prepare` 是必经边，并加了那条回归断言。**这就是"能跑"和"对"的差别。**

**S1.6 P0/P1（工程化，不改业务语义）**：

| 轮次 | 内容 | 证据 |
| --- | --- | --- |
| P0 | 单行 JSON 日志 + `x-request-id`、`/readyz`、依赖锁定、多阶段 Dockerfile、CI（ruff → pytest → evals → docker build） | `docs/reports/2026-11-07-s1.6-p0.md`：59 passed、evals 100%、e2e 10/10 |
| P1 | 每用户配额（429 + `Retry-After`）、单 run token 预算、事件总线 Redis Stream 选项、长期记忆（`memory_fact` + 抽取算子 + 召回注入；`memory_episode` 见 S1.34）、用量聚合接口 | `docs/reports/2026-11-08-s1.6-p1.md`：92 passed、P1 冒烟 9/9、浏览器端到端 |
| S1.7 | 管理端「会话工作台」：`role` 来自 Java `/auth/current`、4 个 `/agent/admin/*` 只读接口、`admin.access` 审计、两个页面（列表 + 详情：对话流/运行轨迹/长期记忆） | `docs/reports/2026-11-08-s1.7-admin.md`：101 passed、管理端冒烟 6/6、Edge 端到端 |
| S1.8 P2 | 真机联调（MySQL 8.0.29 + Redis 5.0.14）、Redis 客户端固定 RESP2、用户维度幂等键（重试回放不重跑）、LLM/后端双熔断 + `/readyz` 联动 | `docs/reports/2026-11-08-s1.8-p2.md`：122 passed、四个冒烟 10/9/6/8、真机 `/readyz` 四项 check |
| S1.9-a | 旁路任务队列 `TaskQueue`（内存/Redis 两实现、`BRPOPLPUSH` 在途恢复、死信与重试）：记忆抽取与工具审计移出请求路径，队列满退回同步 | `docs/reports/2026-11-08-s1.9-task-queue.md`：134 passed、四个冒烟 10/9/6/8、真机 Redis 队列 `LLEN=0` + `task memory observed` 日志 |
| S1.9-b | 队列运维闭环：启动时先把在途消息搬回队列（崩溃不丢任务）、死信重放（`attempt` 归零）、`GET /agent/admin/tasks` 现场接口，两项均 admin-only + 审计 | `docs/reports/2026-11-08-s1.9b-deadletter.md`：142 passed、五个冒烟 10/9/6/8/8、真机"在途 1 → 重启回收 → `tool_call_log` 落库" |
| S1.10–S1.14 | 补 App 历史会话（`GET /agent/sessions` + 抽屉面板）、真实模型冒烟，并把原项目 13 笔卫生债清零：验证码随机化、管理端类型门禁、社区分类/今日提醒、广播已读独立表、排序白名单、真实 HTTP 状态码、仪表盘聚合、数据库口令出仓库、违规管理真实化、管理端用户增改、App 类型收紧、话题归属 `post.topic_id` | `docs/reports/2026-11-08-a2-session-list.md`、`…-a1-real-model-smoke.md`、`…-s1.11…`–`…-s1.14-e9-e12.md`：后端 27 单测、App 37 单测、三端构建、Edge 三页实点 |

| S1.15 / A3 | 文档问答 RAG：`doc_file`/`doc_chunk`、文本/PDF/OCR/视频抽帧解析、切分 + 确定性嵌入、`search_docs` 工具（引用 `kind=doc`）、App 附件上传 | `docs/reports/2026-11-08-s1.15-doc-rag.md`：169 passed、`rag_smoke` 10/10、Edge 上传→提问→引用；D1–D7 |
| S1.16 / B3·B5·B7 | 在途消息可见性超时巡检（`claimed` ZSET + `attempt+1`）、`/metrics` 六组指标、记忆删除/导出（物理删除 + 版本化导出） | `docs/reports/2026-11-08-s1.16-ops.md`：181 passed、`ops_smoke` 11/11（含"造一条死掉的在途消息 → 巡检搬回 → 落库"） |
| S1.17 / B6 | 管理端「队列运维 / 长期记忆 / 知识图谱」三页 + 删记忆（审计）+ 三层图谱接口；Java `LoginUserVO` 补 `role` | `docs/reports/2026-11-08-s1.17-admin-console.md`：183 passed、Edge 三页实点 |
| S1.18 / C2 | 版本化宠物画像 `profile_snapshot` + 确定性 builder + 记忆消费后重算（同 consumer，避免空画像）+ 四接口 + 管理端画像页 | `docs/reports/2026-11-08-s1.18-profile.md`：203 passed、真机 `v2 facts=3` |
| S1.19 / B4·B2·C6 | 失败进 `:retry` ZSET 指数退避（5s→600s 封顶）+ `redrives` 有界自动重投（默认关）；双副本一致性验证；桌宠档 A（`derivePetMood` 纯函数 + 内联 SVG） | `docs/reports/2026-11-08-s1.19-b4-b2-pet.md`：208 passed、`multi_replica_smoke` 8/8、App 50 tests |

**S1 未做**（下一步）：Langfuse 追踪、`agent_run` 与 trace 对齐的自动化校验、多副本熔断共享状态（Redis）、并发压测、RocketMQ 实现（S1.9-c，需 broker）、僵死 `agent_run` 超时收敛（B3 剩余部分）、死信告警阈值（B4 剩余）、桌宠档 B/C（Live2D/VRM）。

---

## 13. Web 端接入（`pet-lumina-app` 聊天页）

S1 的运行时是一堆 HTTP 接口，用户看不见。这一节记录把它接进 App 网页端的过程与验收证据。

### 13.1 前端分层（与新分层对齐的最小集合）

| 文件 | 职责 | 为什么不塞进组件 |
| --- | --- | --- |
| `src/api/sse.ts` | 纯 SSE 文本解析（`push`/`flush`、多行 data、`\r\n`、注释行） | 不碰网络才能单测逐块喂数据 |
| `src/api/agent.ts` | `streamChat` / `replayRun` / `fetchSessionMessages` / `fetchSessions` + 五个类型守卫 | 传输层只做传输；UI 不写 `as any` |
| `src/utils/chatStream.ts` | `applyAgentEvent(bubble, event)` 归约器 + `historyToBubbles` | 事件→界面是纯函数，可被 10 条单测钉死 |
| `src/views/chat/ChatView.vue` | 只负责渲染、滚动、输入法、错误重试、401 跳登录 | 组件里没有业务判断 |

**为什么不用 `EventSource`**：它不能带 `satoken` 请求头、不支持 POST 请求体、续传只会重连同一 URL。
所以走 `fetch + ReadableStream`，自己按 `id:` 游标续传——和后端 `/agent/runs/{run_id}/events?after=` 正好对上。

### 13.2 交互约定

- 会话 id 存 `localStorage['petlumina-agent-session']`，进页面先 `fetchSessionMessages` 回放历史；服务端 404（内存模式重启）就静默换新会话；
- 顶栏「历史会话」打开底部面板（`fetchSessions`，每次打开重拉）：列出本人会话，显示标题/时间/消息数，当前会话高亮；选中后先清空气泡再回读，避免串会话（BACKLOG A2）；
- 流式期间气泡带 `▍` 光标，工具调用显示成 chip（`chat.tool.<name>`），引用 chip 可点，`kind=log` 跳 `/log/{id}`；
- 401/`unauthorized` 清 `satoken` 并跳登录；其余错误保留最后一条用户消息给"重试"；
- Enter 发送、Shift+Enter 换行，`event.isComposing` 保护中文输入法；
- 对话页是全屏沉浸式，`MainLayout` 在 `route.name === 'chat'` 时收起底部导航（否则输入框被胶囊导航压住）。

### 13.3 验证证据

| 手段 | 命令 | 结果 |
| --- | --- | --- |
| 类型检查 + 构建 | `npm run build`（`vue-tsc -b && vite build`） | 通过，产出 `ChatView-*.js` 10.9 kB |
| 单测 | `npx vitest run` | 20 passed（`sse.spec.ts` 10 + `chatStream.spec.ts` 10） |
| 浏览器端到端 | stub_java:8097 + stub_llm:8098 + uvicorn:8099 + vite:5173 | 登录 → 首页 → 问 Lumina → 流式回答 + 「翻找记录」工具 chip + 「疫苗记录」引用 chip |

### 13.4 这轮抓到的两个真 bug

1. **首页白屏**：`PetStatusBento.vue` 直接 `pet.todaySteps.toLocaleString()`，接口少一个字段就是整页渲染崩溃（Vue 的渲染异常会把整棵树带走）。已改成 `?? 0` 兜底——接口字段永远可能缺，模板不能假设。
2. **输入框被导航盖住**：`ChatView` 用了 `fixed bottom-0`，而 `MainLayout` 的胶囊导航是 `fixed bottom-3 z-50`，两者重叠且导航在上层。改成对话页隐藏导航，比"算 100px 偏移"更可靠。

> 这两个都不是"agent 的问题"，但都是"接进去才会发现的问题"——所以端到端验证不能省。

