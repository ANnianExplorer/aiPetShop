# ADR-0009 事件回放用 Redis Stream，异步任务用消息队列（RocketMQ 可选）

- 状态：Accepted
- 日期：2026-11-07
- 决策人：架构（本仓）
- 计划：[s1.9-task-queue.md](../plans/s1.9-task-queue.md)

## 背景

有人提议「用 RocketMQ 来做」，方向是对的，但要先拆清楚本系统里有两类完全不同的「事件」：

| 类别 | 例子 | 访问模式 |
| --- | --- | --- |
| **会话事件流** | SSE 的 `route/tool/delta/done/error`，断线续传 | 按 `(run_id, seq)` **随机读**、任意游标、按 TTL 过期 |
| **旁路任务** | 记忆抽取、审计落库、文档解析/embedding、用量聚合 | 投递—消费—重试—死信，允许**延迟**，不要求随机读 |

把这两类塞进同一个组件，会得到一个两头都不称手的实现。

## 选项

| 选项 | 收益 | 代价 |
| --- | --- | --- |
| A. 全换 RocketMQ（含会话事件流） | 单一中间件 | 消费组是「分摊 + 位点」，不是按 `seq` 随机读；`QueryMessage` 按 key 查需轮询、无有序游标；续传语义要自己重建 |
| B. 事件流保持 Redis Stream；旁路任务抽象 `TaskQueue`，生产实现可插 RocketMQ | 各自用对工具；现有 Redis 已够；MQ 可替换 | 多一个抽象层；两种基础设施 |
| C. 事件流换 MySQL append-only 表；旁路任务用 RocketMQ | 事件可 SQL 查询/审计 | 高频写放大、需清理任务；SSE 延迟取决于轮询 |

## 决定

采用 **B**：

1. **会话事件流继续用 Redis Stream**（`XADD` + `XRANGE` 按 seq 取），理由是本系统唯一硬需求是「按 run 的连续游标回放 + 游标续传」，这是 Stream 的语义，不是队列的语义。
2. **新增 `TaskQueue` 抽象**（`publish(topic, key, payload)`），把「请求路径上的旁路工作」挪出去：记忆抽取、审计批量落库、后续的 RAG 索引。
3. **RocketMQ 作为 `TaskQueue` 的生产实现**，但**优先由 Java 侧承担**：`rocketmq-spring-boot-starter` 是官方一等公民；Python 侧 `rocketmq-client-python` 依赖 C++ SDK、社区 `roc` 为第三方，Windows 打包易踩坑。
4. **消息契约与现有幂等键对齐**：消息 key = `(user_id, idempotency_key)` 或 `run_id`，消费端以 `key` 去重（at-least-once → effectively-once）。

## 后果

**变好**：请求路径不再被记忆抽取的模型调用/MySQL 抖动拖慢；旁路任务可重试、可削峰、可换后端；事件流与业务解耦。

**变差**：多一层抽象；`TaskQueue` 一旦引入，消费者必须自己保证幂等（重复投递是常态不是异常）；RocketMQ 需要额外运维（NameServer + Broker + 磁盘）。

**不做的事**：不把 RocketMQ 用于「多副本 SSE 续传」——那需要随机读，队列做不到；也不引入事务消息，本场景没有跨库事务。

## 验证方式

- `TaskQueue` 契约测试：at-least-once 投递、重复 key 不重复落库、失败重试 3 次进死信、消费者异常不吞消息；
- 响应时间回归：`POST /agent/chat` 的 P95 不因旁路任务变慢（对照 e2e 冒烟延迟）；
- 现有 122 项测试 + 四个冒烟全绿；
- RocketMQ 实现单独用真实 broker 验证（本机当前无 broker，见计划文档第 0 节）。
