package com.petlumina.backend.manager.auth;

import cn.dev33.satoken.stp.StpInterface;
import com.petlumina.backend.service.user.UserService;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.Collections;
import java.util.List;

/**
 * Sa-Token 权限服务实现
 */
@Component
public class StpInterfaceImpl implements StpInterface {

    @Resource
    private UserService userService;

    @Override
    public List<String> getPermissionList(Object loginId, String loginType) {
        return Collections.emptyList();
    }

    @Override
    public List<String> getRoleList(Object loginId, String loginType) {
        long userId = Long.parseLong(loginId.toString());
        com.petlumina.backend.model.entity.User user = userService.getById(userId);
        if (user == null) {
            return Collections.emptyList();
        }
        return Collections.singletonList(user.getRole());
    }
}
