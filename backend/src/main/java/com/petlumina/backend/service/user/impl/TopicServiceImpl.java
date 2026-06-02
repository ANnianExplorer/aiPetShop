package com.petlumina.backend.service.user.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.TopicMapper;
import com.petlumina.backend.model.dto.topic.TopicQueryRequest;
import com.petlumina.backend.model.entity.Topic;
import com.petlumina.backend.model.entity.TopicFollow;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.user.TopicFollowService;
import com.petlumina.backend.service.user.TopicService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;

/**
 * 话题服务实现
 */
@Service
@Slf4j
public class TopicServiceImpl extends ServiceImpl<TopicMapper, Topic>
        implements TopicService {

    @Resource
    private UserService userService;

    @Resource
    private TopicFollowService topicFollowService;

    @Override
    public QueryWrapper<Topic> getQueryWrapper(TopicQueryRequest request) {
        QueryWrapper<Topic> queryWrapper = new QueryWrapper<>();
        String category = request.getCategory();
        String searchText = request.getSearchText();

        queryWrapper.eq(StrUtil.isNotBlank(category), "category", category);
        if (StrUtil.isNotBlank(searchText)) {
            queryWrapper.and(w -> w
                    .like("title", searchText)
                    .or()
                    .like("description", searchText));
        }
        queryWrapper.orderByDesc("create_time");
        return queryWrapper;
    }

    @Override
    public long addTopic(Topic topic, User loginUser) {
        topic.setPostCount(0);
        topic.setFollowerCount(0);
        boolean saved = this.save(topic);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "创建话题失败");
        return topic.getId();
    }

    @Override
    public boolean deleteTopic(long id, User loginUser) {
        ThrowUtils.throwIf(!userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        Topic topic = this.getById(id);
        ThrowUtils.throwIf(topic == null, ErrorCode.NOT_FOUND_ERROR, "话题不存在");
        return this.removeById(id);
    }

    @Override
    public boolean editTopic(Topic topic, User loginUser) {
        ThrowUtils.throwIf(!userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        Topic existing = this.getById(topic.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR);
        return this.updateById(topic);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean toggleFollow(long topicId, User loginUser) {
        Topic topic = this.getById(topicId);
        ThrowUtils.throwIf(topic == null, ErrorCode.NOT_FOUND_ERROR, "话题不存在");

        boolean isFollowed = topicFollowService.toggleFollow(loginUser.getId(), topicId);
        // 更新话题关注数
        if (isFollowed) {
            this.lambdaUpdate()
                    .eq(Topic::getId, topicId)
                    .setSql("follower_count = follower_count + 1")
                    .update();
        } else {
            this.lambdaUpdate()
                    .eq(Topic::getId, topicId)
                    .setSql("follower_count = GREATEST(follower_count - 1, 0)")
                    .update();
        }
        return isFollowed;
    }
}
