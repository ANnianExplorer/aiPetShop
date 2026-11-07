package com.petlumina.backend.service.user.impl;

import cn.hutool.core.collection.CollUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.mapper.NotificationMapper;
import com.petlumina.backend.mapper.NotificationReadMapper;
import com.petlumina.backend.model.entity.Notification;
import com.petlumina.backend.model.entity.NotificationRead;
import com.petlumina.backend.service.user.NotificationReadService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 通知已读实现。
 */
@Service
@Slf4j
public class NotificationReadServiceImpl extends ServiceImpl<NotificationReadMapper, NotificationRead>
        implements NotificationReadService {

    @Resource
    private NotificationMapper notificationMapper;

    @Override
    public Set<Long> readNotificationIds(long userId, Collection<Long> notificationIds) {
        if (CollUtil.isEmpty(notificationIds)) {
            return Collections.emptySet();
        }
        QueryWrapper<NotificationRead> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.in("notification_id", notificationIds);
        return this.list(wrapper).stream()
                .map(NotificationRead::getNotificationId)
                .collect(Collectors.toSet());
    }

    @Override
    public boolean markRead(long userId, long notificationId) {
        QueryWrapper<NotificationRead> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.eq("notification_id", notificationId);
        if (this.count(wrapper) > 0) {
            return true;
        }
        try {
            NotificationRead record = new NotificationRead();
            record.setUserId(userId);
            record.setNotificationId(notificationId);
            this.save(record);
            return true;
        } catch (DuplicateKeyException e) {
            // 并发重复点开：唯一键兜底，视为成功
            return true;
        }
    }

    @Override
    public int markAllBroadcastsRead(long userId) {
        QueryWrapper<Notification> broadcastWrapper = new QueryWrapper<>();
        broadcastWrapper.eq("user_id", 0);
        broadcastWrapper.eq("status", 1);
        List<Long> broadcastIds = notificationMapper.selectList(broadcastWrapper).stream()
                .map(Notification::getId)
                .collect(Collectors.toList());
        if (broadcastIds.isEmpty()) {
            return 0;
        }
        Set<Long> alreadyRead = new HashSet<>(this.readNotificationIds(userId, broadcastIds));
        List<NotificationRead> rows = new ArrayList<>();
        for (Long id : broadcastIds) {
            if (alreadyRead.contains(id)) {
                continue;
            }
            NotificationRead record = new NotificationRead();
            record.setUserId(userId);
            record.setNotificationId(id);
            rows.add(record);
        }
        if (rows.isEmpty()) {
            return 0;
        }
        this.saveBatch(rows);
        log.info("批量标记广播已读: userId={}, count={}", userId, rows.size());
        return rows.size();
    }
}
