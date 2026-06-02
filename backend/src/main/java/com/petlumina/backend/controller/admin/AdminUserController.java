package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
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
        List<Pet> pets = petService.list(new QueryWrapper<Pet>().eq("userId", id).eq("isDelete", 0));
        result.put("pets", pets.stream().map(PetVO::objToVo).collect(Collectors.toList()));

        // Recent posts
        List<Post> posts = postService.list(new QueryWrapper<Post>().eq("authorId", id).eq("isDelete", 0)
                .orderByDesc("createTime").last("LIMIT 10"));
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
}
