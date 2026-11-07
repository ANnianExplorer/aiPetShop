package com.petlumina.backend.exception;

import cn.dev33.satoken.exception.NotLoginException;
import cn.dev33.satoken.exception.NotPermissionException;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.BindException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

import javax.servlet.http.HttpServletRequest;

/**
 * 全局异常处理器。
 *
 * <p>除了 body 里的业务码，响应状态码也按业务语义返回（400/401/403/404/413/429/500），
 * 这样网关、监控、浏览器 DevTools 都能按状态码告警；body 结构保持不变，老前端不受影响。</p>
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @Value("${spring.profiles.active:prod}")
    private String activeProfile;

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<BaseResponse<?>> handleBusinessException(BusinessException e) {
        log.error("业务异常: code={}, message={}", e.getCode(), e.getMessage());
        return build(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(NotLoginException.class)
    public ResponseEntity<BaseResponse<?>> handleNotLoginException(NotLoginException e) {
        log.warn("未登录: {}", e.getMessage());
        return build(ErrorCode.NOT_LOGIN_ERROR.getCode(), ErrorCode.NOT_LOGIN_ERROR.getMessage());
    }

    @ExceptionHandler(NotPermissionException.class)
    public ResponseEntity<BaseResponse<?>> handleNotPermissionException(NotPermissionException e) {
        log.warn("无权限: {}", e.getMessage());
        return build(ErrorCode.NO_AUTH_ERROR.getCode(), ErrorCode.NO_AUTH_ERROR.getMessage());
    }

    /**
     * 参数校验 / 参数类型错误，统一 400，避免落到 500。
     */
    @ExceptionHandler({
            MethodArgumentNotValidException.class,
            BindException.class,
            MissingServletRequestParameterException.class,
            HttpMessageNotReadableException.class,
            IllegalArgumentException.class
    })
    public ResponseEntity<BaseResponse<?>> handleBadRequest(Exception e) {
        log.warn("请求参数错误: {} - {}", e.getClass().getSimpleName(), e.getMessage());
        return build(ErrorCode.PARAMS_ERROR.getCode(), ErrorCode.PARAMS_ERROR.getMessage());
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<BaseResponse<?>> handleUploadTooLarge(MaxUploadSizeExceededException e) {
        log.warn("上传文件过大: {}", e.getMessage());
        return build(ErrorCode.PARAMS_ERROR.getCode(), "上传文件过大");
    }

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<BaseResponse<?>> handleRuntimeException(RuntimeException e, HttpServletRequest request) {
        String uri = request.getRequestURI();
        log.error("系统异常 [{}]: {} - {}", uri, e.getClass().getSimpleName(), e.getMessage(), e);
        // 开发环境返回详细错误信息，方便调试；生产只给通用文案
        if ("dev".equals(activeProfile)) {
            return build(ErrorCode.SYSTEM_ERROR.getCode(),
                    e.getClass().getSimpleName() + ": " + e.getMessage());
        }
        return build(ErrorCode.SYSTEM_ERROR.getCode(), ErrorCode.SYSTEM_ERROR.getMessage());
    }

    private static ResponseEntity<BaseResponse<?>> build(int code, String message) {
        return ResponseEntity.status(toStatus(code)).body(ResultUtils.error(code, message));
    }

    /**
     * 业务码 -> HTTP 状态码。40100 未登录是 401；40101 无权限与 40300 都是 403。
     */
    static HttpStatus toStatus(int code) {
        switch (code) {
            case 40000:
                return HttpStatus.BAD_REQUEST;
            case 40100:
                return HttpStatus.UNAUTHORIZED;
            case 40101:
            case 40300:
                return HttpStatus.FORBIDDEN;
            case 40400:
                return HttpStatus.NOT_FOUND;
            case 41300:
                return HttpStatus.PAYLOAD_TOO_LARGE;
            case 42900:
                return HttpStatus.TOO_MANY_REQUESTS;
            default:
                return HttpStatus.INTERNAL_SERVER_ERROR;
        }
    }
}
