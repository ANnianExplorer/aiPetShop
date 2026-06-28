-- PetLumina 数据库初始化脚本
-- 数据库: petlumina

CREATE DATABASE IF NOT EXISTS petlumina DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE petlumina;

-- 用户表
CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
    `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `password` VARCHAR(100) NOT NULL COMMENT '密码(BCrypt)',
    `nickname` VARCHAR(50) DEFAULT NULL COMMENT '昵称',
    `avatar` VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
    `bio` VARCHAR(500) DEFAULT NULL COMMENT '个人简介',
    `location` VARCHAR(100) DEFAULT NULL COMMENT '所在地',
    `role` VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色: user/admin',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用 1=正常',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除 1=已删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_phone` (`phone`),
    UNIQUE KEY `uk_email` (`email`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 宠物表
CREATE TABLE IF NOT EXISTS `pet` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '所属用户ID',
    `name` VARCHAR(50) NOT NULL COMMENT '宠物名称',
    `avatar` VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
    `type` VARCHAR(10) NOT NULL COMMENT '类型: dog/cat/other',
    `breed` VARCHAR(50) DEFAULT NULL COMMENT '品种',
    `age` VARCHAR(20) DEFAULT NULL COMMENT '年龄',
    `health_score` INT DEFAULT 100 COMMENT '健康评分',
    `today_steps` INT DEFAULT 0 COMMENT '今日步数',
    `feeding_count` INT DEFAULT 0 COMMENT '已喂食次数',
    `feeding_total` INT DEFAULT 0 COMMENT '计划喂食次数',
    `notes` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='宠物表';

-- 健康记录表
CREATE TABLE IF NOT EXISTS `health_record` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `pet_id` BIGINT NOT NULL COMMENT '关联宠物ID',
    `date` DATE NOT NULL COMMENT '记录日期',
    `heart_rate` INT DEFAULT NULL COMMENT '心率(bpm)',
    `sleep_hours` DECIMAL(4,1) DEFAULT NULL COMMENT '睡眠时长(小时)',
    `steps` INT DEFAULT NULL COMMENT '步数',
    `calories` INT DEFAULT NULL COMMENT '卡路里消耗',
    `exercise` INT DEFAULT NULL COMMENT '运动时长(分钟)',
    `weight` DECIMAL(5,2) DEFAULT NULL COMMENT '体重(kg)',
    `water_intake` INT DEFAULT NULL COMMENT '饮水量(ml)',
    `mood` VARCHAR(10) DEFAULT NULL COMMENT '心情: happy/normal/tired/active',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_pet_id` (`pet_id`),
    KEY `idx_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康记录表';

-- 健康计划表
CREATE TABLE IF NOT EXISTS `health_plan` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `pet_id` BIGINT NOT NULL COMMENT '关联宠物ID',
    `type` VARCHAR(20) NOT NULL COMMENT '计划类型: feeding/exercise/medical/grooming/training',
    `title` VARCHAR(100) NOT NULL COMMENT '计划标题',
    `time` VARCHAR(10) DEFAULT NULL COMMENT '执行时间',
    `frequency` VARCHAR(10) NOT NULL DEFAULT 'daily' COMMENT '频率: daily/weekly/monthly',
    `standard` VARCHAR(20) DEFAULT NULL COMMENT '完成标准类型',
    `standard_value` INT DEFAULT NULL COMMENT '目标值',
    `notes` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `is_active` TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用: 0=停用 1=启用',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    PRIMARY KEY (`id`),
    KEY `idx_pet_id` (`pet_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康计划表';

-- 生活记录表
CREATE TABLE IF NOT EXISTS `log_entry` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '发布者ID',
    `pet_id` BIGINT DEFAULT NULL COMMENT '关联宠物ID',
    `type` VARCHAR(20) NOT NULL COMMENT '记录类型: feeding/walking/grooming/medical/other',
    `title` VARCHAR(100) NOT NULL COMMENT '标题',
    `content` TEXT COMMENT '内容描述',
    `images` JSON COMMENT '图片URL列表',
    `tags` JSON COMMENT '标签列表',
    `likes` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_pet_id` (`pet_id`),
    KEY `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生活记录表';

-- 社区帖子表
CREATE TABLE IF NOT EXISTS `post` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `author_id` BIGINT NOT NULL COMMENT '作者ID',
    `content` TEXT NOT NULL COMMENT '帖子内容',
    `images` JSON COMMENT '图片列表',
    `tags` JSON COMMENT '标签',
    `category` VARCHAR(20) DEFAULT NULL COMMENT '分类: 猫咪/狗狗/异宠/医疗健康',
    `likes` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    `comments` INT NOT NULL DEFAULT 0 COMMENT '评论数',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    PRIMARY KEY (`id`),
    KEY `idx_author_id` (`author_id`),
    KEY `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区帖子表';

-- 话题表
CREATE TABLE IF NOT EXISTS `topic` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `title` VARCHAR(100) NOT NULL COMMENT '话题标题',
    `description` TEXT COMMENT '话题描述',
    `image` VARCHAR(500) DEFAULT NULL COMMENT '封面图',
    `category` VARCHAR(20) DEFAULT NULL COMMENT '分类',
    `post_count` INT NOT NULL DEFAULT 0 COMMENT '帖子数量',
    `follower_count` INT NOT NULL DEFAULT 0 COMMENT '关注数',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='话题表';

-- 评论表
CREATE TABLE IF NOT EXISTS `comment` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `post_id` BIGINT NOT NULL COMMENT '所属帖子ID',
    `user_id` BIGINT NOT NULL COMMENT '评论者ID',
    `content` TEXT NOT NULL COMMENT '评论内容',
    `parent_id` BIGINT DEFAULT NULL COMMENT '父评论ID(NULL=顶级评论)',
    `likes` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    PRIMARY KEY (`id`),
    KEY `idx_post_id` (`post_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_parent_id` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';

-- 提醒表
CREATE TABLE IF NOT EXISTS `reminder` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '所属用户ID',
    `pet_id` BIGINT DEFAULT NULL COMMENT '关联宠物ID',
    `title` VARCHAR(100) NOT NULL COMMENT '提醒标题',
    `type` VARCHAR(20) NOT NULL COMMENT '类型: medical/daily/activity',
    `remind_time` DATETIME DEFAULT NULL COMMENT '提醒时间',
    `location` VARCHAR(100) DEFAULT NULL COMMENT '地点',
    `repeat_type` VARCHAR(10) NOT NULL DEFAULT 'none' COMMENT '重复类型: none/daily/weekly/monthly',
    `notes` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `is_completed` TINYINT NOT NULL DEFAULT 0 COMMENT '是否完成: 0=未完成 1=已完成',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_pet_id` (`pet_id`),
    KEY `idx_remind_time` (`remind_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提醒表';

-- 通知表
CREATE TABLE IF NOT EXISTS `notification` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '接收用户ID (0=系统广播)',
    `type` VARCHAR(20) NOT NULL COMMENT '通知类型: reminder/social/health/system',
    `title` VARCHAR(100) NOT NULL COMMENT '通知标题',
    `content` TEXT COMMENT '通知内容',
    `is_read` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已读: 0=未读 1=已读',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=草稿/未发布 1=已发布',
    `is_delete` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=未删除 1=已删除',
    `related_id` BIGINT DEFAULT NULL COMMENT '关联业务ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_is_read` (`is_read`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';

-- 关注关系表
CREATE TABLE IF NOT EXISTS `user_follow` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '关注者ID',
    `follow_user_id` BIGINT NOT NULL COMMENT '被关注者ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_follow` (`user_id`, `follow_user_id`),
    KEY `idx_follow_user_id` (`follow_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关注关系表';

-- 点赞记录表
CREATE TABLE IF NOT EXISTS `like_record` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `target_id` BIGINT NOT NULL COMMENT '目标ID',
    `target_type` VARCHAR(10) NOT NULL COMMENT '目标类型: post/log',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_target` (`user_id`, `target_id`, `target_type`),
    KEY `idx_target` (`target_id`, `target_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='点赞记录表';

-- 收藏记录表
CREATE TABLE IF NOT EXISTS `favorite_record` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `target_id` BIGINT NOT NULL COMMENT '目标ID',
    `target_type` VARCHAR(10) NOT NULL COMMENT '目标类型: post/log',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_target` (`user_id`, `target_id`, `target_type`),
    KEY `idx_target` (`target_id`, `target_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收藏记录表';

-- 话题关注表
CREATE TABLE IF NOT EXISTS `topic_follow` (
    `id` BIGINT NOT NULL COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `topic_id` BIGINT NOT NULL COMMENT '话题ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_topic` (`user_id`, `topic_id`),
    KEY `idx_topic_id` (`topic_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='话题关注表';
