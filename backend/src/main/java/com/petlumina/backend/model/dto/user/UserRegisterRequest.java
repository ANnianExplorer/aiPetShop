package com.petlumina.backend.model.dto.user;

import lombok.Data;

import java.io.Serializable;

/**
 * 用户注册请求
 */
@Data
public class UserRegisterRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 手机号 */
    private String phone;

    /** 验证码 */
    private String code;

    /** 密码 */
    private String password;
}
