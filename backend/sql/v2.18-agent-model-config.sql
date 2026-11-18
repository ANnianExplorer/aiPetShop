-- S1.33 管理员统一模型配置（BACKLOG C10）
-- 单行配置：id 固定为 1；api_key_cipher 只存密文，主密钥在 Agent 进程侧。
-- 未配置或 enabled=0 时，Agent 回退 PET_AGENT_LLM_* 环境变量。

CREATE TABLE IF NOT EXISTS `agent_model_config` (
  `id` TINYINT NOT NULL COMMENT '固定为 1，单例配置',
  `provider` VARCHAR(32) NOT NULL COMMENT '提供方标识，如 deepseek/openai',
  `base_url` VARCHAR(255) NOT NULL COMMENT 'OpenAI 兼容接口根路径',
  `model` VARCHAR(128) NOT NULL COMMENT '模型 ID',
  `api_key_cipher` TEXT NOT NULL COMMENT 'API Key 密文（v1:...）',
  `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用数据库配置',
  `updated_by` VARCHAR(64) NULL COMMENT '最后修改的管理员 ID',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后修改时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员统一模型配置（单例）';
