package com.petlumina.backend.constant;

/**
 * 用户相关常量
 */
public interface UserConstant {

    /** 普通用户角色 */
    String USER_ROLE = "user";

    /** 管理员角色 */
    String ADMIN_ROLE = "admin";

    /** 用户正常状态 */
    Integer STATUS_NORMAL = 1;

    /** 用户禁用状态 */
    Integer STATUS_DISABLED = 0;
}
