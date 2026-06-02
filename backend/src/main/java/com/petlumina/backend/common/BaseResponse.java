package com.petlumina.backend.common;

import lombok.Data;

import java.io.Serializable;

/**
 * 统一响应封装
 */
@Data
public class BaseResponse<T> implements Serializable {

    private int code;

    private T data;

    private String message;

    public BaseResponse(int code, T data, String message) {
        this.code = code;
        this.data = data;
        this.message = message;
    }
}
