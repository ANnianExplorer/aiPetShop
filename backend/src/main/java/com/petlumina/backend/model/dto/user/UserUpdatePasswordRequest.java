package com.petlumina.backend.model.dto.user;

import lombok.Data;

import java.io.Serializable;

/**
 * 修改密码请求
 */
@Data
public class UserUpdatePasswordRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String oldPassword;

    private String newPassword;
}
