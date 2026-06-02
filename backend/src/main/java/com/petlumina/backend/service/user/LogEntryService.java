package com.petlumina.backend.service.user;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.logentry.LogEntryQueryRequest;
import com.petlumina.backend.model.entity.LogEntry;
import com.petlumina.backend.model.entity.User;

/**
 * 生活记录服务接口
 */
public interface LogEntryService extends IService<LogEntry> {

    /**
     * 构建查询条件
     */
    QueryWrapper<LogEntry> getQueryWrapper(LogEntryQueryRequest request);

    /**
     * 添加生活记录
     */
    long addLogEntry(LogEntry logEntry, User loginUser);

    /**
     * 删除生活记录 (校验权限)
     */
    boolean deleteLogEntry(long id, User loginUser);

    /**
     * 编辑生活记录 (校验权限)
     */
    boolean editLogEntry(LogEntry logEntry, User loginUser);
}
