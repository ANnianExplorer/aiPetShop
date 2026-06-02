-- PetLumina 种子数据
-- 密码统一为 123456，BCrypt 加密

USE petlumina;

-- ==================== 用户数据 ====================

-- 管理员用户 (密码: 123456)
INSERT INTO `user` (`id`, `phone`, `email`, `password`, `nickname`, `avatar`, `bio`, `location`, `role`, `status`, `create_time`, `update_time`, `is_delete`)
VALUES
(1000000000000001, '13800000001', 'admin@petlumina.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '管理员', 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin', 'PetLumina 系统管理员', '北京', 'admin', 1, NOW(), NOW(), 0);

-- 普通用户 (密码: 123456)
INSERT INTO `user` (`id`, `phone`, `email`, `password`, `nickname`, `avatar`, `bio`, `location`, `role`, `status`, `create_time`, `update_time`, `is_delete`)
VALUES
(1000000000000002, '13800000002', 'zhangsan@petlumina.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '林间猫影', 'https://api.dicebear.com/7.x/avataaars/svg?seed=cat', '猫咪爱好者，家有两只布偶猫，喜欢分享养猫日常。', '北京', 'user', 1, NOW(), NOW(), 0);

INSERT INTO `user` (`id`, `phone`, `email`, `password`, `nickname`, `avatar`, `bio`, `location`, `role`, `status`, `create_time`, `update_time`, `is_delete`)
VALUES
(1000000000000003, '13800000003', 'lisi@petlumina.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '德牧小伍', 'https://api.dicebear.com/7.x/avataaars/svg?seed=dog', '德牧训练师，分享训犬心得与运动日常。', '上海', 'user', 1, NOW(), NOW(), 0);

INSERT INTO `user` (`id`, `phone`, `email`, `password`, `nickname`, `avatar`, `bio`, `location`, `role`, `status`, `create_time`, `update_time`, `is_delete`)
VALUES
(1000000000000004, '13800000004', 'wangwu@petlumina.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '兔兔爱好者', 'https://api.dicebear.com/7.x/avataaars/svg?seed=rabbit', '异宠达人，养了三只兔子和一只仓鼠。', '广州', 'user', 1, NOW(), NOW(), 0);

INSERT INTO `user` (`id`, `phone`, `email`, `password`, `nickname`, `avatar`, `bio`, `location`, `role`, `status`, `create_time`, `update_time`, `is_delete`)
VALUES
(1000000000000005, '13800000005', 'zhaoliu@petlumina.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '宠物营养师', 'https://api.dicebear.com/7.x/avataaars/svg?seed=vet', '专业宠物营养顾问，关注宠物健康饮食。', '深圳', 'user', 1, NOW(), NOW(), 0);

INSERT INTO `user` (`id`, `phone`, `email`, `password`, `nickname`, `avatar`, `bio`, `location`, `role`, `status`, `create_time`, `update_time`, `is_delete`)
VALUES
(1000000000000006, '13800000006', 'sunqi@petlumina.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '暖冬宠物', 'https://api.dicebear.com/7.x/avataaars/svg?seed=winter', '热爱冬天的铲屎官，分享宠物保暖小妙招。', '哈尔滨', 'user', 1, NOW(), NOW(), 0);

-- 禁用用户 (用于测试状态过滤)
INSERT INTO `user` (`id`, `phone`, `email`, `password`, `nickname`, `avatar`, `bio`, `location`, `role`, `status`, `create_time`, `update_time`, `is_delete`)
VALUES
(1000000000000007, '13800000007', 'disabled@petlumina.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '已禁用用户', 'https://api.dicebear.com/7.x/avataaars/svg?seed=disabled', '该账号已被禁用', '北京', 'user', 0, NOW(), NOW(), 0);


-- ==================== 宠物数据 ====================

-- 林间猫影 的宠物
INSERT INTO `pet` (`id`, `user_id`, `name`, `avatar`, `type`, `breed`, `age`, `health_score`, `today_steps`, `feeding_count`, `feeding_total`, `notes`, `create_time`, `update_time`, `is_delete`)
VALUES
(2000000000000001, 1000000000000002, '布丁', 'https://api.dicebear.com/7.x/croodles/svg?seed=cat1', 'cat', '布偶猫', '2岁', 95, 3200, 2, 3, '性格温顺，喜欢晒太阳', NOW(), NOW(), 0),
(2000000000000002, 1000000000000002, '奶茶', 'https://api.dicebear.com/7.x/croodles/svg?seed=cat2', 'cat', '英短蓝猫', '1岁半', 92, 2800, 2, 3, '活泼好动，爱玩逗猫棒', NOW(), NOW(), 0);

-- 德牧小伍 的宠物
INSERT INTO `pet` (`id`, `user_id`, `name`, `avatar`, `type`, `breed`, `age`, `health_score`, `today_steps`, `feeding_count`, `feeding_total`, `notes`, `create_time`, `update_time`, `is_delete`)
VALUES
(2000000000000003, 1000000000000003, '小伍', 'https://api.dicebear.com/7.x/croodles/svg?seed=dog1', 'dog', '德国牧羊犬', '3岁', 98, 8500, 3, 3, '训练有素的德牧，飞盘高手', NOW(), NOW(), 0);

-- 兔兔爱好者 的宠物
INSERT INTO `pet` (`id`, `user_id`, `name`, `avatar`, `type`, `breed`, `age`, `health_score`, `today_steps`, `feeding_count`, `feeding_total`, `notes`, `create_time`, `update_time`, `is_delete`)
VALUES
(2000000000000004, 1000000000000004, '团子', 'https://api.dicebear.com/7.x/croodles/svg?seed=rabbit1', 'other', '荷兰垂耳兔', '1岁', 88, 1500, 2, 2, '会自己用厕所的聪明兔子', NOW(), NOW(), 0);

-- 宠物营养师 的宠物
INSERT INTO `pet` (`id`, `user_id`, `name`, `avatar`, `type`, `breed`, `age`, `health_score`, `today_steps`, `feeding_count`, `feeding_total`, `notes`, `create_time`, `update_time`, `is_delete`)
VALUES
(2000000000000005, 1000000000000005, '豆豆', 'https://api.dicebear.com/7.x/croodles/svg?seed=dog2', 'dog', '金毛寻回犬', '4岁', 96, 6200, 2, 3, '温柔的大金毛', NOW(), NOW(), 0);

-- 暖冬宠物 的宠物
INSERT INTO `pet` (`id`, `user_id`, `name`, `avatar`, `type`, `breed`, `age`, `health_score`, `today_steps`, `feeding_count`, `feeding_total`, `notes`, `create_time`, `update_time`, `is_delete`)
VALUES
(2000000000000006, 1000000000000006, '雪球', 'https://api.dicebear.com/7.x/croodles/svg?seed=cat3', 'cat', '波斯猫', '3岁', 90, 2100, 2, 3, '怕冷的小公主', NOW(), NOW(), 0);


-- ==================== 话题数据 ====================

INSERT INTO `topic` (`id`, `title`, `description`, `image`, `category`, `post_count`, `follower_count`, `create_time`, `is_delete`)
VALUES
(3000000000000001, '冬季宠物保暖指南', '冬天来了，如何让你的宠物温暖过冬？本话题汇集了各种实用的保暖技巧和经验分享。', 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=400&h=300&fit=crop', '指南', 128, 2340, NOW(), 0),
(3000000000000002, '新手养猫必备清单', '第一次养猫不知道准备什么？这里有一份完整的养猫新手指南！', 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400&h=300&fit=crop', '指南', 256, 4520, NOW(), 0),
(3000000000000003, '宠物摄影大赛', '晒出你家毛孩子最萌最帅的照片，赢取精美奖品！', 'https://images.unsplash.com/photo-1530281700549-e82e7bf110d6?w=400&h=300&fit=crop', '活动', 89, 1890, NOW(), 0),
(3000000000000004, '春季宠物聚会报名中', '春暖花开，带着你的毛孩子来参加线下聚会吧！', 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=300&fit=crop', '社交', 45, 980, NOW(), 0),
(3000000000000005, '宠物健康饮食分享', '科学喂养，健康成长。分享宠物饮食搭配方案。', 'https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=400&h=300&fit=crop', '健康', 167, 3210, NOW(), 0);


-- ==================== 帖子数据 ====================

INSERT INTO `post` (`id`, `author_id`, `content`, `images`, `tags`, `category`, `likes`, `comments`, `create_time`, `update_time`, `is_delete`)
VALUES
(4000000000000001, 1000000000000002, '今天的阳光太好了，家里的主子已经在阳台晒了一整个下午。看着它慵懒的样子，感觉所有的疲惫都被治愈了。大家平时都给主子喂什么零食？', '["https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400&h=300&fit=crop"]', '["猫咪日常", "晒晒宠物"]', '猫咪', 1200, 86, NOW(), NOW(), 0),
(4000000000000002, 1000000000000003, '周末的飞盘训练，小伍表现得越来越稳了。这种高强度运动后的拉伸非常重要！今天训练了将近两个小时，接盘成功率已经达到了80%以上。', '["https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=300&fit=crop"]', '["训犬心得", "狗狗运动"]', '狗狗', 954, 42, NOW(), NOW(), 0),
(4000000000000003, 1000000000000004, '我家小兔子今天学会了新技能，会自己用厕所了！分享一下训练心得：首先要准备一个专用的兔子厕所，然后观察它经常上厕所的角落...', '["https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?w=400&h=300&fit=crop"]', '["异宠", "训练"]', '异宠', 567, 34, NOW(), NOW(), 0),
(4000000000000004, 1000000000000005, '分享一份科学的宠物饮食搭配方案，帮助毛孩子们健康成长。蛋白质、脂肪、碳水化合物的比例很重要，不同年龄段的需求也不同。', '["https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=400&h=300&fit=crop"]', '["健康", "饮食"]', '医疗健康', 2341, 156, NOW(), NOW(), 0),
(4000000000000005, 1000000000000006, '分享我家猫咪的冬季保暖神器——电热毯+小窝，主子舒服得不想出门了！冬天一定要注意给猫咪保暖，尤其是短毛猫。', '["https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400&h=300&fit=crop"]', '["保暖", "猫咪"]', '猫咪', 456, 32, NOW(), NOW(), 0),
(4000000000000006, 1000000000000002, '新买的猫爬架到了，两只主子抢着玩，太可爱了！布丁直接占领了最高层，奶茶只能在下面看着。', '["https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400&h=300&fit=crop"]', '["猫咪", "好物分享"]', '猫咪', 856, 42, DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY), 0);


-- ==================== 评论数据 ====================

INSERT INTO `comment` (`id`, `post_id`, `user_id`, `content`, `parent_id`, `likes`, `create_time`, `is_delete`)
VALUES
(5000000000000001, 4000000000000001, 1000000000000004, '太可爱了！我家猫也特别喜欢晒太阳', NULL, 12, NOW(), 0),
(5000000000000002, 4000000000000001, 1000000000000005, '冻干鸡肉是很好的零食，但要注意控制量哦', NULL, 8, NOW(), 0),
(5000000000000003, 4000000000000001, 1000000000000006, '推荐试试主食罐头，营养更均衡', NULL, 5, NOW(), 0),
(5000000000000004, 4000000000000002, 1000000000000002, '小伍太棒了！飞盘接得好帅', NULL, 15, NOW(), 0),
(5000000000000005, 4000000000000002, 1000000000000005, '运动后拉伸很重要，点赞！', NULL, 6, NOW(), 0);


-- ==================== 提醒数据 ====================

INSERT INTO `reminder` (`id`, `user_id`, `pet_id`, `title`, `type`, `remind_time`, `location`, `repeat_type`, `notes`, `is_completed`, `create_time`, `update_time`, `is_delete`)
VALUES
(6000000000000001, 1000000000000002, 2000000000000001, '年度疫苗接种', 'medical', DATE_ADD(NOW(), INTERVAL 1 DAY), '宠物医院', 'none', '带布丁去打年度疫苗', 0, NOW(), NOW(), 0),
(6000000000000002, 1000000000000002, 2000000000000001, '定期体内驱虫', 'daily', NOW(), '在家', 'monthly', '每月一次驱虫', 0, NOW(), NOW(), 0),
(6000000000000003, 1000000000000002, 2000000000000002, '户外散步', 'activity', DATE_ADD(NOW(), INTERVAL 2 HOUR), '小区公园', 'daily', '每天散步30分钟', 1, NOW(), NOW(), 0),
(6000000000000004, 1000000000000003, 2000000000000003, '飞盘训练', 'activity', DATE_ADD(NOW(), INTERVAL 3 HOUR), '公园草地', 'weekly', '每周三次训练', 0, NOW(), NOW(), 0),
(6000000000000005, 1000000000000003, 2000000000000003, '洗澡美容', 'daily', DATE_ADD(NOW(), INTERVAL 2 DAY), '宠物美容店', 'none', NULL, 0, NOW(), NOW(), 0);


-- ==================== 健康记录数据 ====================

INSERT INTO `health_record` (`id`, `pet_id`, `date`, `heart_rate`, `sleep_hours`, `steps`, `calories`, `exercise`, `weight`, `water_intake`, `mood`, `create_time`)
VALUES
(7000000000000001, 2000000000000001, CURDATE(), 78, 10.5, 3200, 280, 25, 4.50, 350, 'happy', NOW()),
(7000000000000002, 2000000000000001, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 82, 9.8, 2800, 240, 20, 4.48, 320, 'normal', DATE_SUB(NOW(), INTERVAL 1 DAY)),
(7000000000000003, 2000000000000003, CURDATE(), 72, 8.5, 8500, 520, 55, 32.00, 600, 'active', NOW()),
(7000000000000004, 2000000000000003, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 75, 9.0, 7800, 480, 50, 31.80, 550, 'happy', DATE_SUB(NOW(), INTERVAL 1 DAY));


-- ==================== 通知数据 ====================

INSERT INTO `notification` (`id`, `user_id`, `type`, `title`, `content`, `is_read`, `related_id`, `create_time`)
VALUES
(8000000000000001, 1000000000000002, 'reminder', '疫苗接种提醒', '您的宠物布丁年度疫苗接种将在明天进行，请准时到达宠物医院。', 0, 6000000000000001, NOW()),
(8000000000000002, 1000000000000002, 'social', '社区互动', '德牧小伍 点赞了您的帖子', 0, 4000000000000001, DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(8000000000000003, 1000000000000002, 'health', '健康报告', '您宠物的周健康报告已生成，健康评分95分，状态优秀！', 1, NULL, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(8000000000000004, 1000000000000002, 'system', '系统通知', 'PetLumina 已更新至最新版本，新增多项实用功能。', 1, NULL, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(8000000000000005, 1000000000000003, 'social', '社区互动', '林间猫影 评论了您的帖子："小伍太棒了！"', 0, 4000000000000002, DATE_SUB(NOW(), INTERVAL 30 MINUTE));
