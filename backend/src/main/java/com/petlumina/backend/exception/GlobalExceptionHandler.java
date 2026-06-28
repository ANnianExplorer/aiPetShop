package com.petlumina.backend.exception;

import cn.dev33.satoken.exception.NotLoginException;
import cn.dev33.satoken.exception.NotPermissionException;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import javax.servlet.http.HttpServletRequest;

/**
 * 全局异常处理器
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @Value("${spring.profiles.active:prod}")
    private String activeProfile;

    @ExceptionHandler(BusinessException.class)
    public BaseResponse<?> handleBusinessException(BusinessException e) {
        log.error("业务异常: {}", e.getMessage());
        return ResultUtils.error(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(NotLoginException.class)
    public BaseResponse<?> handleNotLoginException(NotLoginException e) {
        log.error("未登录: {}", e.getMessage());
        return ResultUtils.error(ErrorCode.NOT_LOGIN_ERROR);
    }

    @ExceptionHandler(NotPermissionException.class)
    public BaseResponse<?> handleNotPermissionException(NotPermissionException e) {
        log.error("无权限: {}", e.getMessage());
        return ResultUtils.error(ErrorCode.NO_AUTH_ERROR);
    }

    @ExceptionHandler(RuntimeException.class)
    public BaseResponse<?> handleRuntimeException(RuntimeException e, HttpServletRequest request) {
        String uri = request.getRequestURI();
        log.error("系统异常 [{}]: {} - {}", uri, e.getClass().getSimpleName(), e.getMessage(), e);
        // 开发环境返回详细错误信息，方便调试
        if ("dev".equals(activeProfile)) {
            return ResultUtils.error(ErrorCode.SYSTEM_ERROR,
                    e.getClass().getSimpleName() + ": " + e.getMessage());
        }
        return ResultUtils.error(ErrorCode.SYSTEM_ERROR);
    }
}
