package com.petlumina.backend.controller.user;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.notification.NotificationQueryRequest;
import com.petlumina.backend.model.entity.Notification;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.NotificationVO;
import com.petlumina.backend.service.user.NotificationReadService;
import com.petlumina.backend.service.user.NotificationService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 通知控制器
 *
 * <p>广播通知（{@code user_id = 0}）的已读状态由 {@code notification_read} 表记录，
 * 列表与未读数都按"广播是否被该用户读过"计算，不再插副本行。</p>
 */
@RestController
@RequestMapping("/api/v1/notification")
@Slf4j
public class NotificationController {

    private static final long BROADCAST_USER_ID = 0L;

    @Resource
    private NotificationService notificationService;

    @Resource
    private NotificationReadService notificationReadService;

    @Resource
    private UserService userService;

    /**
     * 通知分页查询 (当前用户的 + 广播通知)
     */
    @PostMapping("/list/page")
    public BaseResponse<Page<NotificationVO>> listNotificationVOByPage(
            @RequestBody NotificationQueryRequest request,
            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);

        long current = request.getCurrent();
        long size = request.getPageSize();

        // 用户自己的通知 + 广播通知 (user_id=0)
        QueryWrapper<Notification> queryWrapper = new QueryWrapper<>();
        queryWrapper.and(w -> w.eq("user_id", loginUser.getId()).or().eq("user_id", BROADCAST_USER_ID));
        queryWrapper.eq("status", 1); // 只查询已发布的通知
        queryWrapper.orderByDesc("create_time");

        Page<Notification> page = notificationService.page(new Page<>(current, size), queryWrapper);
        log.info("用户通知查询: userId={}, total={}, records={}",
                loginUser.getId(), page.getTotal(), page.getRecords().size());

        // 广播的已读状态来自 notification_read，不来自通知行本身
        List<Long> broadcastIds = page.getRecords().stream()
                .filter(n -> BROADCAST_USER_ID == safeUserId(n))
                .map(Notification::getId)
                .collect(Collectors.toList());
        Set<Long> readIds = notificationReadService.readNotificationIds(loginUser.getId(), broadcastIds);

        Page<NotificationVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream()
                .map(n -> toVo(n, readIds))
                .collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    /**
     * 获取未读通知数量
     *
     * <p>旧实现只数 {@code is_read = 0}，广播那行永远算未读 → 红点消不掉。
     * 现在 = 自己的未读 + (已发布广播 - 自己已读过的广播)。</p>
     */
    @GetMapping("/unread/count")
    public BaseResponse<Long> getUnreadCount(HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        long mineUnread = notificationService.count(new QueryWrapper<Notification>()
                .eq("user_id", loginUser.getId())
                .eq("is_read", 0)
                .eq("status", 1));

        List<Long> broadcastIds = notificationService.list(new QueryWrapper<Notification>()
                        .eq("user_id", BROADCAST_USER_ID)
                        .eq("status", 1)
                        .select("id"))
                .stream().map(Notification::getId).collect(Collectors.toList());
        long broadcastUnread = 0L;
        if (!broadcastIds.isEmpty()) {
            long readCount = notificationReadService.readNotificationIds(loginUser.getId(), broadcastIds).size();
            broadcastUnread = Math.max(0L, broadcastIds.size() - readCount);
        }
        return ResultUtils.success(mineUnread + broadcastUnread);
    }

    /**
     * 获取通知详情
     */
    @GetMapping("/detail")
    public BaseResponse<NotificationVO> getNotificationDetail(@RequestParam(value = "id") long id,
                                                               HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        Notification notification = notificationService.getById(id);
        ThrowUtils.throwIf(notification == null, ErrorCode.NOT_FOUND_ERROR);
        // 只能查看自己的通知或广播通知
        ThrowUtils.throwIf(!notification.getUserId().equals(loginUser.getId())
                && notification.getUserId() != BROADCAST_USER_ID, ErrorCode.NO_AUTH_ERROR);
        Set<Long> readIds = notificationReadService.readNotificationIds(loginUser.getId(),
                List.of(notification.getId()));
        return ResultUtils.success(toVo(notification, readIds));
    }

    /**
     * 标记单条通知为已读
     */
    @PostMapping("/read/{id}")
    public BaseResponse<Boolean> markAsRead(@PathVariable long id,
                                            HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        Notification notification = notificationService.getById(id);
        ThrowUtils.throwIf(notification == null, ErrorCode.NOT_FOUND_ERROR);

        // 广播通知: 写已读记录（幂等），不再复制通知行
        if (BROADCAST_USER_ID == safeUserId(notification)) {
            return ResultUtils.success(notificationReadService.markRead(loginUser.getId(), id));
        }

        // 个人通知: 直接标记已读
        return ResultUtils.success(notificationService.markAsRead(id, loginUser));
    }

    /**
     * 标记所有通知为已读（含广播）
     */
    @PostMapping("/read/all")
    public BaseResponse<Boolean> markAllAsRead(HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        boolean personal = notificationService.markAllAsRead(loginUser);
        int broadcasts = notificationReadService.markAllBroadcastsRead(loginUser.getId());
        log.info("全部已读: userId={}, personalUpdated={}, broadcastMarked={}",
                loginUser.getId(), personal, broadcasts);
        return ResultUtils.success(true);
    }

    private static long safeUserId(Notification notification) {
        return notification.getUserId() == null ? -1L : notification.getUserId();
    }

    private static NotificationVO toVo(Notification notification, Set<Long> broadcastReadIds) {
        NotificationVO vo = NotificationVO.objToVo(notification);
        if (vo != null && BROADCAST_USER_ID == safeUserId(notification) && broadcastReadIds.contains(vo.getId())) {
            vo.setIsRead(1);
        }
        return vo;
    }
}
