package com.petlumina.backend.service.user.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.mapper.TopicFollowMapper;
import com.petlumina.backend.model.entity.TopicFollow;
import com.petlumina.backend.service.user.TopicFollowService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * 话题关注服务实现
 */
@Service
@Slf4j
public class TopicFollowServiceImpl extends ServiceImpl<TopicFollowMapper, TopicFollow>
        implements TopicFollowService {

    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public boolean toggleFollow(Long userId, Long topicId) {
        QueryWrapper<TopicFollow> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId);
        queryWrapper.eq("topic_id", topicId);

        TopicFollow existing = this.getOne(queryWrapper);
        if (existing != null) {
            this.removeById(existing.getId());
            return false;
        } else {
            TopicFollow follow = new TopicFollow();
            follow.setUserId(userId);
            follow.setTopicId(topicId);
            this.save(follow);
            return true;
        }
    }

    @Override
    public boolean isFollowed(Long userId, Long topicId) {
        QueryWrapper<TopicFollow> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId);
        queryWrapper.eq("topic_id", topicId);
        return this.count(queryWrapper) > 0;
    }
}
