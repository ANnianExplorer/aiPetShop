package com.petlumina.backend.controller.user;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.logentry.LogEntryAddRequest;
import com.petlumina.backend.model.dto.logentry.LogEntryEditRequest;
import com.petlumina.backend.model.dto.logentry.LogEntryQueryRequest;
import com.petlumina.backend.model.entity.LogEntry;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.LogEntryVO;
import com.petlumina.backend.model.vo.UserVO;
import com.petlumina.backend.service.user.LogEntryService;
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
 * 生活记录控制器
 */
@RestController
@RequestMapping("/api/v1/log")
@Slf4j
public class LogController {

    @Resource
    private LogEntryService logEntryService;

    @Resource
    private UserService userService;

    /**
     * 添加生活记录
     */
    @PostMapping("/add")
    @RateLimiter(key = "log_add", time = 60, count = 10, message = "添加记录操作过于频繁")
    public BaseResponse<Long> addLogEntry(@RequestBody LogEntryAddRequest request,
                                          HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(request.getTitle() == null || request.getTitle().isBlank(), ErrorCode.PARAMS_ERROR, "标题不能为空");

        User loginUser = userService.getLoginUser(httpRequest);

        LogEntry logEntry = new LogEntry();
        BeanUtils.copyProperties(request, logEntry);

        long logId = logEntryService.addLogEntry(logEntry, loginUser);
        log.info("添加生活记录成功: logId={}, userId={}", logId, loginUser.getId());
        return ResultUtils.success(logId);
    }

    /**
     * 删除生活记录
     */
    @PostMapping("/delete")
    public BaseResponse<Boolean> deleteLogEntry(@RequestBody DeleteRequest request,
                                                HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = logEntryService.deleteLogEntry(request.getId(), loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 编辑生活记录
     */
    @PostMapping("/edit")
    public BaseResponse<Boolean> editLogEntry(@RequestBody LogEntryEditRequest request,
                                              HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);

        LogEntry logEntry = new LogEntry();
        BeanUtils.copyProperties(request, logEntry);

        boolean result = logEntryService.editLogEntry(logEntry, loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 获取生活记录详情 (VO)
     */
    @GetMapping("/get/vo")
    public BaseResponse<LogEntryVO> getLogEntryVO(@RequestParam long id,
                                                  HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        LogEntry logEntry = logEntryService.getById(id);
        ThrowUtils.throwIf(logEntry == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!logEntry.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        LogEntryVO vo = LogEntryVO.objToVo(logEntry);
        // 填充用户信息
        User user = userService.getById(logEntry.getUserId());
        if (user != null) {
            vo.setUser(UserVO.objToVo(user));
        }
        return ResultUtils.success(vo);
    }

    /**
     * 生活记录分页查询 (当前用户的)
     */
    @PostMapping("/list/page/vo")
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<LogEntryVO>> listLogEntryVOByPage(
            @RequestBody LogEntryQueryRequest request,
            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        // 只查当前用户的记录
        request.setUserId(loginUser.getId());

        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<LogEntry> queryWrapper = logEntryService.getQueryWrapper(request);
        Page<LogEntry> page = logEntryService.page(new Page<>(current, size), queryWrapper);

        Page<LogEntryVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(LogEntryVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }
}
