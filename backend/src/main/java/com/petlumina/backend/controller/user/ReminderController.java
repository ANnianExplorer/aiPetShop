package com.petlumina.backend.controller.user;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.reminder.ReminderAddRequest;
import com.petlumina.backend.model.dto.reminder.ReminderEditRequest;
import com.petlumina.backend.model.dto.reminder.ReminderQueryRequest;
import com.petlumina.backend.model.entity.Reminder;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.ReminderVO;
import com.petlumina.backend.service.user.ReminderService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 日程提醒控制器
 */
@RestController
@RequestMapping("/api/v1/reminder")
@Slf4j
public class ReminderController {

    @Resource
    private ReminderService reminderService;

    @Resource
    private UserService userService;

    /**
     * 添加提醒
     */
    @PostMapping("/add")
    @RateLimiter(key = "reminder_add", time = 60, count = 10, message = "添加提醒操作过于频繁")
    public BaseResponse<Long> addReminder(@RequestBody ReminderAddRequest request,
                                          HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(request.getTitle() == null || request.getTitle().isBlank(), ErrorCode.PARAMS_ERROR, "标题不能为空");

        User loginUser = userService.getLoginUser(httpRequest);

        Reminder reminder = new Reminder();
        BeanUtils.copyProperties(request, reminder);

        long reminderId = reminderService.addReminder(reminder, loginUser);
        log.info("添加提醒成功: reminderId={}, userId={}", reminderId, loginUser.getId());
        return ResultUtils.success(reminderId);
    }

    /**
     * 删除提醒
     */
    @PostMapping("/delete")
    public BaseResponse<Boolean> deleteReminder(@RequestBody DeleteRequest request,
                                                HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = reminderService.deleteReminder(request.getId(), loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 编辑提醒
     */
    @PostMapping("/edit")
    public BaseResponse<Boolean> editReminder(@RequestBody ReminderEditRequest request,
                                              HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);

        Reminder reminder = new Reminder();
        BeanUtils.copyProperties(request, reminder);

        boolean result = reminderService.editReminder(reminder, loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 获取提醒详情 (VO)
     */
    @GetMapping("/get/vo")
    public BaseResponse<ReminderVO> getReminderVO(@RequestParam long id,
                                                  HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        Reminder reminder = reminderService.getById(id);
        ThrowUtils.throwIf(reminder == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!reminder.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return ResultUtils.success(ReminderVO.objToVo(reminder));
    }

    /**
     * 提醒分页查询 (当前用户的)
     */
    @PostMapping("/list/page")
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<ReminderVO>> listReminderVOByPage(
            @RequestBody ReminderQueryRequest request,
            HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        // 只查当前用户的提醒
        request.setUserId(loginUser.getId());

        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Reminder> queryWrapper = reminderService.getQueryWrapper(request);
        Page<Reminder> page = reminderService.page(new Page<>(current, size), queryWrapper);

        Page<ReminderVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(ReminderVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    /**
     * 切换提醒完成状态
     */
    @PostMapping("/complete/{id}")
    public BaseResponse<Boolean> toggleComplete(@PathVariable long id,
                                                HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = reminderService.toggleComplete(id, loginUser);
        return ResultUtils.success(result);
    }
}
