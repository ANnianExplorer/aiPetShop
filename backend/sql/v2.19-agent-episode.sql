-- v2.19 情景记忆：memory_episode 补上事件类型与来源消息。
--
-- 背景：v2.11 建表时只留了 summary/detail/occurred_at/embedding_id，表一直没有写入方。
-- 本轮把「发生过的事」做成不依赖向量库的完整链路：
--   1. kind 让召回能按事件类型命中（洗澡/驱虫/疫苗……）；
--   2. source_message_id 记录写入它的那条用户消息，满足「召回要能追溯原消息」；
--   3. (user_id, source_message_id) 唯一，保证任务队列「至少一次」重复消费不会写出两条。
--
-- 注意：MySQL 8.0 不支持 ADD COLUMN IF NOT EXISTS，本脚本只需在 v2.11 之后执行一次。
-- 全新环境按 backend/sql 下的版本顺序执行即可。

ALTER TABLE memory_episode
    ADD COLUMN kind VARCHAR(32) NOT NULL DEFAULT '' COMMENT '事件类型：bath/deworm/vaccine/...' AFTER session_id,
    ADD COLUMN source_message_id BIGINT NULL COMMENT '写入这条往事的用户消息 id' AFTER kind,
    ADD UNIQUE KEY uk_source_message (user_id, source_message_id),
    ADD KEY idx_user_kind (user_id, pet_id, kind);
