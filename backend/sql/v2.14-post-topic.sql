-- E12：帖子与话题的关系从「tags 里的字符串约定」改成显式列
--
-- 旧实现：发帖时前端往 tags 里塞 "topic:<id>"，话题页用
--         `tags LIKE '"topic:<id>"'` 反查。任何一次 tags 清洗都会让关联静默丢失。
-- 新实现：post.topic_id 显式列 + 索引；tags 只负责展示。
--
-- 执行顺序：ALTER → 回填 → 清理 tags。三步都幂等，可重复执行。

ALTER TABLE `post`
    ADD COLUMN `topic_id` BIGINT DEFAULT NULL COMMENT '所属话题ID' AFTER `category`,
    ADD INDEX `idx_topic_id` (`topic_id`);

-- 回填：把 tags 里形如 "topic:123" 的元素解析成 topic_id
UPDATE `post` p
JOIN (
    SELECT p2.id AS post_id, CAST(SUBSTRING(t.tag, 7) AS UNSIGNED) AS topic_id
    FROM `post` p2
    JOIN JSON_TABLE(p2.tags, '$[*]' COLUMNS (tag VARCHAR(64) PATH '$')) AS t
    WHERE t.tag LIKE 'topic:%'
      AND t.tag REGEXP '^topic:[0-9]+$'
) m ON m.post_id = p.id
SET p.topic_id = m.topic_id
WHERE p.topic_id IS NULL;

-- 清理：tags 里不再保留 topic:*（展示层原本就会过滤掉，这里直接删干净）
UPDATE `post`
SET `tags` = JSON_REMOVE(`tags`, JSON_UNQUOTE(JSON_SEARCH(`tags`, 'one', 'topic:%', NULL, '$[*]')))
WHERE `tags` IS NOT NULL
  AND JSON_SEARCH(`tags`, 'one', 'topic:%', NULL, '$[*]') IS NOT NULL;
