package com.petlumina.backend.service.user.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.ReminderMapper;
import com.petlumina.backend.model.dto.reminder.ReminderQueryRequest;
import com.petlumina.backend.model.entity.Reminder;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.user.ReminderService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;

/**
 * 日程提醒服务实现
 */
@Service
@Slf4j
public class ReminderServiceImpl extends ServiceImpl<ReminderMapper, Reminder>
        implements ReminderService {

    @Resource
    private UserService userService;

    @Override
    public QueryWrapper<Reminder> getQueryWrapper(ReminderQueryRequest request) {
        QueryWrapper<Reminder> queryWrapper = new QueryWrapper<>();
        String type = request.getType();
        Long petId = request.getPetId();
        Long userId = request.getUserId();
        Integer isCompleted = request.getIsCompleted();

        queryWrapper.eq(userId != null, "user_id", userId);
        queryWrapper.eq(StrUtil.isNotBlank(type), "type", type);
        queryWrapper.eq(petId != null, "pet_id", petId);
        queryWrapper.eq(isCompleted != null, "is_completed", isCompleted);
        queryWrapper.ge(request.getStartDate() != null, "remind_time", request.getStartDate());
        queryWrapper.le(request.getEndDate() != null, "remind_time", request.getEndDate());
        queryWrapper.orderByAsc("remind_time");
        return queryWrapper;
    }

    @Override
    public long addReminder(Reminder reminder, User loginUser) {
        reminder.setUserId(loginUser.getId());
        reminder.setIsCompleted(0);
        boolean saved = this.save(reminder);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "添加提醒失败");
        return reminder.getId();
    }

    @Override
    public boolean deleteReminder(long id, User loginUser) {
        Reminder reminder = this.getById(id);
        ThrowUtils.throwIf(reminder == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!reminder.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.removeById(id);
    }

    @Override
    public boolean editReminder(Reminder reminder, User loginUser) {
        Reminder existing = this.getById(reminder.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!existing.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.updateById(reminder);
    }

    @Override
    public boolean toggleComplete(long id, User loginUser) {
        Reminder reminder = this.getById(id);
        ThrowUtils.throwIf(reminder == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!reminder.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        reminder.setIsCompleted(reminder.getIsCompleted() == 1 ? 0 : 1);
        return this.updateById(reminder);
    }
}
