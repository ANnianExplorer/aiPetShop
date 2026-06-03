use petlumina;
-- 通知表增加 status 字段（发布状态）
ALTER TABLE `notification` ADD COLUMN `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=草稿/未发布 1=已发布' AFTER `is_read`;

-- 通知表增加逻辑删除字段
ALTER TABLE `notification` ADD COLUMN `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除 1=已删除' AFTER `status`;

-- 添加索引
ALTER TABLE `notification` ADD INDEX `idx_status` (`status`);
