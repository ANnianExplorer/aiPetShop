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
import com.petlumina.backend.service.user.NotificationService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 通知控制器
 */
@RestController
@RequestMapping("/api/v1/notification")
@Slf4j
public class NotificationController {

    @Resource
    private NotificationService notificationService;

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

        // 简单查询: 用户自己的通知 + 广播通知 (user_id=0)
        QueryWrapper<Notification> queryWrapper = new QueryWrapper<>();
        queryWrapper.and(w -> w.eq("user_id", loginUser.getId()).or().eq("user_id", 0));
        queryWrapper.eq("status", 1); // 只查询已发布的通知
        queryWrapper.orderByDesc("create_time");

        log.info("用户通知查询: userId={}, SQL={}", loginUser.getId(), queryWrapper.getCustomSqlSegment());

        Page<Notification> page = notificationService.page(new Page<>(current, size), queryWrapper);
        log.info("用户通知结果: total={}, records={}", page.getTotal(), page.getRecords().size());

        Page<NotificationVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(NotificationVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    /**
     * 获取未读通知数量
     */
    @GetMapping("/unread/count")
    public BaseResponse<Long> getUnreadCount(HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        long count = notificationService.count(
                new QueryWrapper<Notification>()
                        .and(w -> w.eq("user_id", loginUser.getId()).or().eq("user_id", 0))
                        .eq("is_read", 0));
        return ResultUtils.success(count);
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
                && notification.getUserId() != 0, ErrorCode.NO_AUTH_ERROR);
        return ResultUtils.success(NotificationVO.objToVo(notification));
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

        // 广播通知 (user_id=0): 创建个人已读副本
        if (notification.getUserId() != null && notification.getUserId() == 0) {
            Notification personalCopy = new Notification();
            personalCopy.setUserId(loginUser.getId());
            personalCopy.setType(notification.getType());
            personalCopy.setTitle(notification.getTitle());
            personalCopy.setContent(notification.getContent());
            personalCopy.setIsRead(1);
            personalCopy.setStatus(1);
            personalCopy.setRelatedId(notification.getId());
            notificationService.save(personalCopy);
            return ResultUtils.success(true);
        }

        // 个人通知: 直接标记已读
        boolean result = notificationService.markAsRead(id, loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 标记所有通知为已读
     */
    @PostMapping("/read/all")
    public BaseResponse<Boolean> markAllAsRead(HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = notificationService.markAllAsRead(loginUser);
        return ResultUtils.success(result);
    }
}
