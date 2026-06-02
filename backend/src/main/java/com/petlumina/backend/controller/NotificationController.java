package com.petlumina.backend.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.notification.NotificationQueryRequest;
import com.petlumina.backend.model.entity.Notification;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.NotificationVO;
import com.petlumina.backend.service.NotificationService;
import com.petlumina.backend.service.UserService;
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
     * 通知分页查询 (当前用户的)
     */
    @PostMapping("/list/page")
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<NotificationVO>> listNotificationVOByPage(
            @RequestBody NotificationQueryRequest request,
            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);

        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Notification> queryWrapper = notificationService.getQueryWrapper(request);
        queryWrapper.eq("user_id", loginUser.getId());

        Page<Notification> page = notificationService.page(new Page<>(current, size), queryWrapper);

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
        long count = notificationService.getUnreadCount(loginUser);
        return ResultUtils.success(count);
    }

    /**
     * 标记单条通知为已读
     */
    @PostMapping("/read/{id}")
    public BaseResponse<Boolean> markAsRead(@PathVariable long id,
                                            HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
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
