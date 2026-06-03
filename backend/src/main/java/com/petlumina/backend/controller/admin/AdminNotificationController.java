package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.notification.NotificationQueryRequest;
import com.petlumina.backend.model.entity.Notification;
import com.petlumina.backend.model.vo.NotificationVO;
import com.petlumina.backend.service.user.NotificationService;
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
