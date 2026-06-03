package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.notification.NotificationAddRequest;
import com.petlumina.backend.model.dto.notification.NotificationQueryRequest;
import com.petlumina.backend.model.dto.notification.NotificationToggleRequest;
import com.petlumina.backend.model.entity.Notification;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.NotificationVO;
import com.petlumina.backend.service.user.NotificationService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 管理员通知控制器
 */
@RestController
@RequestMapping("/api/v1/admin/notification")
@Slf4j
public class AdminNotificationController {

    @Resource
    private NotificationService notificationService;

    @Resource
    private UserService userService;

    /**
     * 通知分页查询（所有用户的通知）
     */
    @PostMapping("/list/page/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<NotificationVO>> listNotificationVOByPage(@RequestBody NotificationQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Notification> queryWrapper = notificationService.getQueryWrapper(request);
        queryWrapper.orderByDesc("create_time");
        Page<Notification> page = notificationService.page(new Page<>(current, size), queryWrapper);
        Page<NotificationVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(NotificationVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    /**
     * 发布通知（广播给所有用户）
     */
    @PostMapping("/add")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> addNotification(@RequestBody NotificationAddRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(request.getTitle() == null || request.getTitle().isEmpty(), ErrorCode.PARAMS_ERROR, "标题不能为空");
        // 创建广播模板 (user_id=0, status=1)
        notificationService.createNotification(0L, request.getType(), request.getTitle(), request.getContent(), null);
        return ResultUtils.success(true);
    }

    /**
     * 更新通知
     */
    @PostMapping("/update")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> updateNotification(@RequestBody Notification request) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        Notification existing = notificationService.getById(request.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR);
        if (request.getTitle() != null) existing.setTitle(request.getTitle());
        if (request.getContent() != null) existing.setContent(request.getContent());
        if (request.getType() != null) existing.setType(request.getType());
        boolean result = notificationService.updateById(existing);
        return ResultUtils.success(result);
    }

    /**
     * 切换通知发布状态
     */
    @PostMapping("/toggle-status")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> toggleStatus(@RequestBody NotificationToggleRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(request.getStatus() != 0 && request.getStatus() != 1, ErrorCode.PARAMS_ERROR, "状态值无效");
        // 使用 lambdaUpdate 直接更新 status 字段
        boolean result = notificationService.lambdaUpdate()
                .eq(Notification::getId, request.getId())
                .set(Notification::getStatus, request.getStatus())
                .update();
        log.info("通知状态切换: id={}, newStatus={}, result={}", request.getId(), request.getStatus(), result);
        return ResultUtils.success(result);
    }

    /**
     * 删除通知
     */
    @PostMapping("/delete")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> deleteNotification(@RequestBody com.petlumina.backend.common.DeleteRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        Notification notification = notificationService.getById(request.getId());
        ThrowUtils.throwIf(notification == null, ErrorCode.NOT_FOUND_ERROR);
        boolean result = notificationService.removeById(request.getId());
        return ResultUtils.success(result);
    }
}
