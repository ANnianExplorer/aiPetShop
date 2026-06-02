package com.petlumina.backend.utils;

import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.exception.ErrorCode;

/**
 * 异常抛出工具类
 */
public class ThrowUtils {

    /**
     * 条件成立则抛出异常
     */
    public static void throwIf(boolean condition, ErrorCode errorCode) {
        if (condition) {
            throw new BusinessException(errorCode);
        }
    }

    /**
     * 条件成立则抛出异常 (自定义消息)
     */
    public static void throwIf(boolean condition, ErrorCode errorCode, String message) {
        if (condition) {
            throw new BusinessException(errorCode, message);
        }
    }
}
