package com.petlumina.backend.service.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.NotificationMapper;
import com.petlumina.backend.model.dto.notification.NotificationQueryRequest;
import com.petlumina.backend.model.entity.Notification;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.NotificationService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * 通知服务实现
 */
@Service
@Slf4j
public class NotificationServiceImpl extends ServiceImpl<NotificationMapper, Notification>
        implements NotificationService {

    @Override
    public QueryWrapper<Notification> getQueryWrapper(NotificationQueryRequest request) {
        QueryWrapper<Notification> queryWrapper = new QueryWrapper<>();
        String type = request.getType();
        Integer isRead = request.getIsRead();

        queryWrapper.eq(StrUtil.isNotBlank(type), "type", type);
        queryWrapper.eq(isRead != null, "is_read", isRead);
        queryWrapper.orderByDesc("create_time");
        return queryWrapper;
    }

    @Override
    public long getUnreadCount(User loginUser) {
        QueryWrapper<Notification> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", loginUser.getId());
        queryWrapper.eq("is_read", 0);
        return this.count(queryWrapper);
    }

    @Override
    public boolean markAsRead(long id, User loginUser) {
        Notification notification = this.getById(id);
        ThrowUtils.throwIf(notification == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!notification.getUserId().equals(loginUser.getId()), ErrorCode.NO_AUTH_ERROR);

        notification.setIsRead(1);
        return this.updateById(notification);
    }

    @Override
    public boolean markAllAsRead(User loginUser) {
        UpdateWrapper<Notification> updateWrapper = new UpdateWrapper<>();
        updateWrapper.eq("user_id", loginUser.getId());
        updateWrapper.eq("is_read", 0);
        updateWrapper.set("is_read", 1);
        return this.update(updateWrapper);
    }

    @Override
    public void createNotification(Long userId, String type, String title, String content, Long relatedId) {
        Notification notification = new Notification();
        notification.setUserId(userId);
        notification.setType(type);
        notification.setTitle(title);
        notification.setContent(content);
        notification.setIsRead(0);
        notification.setRelatedId(relatedId);
        this.save(notification);
        log.debug("创建通知: userId={}, type={}, title={}", userId, type, title);
    }
}
