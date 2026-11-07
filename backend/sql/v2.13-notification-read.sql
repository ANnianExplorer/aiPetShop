-- v2.13 通知已读模型修正（BACKLOG E2）
--
-- 旧实现：广播（user_id = 0）被点开时给用户插一条"已读副本"，
--   1) 列表里会出现广播 + 副本两份，重复展示；
--   2) unread/count 只数 is_read = 0，广播那条永远数进去 → 红点永远消不掉；
--   3) read/all 也清不掉广播。
-- 新实现：用独立的已读表记录 (user_id, notification_id)，广播本身不再复制。

CREATE TABLE IF NOT EXISTS notification_read (
    id BIGINT NOT NULL COMMENT '主键',
    user_id BIGINT NOT NULL COMMENT '用户 id',
    notification_id BIGINT NOT NULL COMMENT '被读的通知/广播 id',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次已读时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_notification (user_id, notification_id),
    KEY idx_user (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '通知已读记录';

-- 把旧的"已读副本"迁移成正式已读记录，避免老用户红点回弹
INSERT IGNORE INTO notification_read (id, user_id, notification_id, create_time)
SELECT n.id, n.user_id, n.related_id, IFNULL(n.create_time, NOW())
FROM notification n
WHERE n.user_id <> 0
  AND n.related_id IS NOT NULL
  AND EXISTS (SELECT 1 FROM notification b WHERE b.id = n.related_id AND b.user_id = 0);

-- 迁移完成后删除副本，列表不再重复
-- 注意：MySQL 不允许 DELETE 的子查询直接引用同一张表，需再包一层派生表
DELETE FROM notification
WHERE user_id <> 0
  AND related_id IN (SELECT id FROM (SELECT id FROM notification WHERE user_id = 0) t);
