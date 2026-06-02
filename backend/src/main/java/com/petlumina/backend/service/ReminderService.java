package com.petlumina.backend.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.reminder.ReminderQueryRequest;
import com.petlumina.backend.model.entity.Reminder;
import com.petlumina.backend.model.entity.User;

/**
 * 日程提醒服务接口
 */
public interface ReminderService extends IService<Reminder> {

    /**
     * 构建查询条件
     */
    QueryWrapper<Reminder> getQueryWrapper(ReminderQueryRequest request);

    /**
     * 添加提醒
     */
    long addReminder(Reminder reminder, User loginUser);

    /**
     * 删除提醒 (校验权限)
     */
    boolean deleteReminder(long id, User loginUser);

    /**
     * 编辑提醒 (校验权限)
     */
    boolean editReminder(Reminder reminder, User loginUser);

    /**
     * 切换完成状态
     */
    boolean toggleComplete(long id, User loginUser);
}
