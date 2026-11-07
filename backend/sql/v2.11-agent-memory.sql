-- ============================================================
-- PetLumina v2.11 路 Pet-Agent 长期记忆表（P1）
-- 用法: mysql -u root -p < backend/sql/v2.11-agent-memory.sql
-- 前置: 已执行 backend/sql/v2.10-agent.sql
-- 约定与 init.sql 一致: BIGINT 雪花 ID(非自增) / utf8mb4_unicode_ci / is_delete 逻辑删除
-- ============================================================

USE `petlumina`;

-- ------------------------------------------------------------
-- 1. 事实记忆：一条 (user_id, pet_id, fact_key) 只允许一行
--    写入是 UPSERT：同一事实改值走 UPDATE，重复同一句话走 NOOP（见 app/memory/ops.py）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `memory_fact` (
    `id` BIGINT NOT NULL COMMENT '记忆ID(雪花)',
    `user_id` BIGINT NOT NULL COMMENT '所属用户ID',
    `pet_id` BIGINT NOT NULL DEFAULT 0 COMMENT '宠物ID；0=未指定宠物(唯一键里不能用 NULL)',
    `fact_key` VARCHAR(64) NOT NULL COMMENT '事实类型: pet_name/pet_age/pet_weight/allergy/food_avoid/food_like/vaccine',
    `fact_value` VARCHAR(255) NOT NULL COMMENT '事实值(已归一化的短文本)',
    `confidence` DECIMAL(3,2) NOT NULL DEFAULT 0.80 COMMENT '置信度 0~1，低于阈值不参与召回',
    `source` VARCHAR(32) NOT NULL DEFAULT 'conversation' COMMENT '来源: conversation/manual/import',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=有效 1=已删除',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_pet_key` (`user_id`, `pet_id`, `fact_key`),
    KEY `idx_user_update` (`user_id`, `pet_id`, `update_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent长期事实记忆';

-- ------------------------------------------------------------
-- 2. 情景记忆：一次值得记住的事件（不参与精确问答，用于"上次那件事"类回忆）
--    embedding_id 指向向量库中的向量，表本身不存向量，避免 MySQL 成为向量数据库
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `memory_episode` (
    `id` BIGINT NOT NULL COMMENT '情景ID(雪花)',
    `user_id` BIGINT NOT NULL COMMENT '所属用户ID',
    `pet_id` BIGINT NOT NULL DEFAULT 0 COMMENT '宠物ID；0=未指定',
    `session_id` BIGINT DEFAULT NULL COMMENT '来源会话ID',
    `summary` VARCHAR(512) NOT NULL COMMENT '一句话摘要(给模型读)',
    `detail` JSON DEFAULT NULL COMMENT '结构化细节: {key: value}',
    `occurred_at` DATETIME NOT NULL COMMENT '事件发生时间(不是入库时间)',
    `embedding_id` VARCHAR(64) DEFAULT NULL COMMENT '向量库中的ID(doc_id 或 pgvector 主键)',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_occurred` (`user_id`, `pet_id`, `occurred_at`),
    KEY `idx_session` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent长期情景记忆';
