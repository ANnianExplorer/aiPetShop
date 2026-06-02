package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.logentry.LogEntryQueryRequest;
import com.petlumina.backend.model.entity.LogEntry;
import com.petlumina.backend.model.vo.LogEntryVO;
import com.petlumina.backend.service.user.LogEntryService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/admin/log")
@Slf4j
public class AdminLogController {

    @Resource
    private LogEntryService logEntryService;

    @PostMapping("/list/page/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<LogEntryVO>> listLogVOByPage(@RequestBody LogEntryQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<LogEntry> queryWrapper = logEntryService.getQueryWrapper(request);
        Page<LogEntry> page = logEntryService.page(new Page<>(current, size), queryWrapper);
        Page<LogEntryVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(LogEntryVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    @PostMapping("/delete")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> deleteLog(@RequestBody DeleteRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() <= 0, ErrorCode.PARAMS_ERROR);
        LogEntry logEntry = logEntryService.getById(request.getId());
        ThrowUtils.throwIf(logEntry == null, ErrorCode.NOT_FOUND_ERROR);
        boolean result = logEntryService.removeById(request.getId());
        return ResultUtils.success(result);
    }
}
