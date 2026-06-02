package com.petlumina.backend.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.entity.TopicFollow;

/**
 * 话题关注服务接口
 */
public interface TopicFollowService extends IService<TopicFollow> {

    /**
     * 切换话题关注状态
     *
     * @return true=已关注, false=已取消关注
     */
    boolean toggleFollow(Long userId, Long topicId);

    /**
     * 查询是否关注了话题
     */
    boolean isFollowed(Long userId, Long topicId);
}
