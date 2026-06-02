package com.petlumina.backend.service.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.PostMapper;
import com.petlumina.backend.model.dto.post.PostQueryRequest;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.FavoriteRecordService;
import com.petlumina.backend.service.LikeRecordService;
import com.petlumina.backend.service.PostService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;

/**
 * 帖子服务实现
 */
@Service
@Slf4j
public class PostServiceImpl extends ServiceImpl<PostMapper, Post>
        implements PostService {

    @Resource
    private UserService userService;

    @Resource
    private LikeRecordService likeRecordService;

    @Resource
    private FavoriteRecordService favoriteRecordService;

    private static final String TARGET_TYPE = "post";

    @Override
    public QueryWrapper<Post> getQueryWrapper(PostQueryRequest request) {
        QueryWrapper<Post> queryWrapper = new QueryWrapper<>();
        String category = request.getCategory();
        String searchText = request.getSearchText();

        queryWrapper.eq(StrUtil.isNotBlank(category), "category", category);
        if (StrUtil.isNotBlank(searchText)) {
            queryWrapper.and(w -> w
                    .like("content", searchText)
                    .or()
                    .like("tags", searchText));
        }
        queryWrapper.orderByDesc("create_time");
        return queryWrapper;
    }

    @Override
    public long addPost(Post post, User loginUser) {
        post.setAuthorId(loginUser.getId());
        post.setLikes(0);
        post.setComments(0);
        boolean saved = this.save(post);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "发布帖子失败");
        return post.getId();
    }

    @Override
    public boolean deletePost(long id, User loginUser) {
        Post post = this.getById(id);
        ThrowUtils.throwIf(post == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!post.getAuthorId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.removeById(id);
    }

    @Override
    public boolean editPost(Post post, User loginUser) {
        Post existing = this.getById(post.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!existing.getAuthorId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.updateById(post);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean toggleLike(long postId, User loginUser) {
        Post post = this.getById(postId);
        ThrowUtils.throwIf(post == null, ErrorCode.NOT_FOUND_ERROR, "帖子不存在");

        boolean isLiked = likeRecordService.toggleLike(loginUser.getId(), postId, TARGET_TYPE);
        // 更新帖子点赞数
        if (isLiked) {
            this.lambdaUpdate()
                    .eq(Post::getId, postId)
                    .setSql("likes = likes + 1")
                    .update();
        } else {
            this.lambdaUpdate()
                    .eq(Post::getId, postId)
                    .setSql("likes = GREATEST(likes - 1, 0)")
                    .update();
        }
        return isLiked;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean toggleFavorite(long postId, User loginUser) {
        Post post = this.getById(postId);
        ThrowUtils.throwIf(post == null, ErrorCode.NOT_FOUND_ERROR, "帖子不存在");

        return favoriteRecordService.toggleFavorite(loginUser.getId(), postId, TARGET_TYPE);
    }
}
