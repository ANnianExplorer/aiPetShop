-- ============================================================
-- PetLumina v2.10 · Pet-Agent 会话与运行轨迹表（S1）
-- 用法: mysql -u root -p < backend/sql/v2.10-agent.sql
-- 约定与 init.sql 一致: BIGINT 雪花 ID(非自增) / utf8mb4_unicode_ci / is_delete 逻辑删除
-- ============================================================

CREATE DATABASE IF NOT EXISTS `petlumina` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `petlumina`;

-- ------------------------------------------------------------
-- 1. 会话：一个用户在一个通道上与 Agent 的一段连续对话
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agent_session` (
    `id` BIGINT NOT NULL COMMENT '会话ID(雪花)',
    `user_id` BIGINT NOT NULL COMMENT '所属用户ID',
    `pet_id` BIGINT DEFAULT NULL COMMENT '对话聚焦的宠物ID(可空=未指定)',
    `title` VARCHAR(128) NOT NULL DEFAULT '新对话' COMMENT '会话标题',
    `channel` VARCHAR(16) NOT NULL DEFAULT 'app' COMMENT '通道: app/admin/desktop',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1=活跃 0=归档',
    `message_count` INT NOT NULL DEFAULT 0 COMMENT '消息条数(冗余,便于列表排序)',
    `total_tokens` BIGINT NOT NULL DEFAULT 0 COMMENT '累计token(计费口径)',
    `last_message_time` DATETIME DEFAULT NULL COMMENT '最后一条消息时间',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除 1=已删除',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_last` (`user_id`, `last_message_time`),
    KEY `idx_pet` (`pet_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent会话表';

-- ------------------------------------------------------------
-- 2. 消息：用户/助手/工具结果，业务真源(不依赖 harness 的 checkpointer)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agent_message` (
    `id` BIGINT NOT NULL COMMENT '消息ID(雪花)',
    `session_id` BIGINT NOT NULL COMMENT '会话ID',
    `run_id` BIGINT DEFAULT NULL COMMENT '所属运行ID(用户消息为空)',
    `role` VARCHAR(16) NOT NULL COMMENT '角色: user/assistant/system/tool',
    `content` MEDIUMTEXT NOT NULL COMMENT '消息正文(markdown)',
    `content_type` VARCHAR(16) NOT NULL DEFAULT 'text' COMMENT '类型: text/markdown/card',
    `tokens` INT NOT NULL DEFAULT 0 COMMENT '该消息消耗token',
    `citations` JSON DEFAULT NULL COMMENT '引用: [{"kind":"doc|record","id":"...","label":"...","locator":"page=3|t=93s"}]',
    `meta` JSON DEFAULT NULL COMMENT '扩展: route/tool_name/latency_ms 等',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_session_time` (`session_id`, `create_time`),
    KEY `idx_run` (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent消息表';

-- ------------------------------------------------------------
-- 3. 运行：一次用户提问触发的完整执行（可回放、可计费）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agent_run` (
    `id` BIGINT NOT NULL COMMENT '运行ID(雪花)',
    `session_id` BIGINT NOT NULL COMMENT '会话ID',
    `user_message_id` BIGINT DEFAULT NULL COMMENT '触发该运行的用户消息ID',
    `intent` VARCHAR(64) DEFAULT NULL COMMENT '识别到的意图(health/log/reminder/chat...)',
    `route` VARCHAR(8) NOT NULL DEFAULT 'L1' COMMENT '调度层级: L1直答/L2 ReAct/L3 Plan',
    `status` VARCHAR(16) NOT NULL DEFAULT 'running' COMMENT '状态: running/succeeded/failed/interrupted',
    `model` VARCHAR(64) DEFAULT NULL COMMENT '使用的模型',
    `prompt_tokens` INT NOT NULL DEFAULT 0 COMMENT '输入token',
    `completion_tokens` INT NOT NULL DEFAULT 0 COMMENT '输出token',
    `latency_ms` INT NOT NULL DEFAULT 0 COMMENT '端到端耗时',
    `error` VARCHAR(512) DEFAULT NULL COMMENT '失败原因',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_session_time` (`session_id`, `create_time`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent运行表';

-- ------------------------------------------------------------
-- 4. 步骤：运行内部的每一次 LLM 调用 / 工具调用 / 检索（管理端回放的最小单元）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `agent_step` (
    `id` BIGINT NOT NULL COMMENT '步骤ID(雪花)',
    `run_id` BIGINT NOT NULL COMMENT '运行ID',
    `seq` INT NOT NULL COMMENT '步骤序号(从1开始)',
    `kind` VARCHAR(16) NOT NULL COMMENT '类型: llm/tool/retrieve/reflect',
    `name` VARCHAR(64) DEFAULT NULL COMMENT '名称(工具名/节点名)',
    `input` JSON DEFAULT NULL COMMENT '入参(已脱敏)',
    `output_digest` VARCHAR(512) DEFAULT NULL COMMENT '出参摘要(前512字符,避免大字段)',
    `status` VARCHAR(16) NOT NULL DEFAULT 'ok' COMMENT '状态: ok/error/skipped',
    `latency_ms` INT NOT NULL DEFAULT 0 COMMENT '耗时',
    `error` VARCHAR(512) DEFAULT NULL COMMENT '错误信息',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_run_seq` (`run_id`, `seq`),
    KEY `idx_kind` (`kind`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent步骤表';

-- ------------------------------------------------------------
-- 5. 工具审计：谁在什么运行里调了什么工具、成没成功（只存入参摘要，不留原文）
--    与 agent_step 的区别：step 是回放用的轨迹，审计表是安全/成本核查用的流水，
--    二者生命周期不同（step 可归档，审计需按合规要求长期保留）。
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tool_call_log` (
    `id` BIGINT NOT NULL COMMENT '审计记录ID(雪花)',
    `run_id` BIGINT NOT NULL COMMENT '运行ID',
    `tool_name` VARCHAR(64) NOT NULL COMMENT '工具名',
    `args_digest` VARCHAR(64) NOT NULL COMMENT '入参摘要(sha256 前16位,不存原文,防敏感信息落库)',
    `ok` TINYINT NOT NULL DEFAULT 1 COMMENT '是否成功: 1=成功 0=失败',
    `error_code` VARCHAR(64) DEFAULT NULL COMMENT '失败错误码(如 invalid_arguments/backend_error)',
    `latency_ms` INT NOT NULL DEFAULT 0 COMMENT '工具耗时',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_run` (`run_id`),
    KEY `idx_tool_time` (`tool_name`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent工具调用审计表';
