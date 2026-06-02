package com.petlumina.backend.service.user;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.notification.NotificationQueryRequest;
import com.petlumina.backend.model.entity.Notification;
import com.petlumina.backend.model.entity.User;

/**
 * 通知服务接口
 */
public interface NotificationService extends IService<Notification> {

    /**
     * 构建查询条件
     */
    QueryWrapper<Notification> getQueryWrapper(NotificationQueryRequest request);

    /**
     * 获取未读通知数量
     */
    long getUnreadCount(User loginUser);

    /**
     * 标记单条通知为已读
     */
    boolean markAsRead(long id, User loginUser);

    /**
     * 标记所有通知为已读
     */
    boolean markAllAsRead(User loginUser);

    /**
     * 创建通知 (内部调用)
     */
    void createNotification(Long userId, String type, String title, String content, Long relatedId);
}
