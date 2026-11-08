package com.petlumina.backend.model.vo;

import lombok.Data;

import java.io.Serializable;

/**
 * 登录用户 VO
 */
@Data
public class LoginUserVO implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 用户ID */
    private Long id;

    /** 昵称 */
    private String nickname;

    /** 头像 */
    private String avatar;

    /** 手机号 */
    private String phone;

    /** 角色（user / admin）：Agent 运行时用它判断管理端权限 */
    private String role;

    /** Token */
    private String token;
}
