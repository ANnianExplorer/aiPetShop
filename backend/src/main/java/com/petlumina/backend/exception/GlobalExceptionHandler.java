package com.petlumina.backend.exception;

import cn.dev33.satoken.exception.NotLoginException;
import cn.dev33.satoken.exception.NotPermissionException;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常处理器
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

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
    public BaseResponse<?> handleRuntimeException(RuntimeException e) {
        log.error("系统异常", e);
        return ResultUtils.error(ErrorCode.SYSTEM_ERROR);
    }
}
