package com.petlumina.backend.model.dto.user;

import lombok.Data;

import java.io.Serializable;

/**
 * 用户登录请求
 */
@Data
public class UserLoginRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 手机号 */
    private String phone;

    /** 密码 */
    private String password;
}
