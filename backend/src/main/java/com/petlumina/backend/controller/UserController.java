package com.petlumina.backend.controller;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.manager.cos.CosManager;
import com.petlumina.backend.model.dto.user.UserQueryRequest;
import com.petlumina.backend.model.dto.user.UserUpdatePasswordRequest;
import com.petlumina.backend.model.dto.user.UserUpdateRequest;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.LoginUserVO;
import com.petlumina.backend.model.vo.UserVO;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 用户控制器
 */
@RestController
@RequestMapping("/api/v1/user")
@Slf4j
public class UserController {

    @Resource
    private UserService userService;

    @Resource
    private CosManager cosManager;

    /**
     * 获取当前登录用户信息
     */
    @GetMapping("/get/login")
    public BaseResponse<LoginUserVO> getLoginUser(HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        LoginUserVO vo = userService.getLoginUserVO(loginUser);
        return ResultUtils.success(vo);
    }

    /**
     * 获取用户详情 (VO)
     */
    @GetMapping("/get/vo")
    public BaseResponse<UserVO> getUserVO(@RequestParam long id) {
        User user = userService.getById(id);
        ThrowUtils.throwIf(user == null, ErrorCode.NOT_FOUND_ERROR);
        return ResultUtils.success(UserVO.objToVo(user));
    }

    /**
     * 更新用户资料
     */
    @PostMapping("/update")
    @RateLimiter(key = "user_update", time = 60, count = 10, message = "更新资料操作过于频繁")
    public BaseResponse<Boolean> updateUser(@RequestBody UserUpdateRequest request,
                                            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);

        User user = new User();
        if (StrUtil.isNotBlank(request.getNickname())) {
            user.setNickname(request.getNickname());
        }
        user.setBio(request.getBio());
        user.setLocation(request.getLocation());

        boolean result = userService.updateUserProfile(user, loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 更新用户头像
     */
    @PostMapping("/update/avatar")
    @RateLimiter(key = "user_avatar", time = 60, count = 5, message = "更新头像操作过于频繁")
    public BaseResponse<String> updateAvatar(@RequestParam("file") MultipartFile file,
                                             HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(file == null || file.isEmpty(), ErrorCode.PARAMS_ERROR, "头像文件不能为空");

        User loginUser = userService.getLoginUser(httpRequest);

        // 上传到 COS
        String originalFilename = file.getOriginalFilename();
        String extension = "";
        if (originalFilename != null && originalFilename.contains(".")) {
            extension = originalFilename.substring(originalFilename.lastIndexOf("."));
        }
        String key = "avatar/" + loginUser.getId() + extension;
        String avatarUrl;
        try {
            avatarUrl = cosManager.upload(key, file.getInputStream());
        } catch (Exception e) {
            log.error("头像上传失败", e);
            throw new BusinessException(ErrorCode.OPERATION_ERROR, "头像上传失败");
        }
        ThrowUtils.throwIf(StrUtil.isBlank(avatarUrl), ErrorCode.OPERATION_ERROR, "头像上传失败");

        boolean result = userService.updateUserAvatar(avatarUrl, loginUser);
        ThrowUtils.throwIf(!result, ErrorCode.OPERATION_ERROR, "更新头像失败");

        return ResultUtils.success(avatarUrl);
    }

    /**
     * 修改密码
     */
    @PostMapping("/update/password")
    @RateLimiter(key = "user_password", time = 300, count = 3, message = "修改密码操作过于频繁")
    public BaseResponse<Boolean> updatePassword(@RequestBody UserUpdatePasswordRequest request,
                                                HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(StrUtil.isBlank(request.getOldPassword()), ErrorCode.PARAMS_ERROR, "原密码不能为空");
        ThrowUtils.throwIf(StrUtil.isBlank(request.getNewPassword()), ErrorCode.PARAMS_ERROR, "新密码不能为空");

        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = userService.updateUserPassword(request.getOldPassword(), request.getNewPassword(), loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 用户分页查询 (管理员)
     */
    @PostMapping("/list/page/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<UserVO>> listUserVOByPage(
            @RequestBody UserQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<User> queryWrapper = userService.getQueryWrapper(request);
        Page<User> page = userService.page(new Page<>(current, size), queryWrapper);

        Page<UserVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(UserVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }
}
