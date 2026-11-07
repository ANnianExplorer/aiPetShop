package com.petlumina.backend.model.dto.user;

import lombok.Data;

import java.io.Serializable;

/**
 * 管理端新增/编辑用户请求（E10：管理端原来只有前端 toast，没有真实落库接口）
 */
@Data
public class AdminUserSaveRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 编辑时必填；新增时忽略 */
    private Long id;

    private String phone;

    private String email;

    /** 新增必填；编辑时留空表示不修改口令 */
    private String password;

    private String nickname;

    private String avatar;

    /** user / admin */
    private String role;

    /** 0 禁用 / 1 正常 */
    private Integer status;
}
