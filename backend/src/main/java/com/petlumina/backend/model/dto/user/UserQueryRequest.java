package com.petlumina.backend.model.dto.user;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 用户查询请求
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class UserQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String nickname;

    private String phone;

    private String email;

    private String role;

    private Integer status;
}
