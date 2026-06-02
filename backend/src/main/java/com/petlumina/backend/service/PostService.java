package com.petlumina.backend.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.post.PostQueryRequest;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.User;

/**
 * 帖子服务接口
 */
public interface PostService extends IService<Post> {

    /**
     * 构建查询条件
     */
    QueryWrapper<Post> getQueryWrapper(PostQueryRequest request);

    /**
     * 添加帖子
     */
    long addPost(Post post, User loginUser);

    /**
     * 删除帖子 (校验权限)
     */
    boolean deletePost(long id, User loginUser);

    /**
     * 编辑帖子 (校验权限)
     */
    boolean editPost(Post post, User loginUser);

    /**
     * 切换点赞状态
     *
     * @return true=已点赞, false=已取消点赞
     */
    boolean toggleLike(long postId, User loginUser);

    /**
     * 切换收藏状态
     *
     * @return true=已收藏, false=已取消收藏
     */
    boolean toggleFavorite(long postId, User loginUser);
}
