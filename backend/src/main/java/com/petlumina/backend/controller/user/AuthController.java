package com.petlumina.backend.controller.user;

import cn.dev33.satoken.stp.StpUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.crypto.digest.BCrypt;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.RedisConstant;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.user.UserLoginRequest;
import com.petlumina.backend.model.dto.user.UserRegisterRequest;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.LoginUserVO;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import com.petlumina.backend.utils.VerifyCodeUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.util.concurrent.TimeUnit;

/**
 * 认证控制器
 */
@RestController
@RequestMapping("/api/v1/auth")
@Slf4j
public class AuthController {

    @Resource
    private UserService userService;

    @Resource
    private StringRedisTemplate stringRedisTemplate;

    /**
     * 本地开发 / 自动化测试用的固定验证码；生产环境不配置即为随机码。
     */
    @Value("${petlumina.auth.fixed-verify-code:}")
    private String fixedVerifyCode;

    /**
     * 用户注册
     */
    @PostMapping("/register")
    public BaseResponse<LoginUserVO> register(@RequestBody UserRegisterRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        String phone = request.getPhone();
        String code = request.getCode();
        String password = request.getPassword();

        ThrowUtils.throwIf(StrUtil.hasBlank(phone, code, password), ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(password.length() < 6, ErrorCode.PARAMS_ERROR, "密码长度不能少于6位");

        // 校验验证码
        String redisKey = RedisConstant.VERIFY_CODE_PREFIX + phone;
        String cachedCode = stringRedisTemplate.opsForValue().get(redisKey);
        ThrowUtils.throwIf(!code.equals(cachedCode), ErrorCode.PARAMS_ERROR, "验证码错误或已过期");

        // 检查手机号是否已注册
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("phone", phone);
        long count = userService.count(queryWrapper);
        ThrowUtils.throwIf(count > 0, ErrorCode.PARAMS_ERROR, "该手机号已注册");

        // 创建用户
        User user = new User();
        user.setPhone(phone);
        user.setPassword(BCrypt.hashpw(password));
        user.setNickname("用户" + phone.substring(7));
        user.setRole(UserConstant.USER_ROLE);
        user.setStatus(UserConstant.STATUS_NORMAL);
        boolean saved = userService.save(user);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "注册失败");

        // 清除验证码
        stringRedisTemplate.delete(redisKey);

        // 自动登录
        StpUtil.login(user.getId());
        LoginUserVO vo = userService.getLoginUserVO(user);
        log.info("用户注册成功: phone={}", phone);
        return ResultUtils.success(vo);
    }

    /**
     * 用户登录
     */
    @PostMapping("/login")
    public BaseResponse<LoginUserVO> login(@RequestBody UserLoginRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        String phone = request.getPhone();
        String password = request.getPassword();

        ThrowUtils.throwIf(StrUtil.hasBlank(phone, password), ErrorCode.PARAMS_ERROR);

        // 查询用户
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("phone", phone);
        User user = userService.getOne(queryWrapper);
        ThrowUtils.throwIf(user == null, ErrorCode.PARAMS_ERROR, "手机号或密码错误");

        // 校验密码
        ThrowUtils.throwIf(!BCrypt.checkpw(password, user.getPassword()),
                ErrorCode.PARAMS_ERROR, "手机号或密码错误");

        // 校验状态
        ThrowUtils.throwIf(user.getStatus() == UserConstant.STATUS_DISABLED,
                ErrorCode.FORBIDDEN_ERROR, "账号已被禁用");

        // 登录
        StpUtil.login(user.getId());
        LoginUserVO vo = userService.getLoginUserVO(user);
        log.info("用户登录成功: phone={}", phone);
        return ResultUtils.success(vo);
    }

    /**
     * 退出登录
     */
    @PostMapping("/logout")
    public BaseResponse<Boolean> logout() {
        StpUtil.logout();
        return ResultUtils.success(true);
    }

    /**
     * 发送验证码
     */
    @PostMapping("/send-code")
    public BaseResponse<Boolean> sendCode(@RequestParam String phone) {
        ThrowUtils.throwIf(StrUtil.isBlank(phone), ErrorCode.PARAMS_ERROR);

        // 检查是否频繁发送
        String redisKey = RedisConstant.VERIFY_CODE_PREFIX + phone;
        Boolean exists = stringRedisTemplate.hasKey(redisKey);
        ThrowUtils.throwIf(Boolean.TRUE.equals(exists), ErrorCode.TOO_MANY_REQUEST, "验证码已发送，请稍后再试");

        // 生成验证码：生产环境随机 6 位；只有配置了 petlumina.auth.fixed-verify-code 时才固定
        String code = VerifyCodeUtils.generate(fixedVerifyCode);

        // 存入 Redis
        stringRedisTemplate.opsForValue().set(redisKey, code,
                RedisConstant.VERIFY_CODE_EXPIRE, TimeUnit.SECONDS);

        // TODO: 生产环境对接短信服务 (阿里云/腾讯云 SMS)
        log.debug("验证码已生成: phone={}, code={}", phone, code);
        return ResultUtils.success(true);
    }

    /**
     * 重置密码
     */
    @PostMapping("/reset-password")
    public BaseResponse<Boolean> resetPassword(@RequestBody UserRegisterRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        String phone = request.getPhone();
        String code = request.getCode();
        String password = request.getPassword();

        ThrowUtils.throwIf(StrUtil.hasBlank(phone, code, password), ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(password.length() < 6, ErrorCode.PARAMS_ERROR, "密码长度不能少于6位");

        // 校验验证码
        String redisKey = RedisConstant.VERIFY_CODE_PREFIX + phone;
        String cachedCode = stringRedisTemplate.opsForValue().get(redisKey);
        ThrowUtils.throwIf(!code.equals(cachedCode), ErrorCode.PARAMS_ERROR, "验证码错误或已过期");

        // 查询用户
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("phone", phone);
        User user = userService.getOne(queryWrapper);
        ThrowUtils.throwIf(user == null, ErrorCode.NOT_FOUND_ERROR, "用户不存在");

        // 更新密码
        user.setPassword(BCrypt.hashpw(password));
        boolean updated = userService.updateById(user);
        ThrowUtils.throwIf(!updated, ErrorCode.OPERATION_ERROR);

        // 清除验证码
        stringRedisTemplate.delete(redisKey);

        log.info("密码重置成功: phone={}", phone);
        return ResultUtils.success(true);
    }

    /**
     * 获取当前登录用户
     */
    @GetMapping("/current")
    public BaseResponse<LoginUserVO> getCurrentUser(HttpServletRequest request) {
        User user = userService.getLoginUser(request);
        LoginUserVO vo = userService.getLoginUserVO(user);
        return ResultUtils.success(vo);
    }
}
