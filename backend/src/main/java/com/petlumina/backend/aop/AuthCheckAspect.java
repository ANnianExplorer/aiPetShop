package com.petlumina.backend.aop;

import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;

/**
 * 权限校验切面
 */
@Aspect
@Component
@Slf4j
public class AuthCheckAspect {

    @Resource
    private UserService userService;

    @Around("@annotation(authCheck)")
    public Object doInterceptor(ProceedingJoinPoint joinPoint, AuthCheck authCheck) throws Throwable {
        String mustRole = authCheck.mustRole();
        RequestAttributes requestAttributes = RequestContextHolder.getRequestAttributes();
        if (requestAttributes == null) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "获取请求上下文失败");
        }
        HttpServletRequest request = ((ServletRequestAttributes) requestAttributes).getRequest();

        User loginUser = userService.getLoginUser(request);
        String userRole = loginUser.getRole();

        // 管理员拥有所有权限
        if (!"admin".equals(userRole) && !mustRole.equals(userRole)) {
            throw new BusinessException(ErrorCode.NO_AUTH_ERROR);
        }

        return joinPoint.proceed();
    }
}
