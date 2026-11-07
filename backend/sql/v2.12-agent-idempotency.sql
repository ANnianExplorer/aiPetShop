-- ============================================================
-- PetLumina v2.12 · Agent 幂等键（S1.8 P2）
-- 用法: mysql -u root -p < backend/sql/v2.12-agent-idempotency.sql
-- 前置: 已执行 backend/sql/v2.10-agent.sql
-- 目的: 客户端重试同一条消息（网络抖动、用户狂点）时，不重复调用模型、不重复计费。
-- 唯一键放在库层，Python 侧先查后写只是"快路径"，并发仍由这个键兜底。
--
-- 为什么唯一键是 (user_id, idempotency_key) 而不是 (session_id, ...)：
-- 首次请求如果失败在「会话还没建出来」之前，客户端拿不到 session_id，
-- 重试时只能重发同一条消息；此时若按 session 去重，会新建会话再执行一遍。
-- 用户维度去重才能覆盖「第一次就失败」的场景。
-- ============================================================

USE `petlumina`;

ALTER TABLE `agent_run`
    ADD COLUMN `user_id` BIGINT NOT NULL DEFAULT 0 COMMENT '会话所属用户(冗余,用于幂等键)' AFTER `session_id`,
    ADD COLUMN `idempotency_key` VARCHAR(64) DEFAULT NULL COMMENT '幂等键(客户端生成,同一用户内唯一)' AFTER `model`,
    ADD UNIQUE KEY `uk_idem` (`user_id`, `idempotency_key`),
    ADD KEY `idx_user_time` (`user_id`, `create_time`);
