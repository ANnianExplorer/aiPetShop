-- v2.16 文档问答（RAG）：用户上传的资料 + 切片
-- 设计要点：
--   1. MySQL 8 没有向量类型，embedding 存 JSON 浮点数组，dim 用于识别换模型后的旧向量；
--   2. uk_user_sha 让同一用户重复上传同一文件复用，不重复解析与计费；
--   3. status 用状态机：0 queued / 1 parsing / 2 ready / 3 failed / 4 unsupported。

CREATE TABLE IF NOT EXISTS `doc_file`
(
    `id`          BIGINT       NOT NULL COMMENT '雪花 ID',
    `user_id`     BIGINT       NOT NULL COMMENT '归属用户',
    `pet_id`      BIGINT       NULL COMMENT '归属宠物（可空）',
    `name`        VARCHAR(255) NOT NULL COMMENT '原始文件名',
    `mime`        VARCHAR(128) NOT NULL DEFAULT '' COMMENT 'MIME',
    `size_bytes`  INT          NOT NULL DEFAULT 0 COMMENT '字节数',
    `sha256`      CHAR(64)     NOT NULL COMMENT '内容摘要，用于去重',
    `storage_key` VARCHAR(512) NOT NULL DEFAULT '' COMMENT '对象存储键',
    `status`      TINYINT      NOT NULL DEFAULT 0 COMMENT '0 queued 1 parsing 2 ready 3 failed 4 unsupported',
    `error`       VARCHAR(512) NULL COMMENT '失败原因',
    `chunk_count` INT          NOT NULL DEFAULT 0 COMMENT '切片数',
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_delete`   TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_sha` (`user_id`, `sha256`),
    KEY `idx_user_time` (`user_id`, `create_time`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT ='用户上传的文档';

CREATE TABLE IF NOT EXISTS `doc_chunk`
(
    `id`          BIGINT      NOT NULL COMMENT '雪花 ID',
    `file_id`     BIGINT      NOT NULL COMMENT '所属文档',
    `user_id`     BIGINT      NOT NULL COMMENT '冗余用户，检索强制按它过滤',
    `pet_id`      BIGINT      NULL COMMENT '冗余宠物',
    `chunk_index` INT         NOT NULL DEFAULT 0 COMMENT '块序号',
    `locator`     VARCHAR(64) NOT NULL DEFAULT '' COMMENT '页码/时间戳/偏移，供引用回跳',
    `content`     TEXT        NOT NULL COMMENT '块正文',
    `token_hint`  INT         NOT NULL DEFAULT 0 COMMENT '字符数，粗略 token 估算',
    `embedding`   MEDIUMTEXT  NULL COMMENT 'JSON 浮点数组',
    `dim`         INT         NOT NULL DEFAULT 0 COMMENT '向量维度',
    `create_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_file` (`file_id`),
    KEY `idx_user` (`user_id`, `pet_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT ='文档切片与向量';
