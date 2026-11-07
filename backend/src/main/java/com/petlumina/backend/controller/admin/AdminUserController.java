package com.petlumina.backend.controller.admin;

import cn.hutool.core.util.StrUtil;
import cn.hutool.crypto.digest.BCrypt;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.user.AdminUserSaveRequest;
import com.petlumina.backend.model.dto.user.UserQueryRequest;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.PetVO;
import com.petlumina.backend.model.vo.PostVO;
import com.petlumina.backend.model.vo.UserVO;
import com.petlumina.backend.service.user.PetService;
import com.petlumina.backend.service.user.PostService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/admin/user")
@Slf4j
public class AdminUserController {

    @Resource
    private UserService userService;

    @Resource
    private PetService petService;

    @Resource
    private PostService postService;

    @PostMapping("/list/page/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<UserVO>> listUserVOByPage(@RequestBody UserQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<User> queryWrapper = userService.getQueryWrapper(request);
        Page<User> page = userService.page(new Page<>(current, size), queryWrapper);
        Page<UserVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(UserVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    @GetMapping("/get/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Map<String, Object>> getUserDetail(@RequestParam long id) {
        User user = userService.getById(id);
        ThrowUtils.throwIf(user == null, ErrorCode.NOT_FOUND_ERROR);

        Map<String, Object> result = new HashMap<>();
        result.put("user", UserVO.objToVo(user));

        // User's pets
        List<Pet> pets = petService.list(new QueryWrapper<Pet>().eq("user_id", id).eq("is_delete", 0));
        result.put("pets", pets.stream().map(PetVO::objToVo).collect(Collectors.toList()));

        // Recent posts
        List<Post> posts = postService.list(new QueryWrapper<Post>().eq("author_id", id).eq("is_delete", 0)
                .orderByDesc("create_time").last("LIMIT 10"));
        result.put("posts", posts.stream().map(PostVO::objToVo).collect(Collectors.toList()));

        return ResultUtils.success(result);
    }

    @PostMapping("/update/status")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> updateUserStatus(@RequestBody Map<String, Object> params) {
        Long id = Long.valueOf(params.get("id").toString());
        Integer status = Integer.valueOf(params.get("status").toString());
        ThrowUtils.throwIf(status != 0 && status != 1, ErrorCode.PARAMS_ERROR, "状态值无效");

        User user = userService.getById(id);
        ThrowUtils.throwIf(user == null, ErrorCode.NOT_FOUND_ERROR);
        user.setStatus(status);
        boolean result = userService.updateById(user);
        return ResultUtils.success(result);
    }

    /**
     * 新增用户（E10：管理端「新增用户」原来只弹 toast，不落库）
     */
    @PostMapping("/add")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Long> addUser(@RequestBody AdminUserSaveRequest request) {
        validate(request, true);
        ThrowUtils.throwIf(
                userService.count(new QueryWrapper<User>().eq("phone", request.getPhone().trim())) > 0,
                ErrorCode.PARAMS_ERROR, "手机号已存在");

        User user = new User();
        user.setPhone(request.getPhone().trim());
        user.setEmail(StrUtil.blankToDefault(request.getEmail(), null));
        user.setPassword(BCrypt.hashpw(request.getPassword()));
        user.setNickname(StrUtil.blankToDefault(request.getNickname(), "用户" + user.getPhone().substring(7)));
        user.setAvatar(request.getAvatar());
        user.setRole(StrUtil.blankToDefault(request.getRole(), UserConstant.USER_ROLE));
        user.setStatus(request.getStatus() == null ? 1 : request.getStatus());
        boolean saved = userService.save(user);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "新增用户失败");
        log.info("管理端新增用户: id={}, phone={}, role={}", user.getId(), user.getPhone(), user.getRole());
        return ResultUtils.success(user.getId());
    }

    /**
     * 编辑用户（口令留空表示不修改）
     */
    @PostMapping("/update")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> updateUser(@RequestBody AdminUserSaveRequest request) {
        validate(request, false);
        User existing = userService.getById(request.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR, "用户不存在");

        if (StrUtil.isNotBlank(request.getPhone()) && !request.getPhone().trim().equals(existing.getPhone())) {
            ThrowUtils.throwIf(
                    userService.count(new QueryWrapper<User>().eq("phone", request.getPhone().trim())) > 0,
                    ErrorCode.PARAMS_ERROR, "手机号已存在");
            existing.setPhone(request.getPhone().trim());
        }
        if (StrUtil.isNotBlank(request.getEmail())) {
            existing.setEmail(request.getEmail().trim());
        }
        if (StrUtil.isNotBlank(request.getNickname())) {
            existing.setNickname(request.getNickname().trim());
        }
        if (request.getAvatar() != null) {
            existing.setAvatar(request.getAvatar());
        }
        if (StrUtil.isNotBlank(request.getPassword())) {
            existing.setPassword(BCrypt.hashpw(request.getPassword()));
        }
        if (StrUtil.isNotBlank(request.getRole())) {
            existing.setRole(request.getRole());
        }
        if (request.getStatus() != null) {
            existing.setStatus(request.getStatus());
        }
        boolean result = userService.updateById(existing);
        log.info("管理端编辑用户: id={}, role={}, status={}", existing.getId(), existing.getRole(), existing.getStatus());
        return ResultUtils.success(result);
    }

    private void validate(AdminUserSaveRequest request, boolean isCreate) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        if (isCreate) {
            ThrowUtils.throwIf(StrUtil.isBlank(request.getPhone()), ErrorCode.PARAMS_ERROR, "手机号不能为空");
            ThrowUtils.throwIf(!request.getPhone().trim().matches("^1\\d{10}$"),
                    ErrorCode.PARAMS_ERROR, "手机号格式不正确");
            ThrowUtils.throwIf(StrUtil.isBlank(request.getPassword()) || request.getPassword().length() < 6,
                    ErrorCode.PARAMS_ERROR, "密码至少 6 位");
        } else {
            ThrowUtils.throwIf(request.getId() == null, ErrorCode.PARAMS_ERROR, "用户ID不能为空");
        }
        if (StrUtil.isNotBlank(request.getRole())) {
            ThrowUtils.throwIf(!UserConstant.USER_ROLE.equals(request.getRole())
                            && !UserConstant.ADMIN_ROLE.equals(request.getRole()),
                    ErrorCode.PARAMS_ERROR, "角色只能是 user 或 admin");
        }
        if (request.getStatus() != null) {
            ThrowUtils.throwIf(request.getStatus() != 0 && request.getStatus() != 1,
                    ErrorCode.PARAMS_ERROR, "状态值无效");
        }
    }
}
