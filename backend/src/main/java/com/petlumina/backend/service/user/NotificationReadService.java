package com.petlumina.backend.service.user;

import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.entity.NotificationRead;

import java.util.Collection;
import java.util.Set;

/**
 * 通知已读服务：广播通知的"谁读过"由本表承担，不再复制通知行。
 */
public interface NotificationReadService extends IService<NotificationRead> {

    /**
     * 查询这批通知里当前用户已读过的 id 集合。
     *
     * @param userId         用户 id
     * @param notificationIds 待检查的通知 id（可为空集合）
     * @return 已读 id 集合，永不返回 null
     */
    Set<Long> readNotificationIds(long userId, Collection<Long> notificationIds);

    /**
     * 标记一条通知为已读（幂等：重复调用不会报错也不会多写）。
     *
     * @return true 表示标记成功或此前已标记
     */
    boolean markRead(long userId, long notificationId);

    /**
     * 把当前时间点所有已发布广播标记为该用户已读。
     *
     * @return 新增的已读记录数
     */
    int markAllBroadcastsRead(long userId);
}
