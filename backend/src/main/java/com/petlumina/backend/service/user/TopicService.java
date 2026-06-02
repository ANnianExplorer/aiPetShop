package com.petlumina.backend.service.user;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.topic.TopicQueryRequest;
import com.petlumina.backend.model.entity.Topic;
import com.petlumina.backend.model.entity.User;

/**
 * 话题服务接口
 */
public interface TopicService extends IService<Topic> {

    /**
     * 构建查询条件
     */
    QueryWrapper<Topic> getQueryWrapper(TopicQueryRequest request);

    /**
     * 添加话题
     */
    long addTopic(Topic topic, User loginUser);

    /**
     * 删除话题 (管理员)
     */
    boolean deleteTopic(long id, User loginUser);

    /**
     * 编辑话题 (管理员)
     */
    boolean editTopic(Topic topic, User loginUser);

    /**
     * 切换话题关注状态
     *
     * @return true=已关注, false=已取消关注
     */
    boolean toggleFollow(long topicId, User loginUser);
}
