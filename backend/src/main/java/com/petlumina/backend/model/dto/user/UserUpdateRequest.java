package com.petlumina.backend.model.dto.user;

import lombok.Data;

import java.io.Serializable;

/**
 * 用户资料更新请求
 */
@Data
public class UserUpdateRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String nickname;

    private String bio;

    private String location;
}
