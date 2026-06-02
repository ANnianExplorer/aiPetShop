package com.petlumina.backend.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.PageRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.UserVO;
import com.petlumina.backend.service.UserFollowService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;

/**
 * 关注系统控制器
 */
@RestController
@RequestMapping("/api/v1/follow")
@Slf4j
public class FollowController {

    @Resource
    private UserFollowService userFollowService;

    @Resource
    private UserService userService;

    /**
     * 切换关注/取消关注
     */
    @PostMapping("/{userId}")
    @RateLimiter(key = "follow", time = 60, count = 20, message = "关注操作过于频繁")
    public BaseResponse<Boolean> toggleFollow(@PathVariable long userId,
                                              HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        boolean isFollowed = userFollowService.toggleFollow(userId, loginUser);
        return ResultUtils.success(isFollowed);
    }

    /**
     * 查询粉丝列表
     */
    @PostMapping("/list/followers")
    public BaseResponse<IPage<UserVO>> listFollowers(@RequestBody PageRequest request,
                                                     HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        IPage<UserVO> result = userFollowService.listFollowers(request.getCurrent(), request.getPageSize(), loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 查询关注列表
     */
    @PostMapping("/list/following")
    public BaseResponse<IPage<UserVO>> listFollowing(@RequestBody PageRequest request,
                                                     HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        IPage<UserVO> result = userFollowService.listFollowing(request.getCurrent(), request.getPageSize(), loginUser);
        return ResultUtils.success(result);
    }
}
