package com.petlumina.backend.service.user;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.entity.UserFollow;
import com.petlumina.backend.model.vo.UserVO;

/**
 * 用户关注服务接口
 */
public interface UserFollowService extends IService<UserFollow> {

    /**
     * 切换关注状态
     *
     * @return true=已关注, false=已取消关注
     */
    boolean toggleFollow(Long targetUserId, User loginUser);

    /**
     * 查询粉丝列表
     */
    IPage<UserVO> listFollowers(long current, long size, User loginUser);

    /**
     * 查询关注列表
     */
    IPage<UserVO> listFollowing(long current, long size, User loginUser);
}
