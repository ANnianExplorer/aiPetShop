-- S1.18 宠物画像（BACKLOG C2）
-- 追加式快照：不覆盖历史，保留最近 N 版，便于管理端 diff 与审计。

CREATE TABLE IF NOT EXISTS `profile_snapshot` (
  `id` BIGINT NOT NULL COMMENT '雪花 ID',
  `user_id` BIGINT NOT NULL COMMENT '用户 ID',
  `pet_id` BIGINT NOT NULL DEFAULT 0 COMMENT '宠物 ID，0 表示不区分宠物',
  `version` INT NOT NULL COMMENT '同一 (user, pet) 内自增，从 1 开始',
  `data` MEDIUMTEXT NOT NULL COMMENT '画像 JSON（basics/traits/preferences/riskFlags/careGaps/evidence）',
  `fact_count` INT NOT NULL DEFAULT 0 COMMENT '生成本版时用到的事实条数',
  `confidence` DECIMAL(3,2) NOT NULL DEFAULT 0.00 COMMENT '所用事实的加权均值',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_pet_version` (`user_id`, `pet_id`, `version`),
  KEY `idx_latest` (`user_id`, `pet_id`, `version` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='宠物画像快照（追加式）';
