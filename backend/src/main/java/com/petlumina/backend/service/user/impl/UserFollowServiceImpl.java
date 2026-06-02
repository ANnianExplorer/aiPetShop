package com.petlumina.backend.service.user.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.UserFollowMapper;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.entity.UserFollow;
import com.petlumina.backend.model.vo.UserVO;
import com.petlumina.backend.service.user.UserFollowService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 用户关注服务实现
 */
@Service
@Slf4j
public class UserFollowServiceImpl extends ServiceImpl<UserFollowMapper, UserFollow>
        implements UserFollowService {

    @Resource
    private UserService userService;

    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public boolean toggleFollow(Long targetUserId, User loginUser) {
        Long currentUserId = loginUser.getId();
        ThrowUtils.throwIf(currentUserId.equals(targetUserId), ErrorCode.PARAMS_ERROR, "不能关注自己");

        // 验证目标用户存在
        User targetUser = userService.getById(targetUserId);
        ThrowUtils.throwIf(targetUser == null, ErrorCode.NOT_FOUND_ERROR, "用户不存在");

        QueryWrapper<UserFollow> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", currentUserId);
        queryWrapper.eq("follow_user_id", targetUserId);

        UserFollow existing = this.getOne(queryWrapper);
        if (existing != null) {
            this.removeById(existing.getId());
            return false;
        } else {
            UserFollow follow = new UserFollow();
            follow.setUserId(currentUserId);
            follow.setFollowUserId(targetUserId);
            this.save(follow);
            return true;
        }
    }

    @Override
    public IPage<UserVO> listFollowers(long current, long size, User loginUser) {
        // 查询谁关注了我
        QueryWrapper<UserFollow> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("follow_user_id", loginUser.getId());
        queryWrapper.orderByDesc("create_time");

        Page<UserFollow> page = this.page(new Page<>(current, size), queryWrapper);

        // 批量查询用户信息
        Set<Long> userIds = page.getRecords().stream().map(UserFollow::getUserId).collect(Collectors.toSet());
        List<UserVO> voList = userIds.isEmpty() ? new ArrayList<>() :
                userService.listByIds(userIds).stream()
                        .map(UserVO::objToVo)
                        .collect(Collectors.toList());

        Page<UserVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(voList);
        return voPage;
    }

    @Override
    public IPage<UserVO> listFollowing(long current, long size, User loginUser) {
        // 查询我关注了谁
        QueryWrapper<UserFollow> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", loginUser.getId());
        queryWrapper.orderByDesc("create_time");

        Page<UserFollow> page = this.page(new Page<>(current, size), queryWrapper);

        // 批量查询用户信息
        Set<Long> userIds = page.getRecords().stream().map(UserFollow::getFollowUserId).collect(Collectors.toSet());
        List<UserVO> voList = userIds.isEmpty() ? new ArrayList<>() :
                userService.listByIds(userIds).stream()
                        .map(UserVO::objToVo)
                        .collect(Collectors.toList());

        Page<UserVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(voList);
        return voPage;
    }
}
