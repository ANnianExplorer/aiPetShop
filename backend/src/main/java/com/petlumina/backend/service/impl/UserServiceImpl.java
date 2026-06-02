package com.petlumina.backend.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.crypto.digest.BCrypt;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.UserMapper;
import com.petlumina.backend.model.dto.user.UserQueryRequest;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.LoginUserVO;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.servlet.http.HttpServletRequest;

/**
 * 用户服务实现
 */
@Service
@Slf4j
public class UserServiceImpl extends ServiceImpl<UserMapper, User>
        implements UserService {

    @Override
    public QueryWrapper<User> getQueryWrapper(UserQueryRequest request) {
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        String nickname = request.getNickname();
        String phone = request.getPhone();
        String email = request.getEmail();
        String role = request.getRole();
        Integer status = request.getStatus();

        queryWrapper.like(StrUtil.isNotBlank(nickname), "nickname", nickname);
        queryWrapper.like(StrUtil.isNotBlank(phone), "phone", phone);
        queryWrapper.like(StrUtil.isNotBlank(email), "email", email);
        queryWrapper.eq(StrUtil.isNotBlank(role), "role", role);
        queryWrapper.eq(status != null, "status", status);
        queryWrapper.orderByDesc("create_time");
        return queryWrapper;
    }

    @Override
    public User getLoginUser(HttpServletRequest request) {
        // 从 Sa-Token 获取用户 ID
        try {
            long userId = Long.parseLong(StpUtil.getLoginId().toString());
            User user = this.getById(userId);
            if (user == null || user.getStatus() == UserConstant.STATUS_DISABLED) {
                throw new BusinessException(ErrorCode.NOT_LOGIN_ERROR);
            }
            return user;
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            throw new BusinessException(ErrorCode.NOT_LOGIN_ERROR);
        }
    }

    @Override
    public boolean isAdmin(User user) {
        return user != null && UserConstant.ADMIN_ROLE.equals(user.getRole());
    }

    @Override
    public LoginUserVO getLoginUserVO(User user) {
        if (user == null) {
            return null;
        }
        LoginUserVO vo = new LoginUserVO();
        vo.setId(user.getId());
        vo.setNickname(user.getNickname());
        vo.setAvatar(user.getAvatar());
        vo.setPhone(user.getPhone());
        vo.setToken(StpUtil.getTokenValue());
        return vo;
    }

    @Override
    public boolean updateUserProfile(User user, User loginUser) {
        User update = new User();
        update.setId(loginUser.getId());
        update.setNickname(user.getNickname());
        update.setBio(user.getBio());
        update.setLocation(user.getLocation());
        return this.updateById(update);
    }

    @Override
    public boolean updateUserAvatar(String avatarUrl, User loginUser) {
        User update = new User();
        update.setId(loginUser.getId());
        update.setAvatar(avatarUrl);
        return this.updateById(update);
    }

    @Override
    public boolean updateUserPassword(String oldPassword, String newPassword, User loginUser) {
        ThrowUtils.throwIf(!BCrypt.checkpw(oldPassword, loginUser.getPassword()),
                ErrorCode.PARAMS_ERROR, "原密码错误");
        ThrowUtils.throwIf(StrUtil.isBlank(newPassword) || newPassword.length() < 6,
                ErrorCode.PARAMS_ERROR, "新密码长度不能少于6位");

        User update = new User();
        update.setId(loginUser.getId());
        update.setPassword(BCrypt.hashpw(newPassword));
        return this.updateById(update);
    }
}
