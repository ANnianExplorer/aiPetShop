package com.petlumina.backend.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.user.UserQueryRequest;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.LoginUserVO;

import javax.servlet.http.HttpServletRequest;

/**
 * 用户服务接口
 */
public interface UserService extends IService<User> {

    /**
     * 构建查询条件
     */
    QueryWrapper<User> getQueryWrapper(UserQueryRequest request);

    /**
     * 获取当前登录用户
     */
    User getLoginUser(HttpServletRequest request);

    /**
     * 判断是否管理员
     */
    boolean isAdmin(User user);

    /**
     * Entity → LoginUserVO
     */
    LoginUserVO getLoginUserVO(User user);

    /**
     * 更新用户资料
     */
    boolean updateUserProfile(User user, User loginUser);

    /**
     * 更新用户头像
     */
    boolean updateUserAvatar(String avatarUrl, User loginUser);

    /**
     * 修改密码
     */
    boolean updateUserPassword(String oldPassword, String newPassword, User loginUser);
}
