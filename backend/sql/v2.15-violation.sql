-- v2.15 违规管理（BACKLOG E9）
--
-- 敏感词库 + 违规记录。发帖/评论命中敏感词时：
--   1) sensitive_word.hit_count + 1
--   2) 写一条 violation_record（status = 0 待处理）
--   3) 拒绝本次请求
--
-- 幂等：建表用 CREATE TABLE IF NOT EXISTS，种子词用 INSERT IGNORE（uk_word 去重）。

CREATE TABLE IF NOT EXISTS sensitive_word (
    id BIGINT NOT NULL COMMENT '主键',
    word VARCHAR(64) NOT NULL COMMENT '敏感词',
    category VARCHAR(20) DEFAULT NULL COMMENT '分类：spam/fraud/violent/other',
    level VARCHAR(20) DEFAULT NULL COMMENT '风险等级：critical/high/medium/low',
    hit_count INT DEFAULT 0 COMMENT '命中次数',
    status TINYINT DEFAULT 1 COMMENT '状态：1 启用，0 禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_delete TINYINT DEFAULT 0 COMMENT '逻辑删除：0 正常，1 已删除',
    PRIMARY KEY (id),
    UNIQUE KEY uk_word (word)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '敏感词库';

CREATE TABLE IF NOT EXISTS violation_record (
    id BIGINT NOT NULL COMMENT '主键',
    target_type VARCHAR(20) DEFAULT NULL COMMENT '目标类型：post/comment',
    target_id BIGINT DEFAULT NULL COMMENT '目标 id（创建时被拦截则为空）',
    content_snapshot VARCHAR(500) DEFAULT NULL COMMENT '违规内容快照（截断 500）',
    author_id BIGINT DEFAULT NULL COMMENT '发布者用户 id',
    reason VARCHAR(100) DEFAULT NULL COMMENT '违规原因',
    word VARCHAR(64) DEFAULT NULL COMMENT '命中的敏感词',
    status TINYINT DEFAULT 0 COMMENT '状态：0 待处理，1 已处理',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_delete TINYINT DEFAULT 0 COMMENT '逻辑删除：0 正常，1 已删除',
    PRIMARY KEY (id),
    KEY idx_status_time (status, create_time),
    KEY idx_author (author_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '违规记录';

-- 种子敏感词（INSERT IGNORE：重复执行不会报错，也不会重复插入）
INSERT IGNORE INTO sensitive_word (id, word, category, level, hit_count, status) VALUES
    (1, '广告引流', 'spam', 'high', 0, 1),
    (2, '加微信', 'spam', 'high', 0, 1),
    (3, '免费领养', 'fraud', 'medium', 0, 1),
    (4, '低价转让', 'fraud', 'medium', 0, 1),
    (5, '虐待', 'violent', 'critical', 0, 1),
    (6, '毒杀', 'violent', 'critical', 0, 1);
