package com.petlumina.backend.service.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.LogEntryMapper;
import com.petlumina.backend.model.dto.logentry.LogEntryQueryRequest;
import com.petlumina.backend.model.entity.LogEntry;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.LogEntryService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;

/**
 * 生活记录服务实现
 */
@Service
@Slf4j
public class LogEntryServiceImpl extends ServiceImpl<LogEntryMapper, LogEntry>
        implements LogEntryService {

    @Resource
    private UserService userService;

    @Override
    public QueryWrapper<LogEntry> getQueryWrapper(LogEntryQueryRequest request) {
        QueryWrapper<LogEntry> queryWrapper = new QueryWrapper<>();
        String type = request.getType();
        Long userId = request.getUserId();
        Long petId = request.getPetId();

        queryWrapper.eq(StrUtil.isNotBlank(type), "type", type);
        queryWrapper.eq(userId != null, "user_id", userId);
        queryWrapper.eq(petId != null, "pet_id", petId);
        queryWrapper.orderByDesc("create_time");
        return queryWrapper;
    }

    @Override
    public long addLogEntry(LogEntry logEntry, User loginUser) {
        logEntry.setUserId(loginUser.getId());
        logEntry.setLikes(0);
        boolean saved = this.save(logEntry);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "添加记录失败");
        return logEntry.getId();
    }

    @Override
    public boolean deleteLogEntry(long id, User loginUser) {
        LogEntry logEntry = this.getById(id);
        ThrowUtils.throwIf(logEntry == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!logEntry.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.removeById(id);
    }

    @Override
    public boolean editLogEntry(LogEntry logEntry, User loginUser) {
        LogEntry existing = this.getById(logEntry.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!existing.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.updateById(logEntry);
    }
}
