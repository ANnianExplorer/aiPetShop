package com.petlumina.backend.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.CommentMapper;
import com.petlumina.backend.model.dto.comment.CommentQueryRequest;
import com.petlumina.backend.model.entity.Comment;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.CommentVO;
import com.petlumina.backend.model.vo.UserVO;
import com.petlumina.backend.service.CommentService;
import com.petlumina.backend.service.PostService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 评论服务实现
 */
@Service
@Slf4j
public class CommentServiceImpl extends ServiceImpl<CommentMapper, Comment>
        implements CommentService {

    @Resource
    private PostService postService;

    @Resource
    private UserService userService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public long addComment(Comment comment, User loginUser) {
        // 校验帖子存在
        Post post = postService.getById(comment.getPostId());
        ThrowUtils.throwIf(post == null, ErrorCode.NOT_FOUND_ERROR, "帖子不存在");

        // 校验父评论存在且属于同一帖子
        if (comment.getParentId() != null) {
            Comment parent = this.getById(comment.getParentId());
            ThrowUtils.throwIf(parent == null, ErrorCode.NOT_FOUND_ERROR, "父评论不存在");
            ThrowUtils.throwIf(!parent.getPostId().equals(comment.getPostId()),
                    ErrorCode.PARAMS_ERROR, "父评论不属于该帖子");
        }

        comment.setUserId(loginUser.getId());
        comment.setLikes(0);
        boolean saved = this.save(comment);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "评论失败");

        // 更新帖子评论数
        postService.lambdaUpdate()
                .eq(Post::getId, comment.getPostId())
                .setSql("comments = comments + 1")
                .update();

        return comment.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteComment(long id, User loginUser) {
        Comment comment = this.getById(id);
        ThrowUtils.throwIf(comment == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!comment.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);

        boolean removed = this.removeById(id);
        if (removed) {
            // 更新帖子评论数
            postService.lambdaUpdate()
                    .eq(Post::getId, comment.getPostId())
                    .setSql("comments = GREATEST(comments - 1, 0)")
                    .update();
        }
        return removed;
    }

    @Override
    public IPage<CommentVO> listCommentVOByPage(CommentQueryRequest request) {
        Long postId = request.getPostId();
        ThrowUtils.throwIf(postId == null, ErrorCode.PARAMS_ERROR, "帖子ID不能为空");

        long current = request.getCurrent();
        long size = request.getPageSize();

        // 1. 查询一级评论 (parentId IS NULL)
        QueryWrapper<Comment> topWrapper = new QueryWrapper<>();
        topWrapper.eq("post_id", postId);
        topWrapper.isNull("parent_id");
        topWrapper.orderByDesc("create_time");
        Page<Comment> topPage = this.page(new Page<>(current, size), topWrapper);

        if (topPage.getRecords().isEmpty()) {
            Page<CommentVO> emptyPage = new Page<>(current, size, 0);
            emptyPage.setRecords(new ArrayList<>());
            return emptyPage;
        }

        // 2. 批量查询子评论
        Set<Long> topIds = topPage.getRecords().stream().map(Comment::getId).collect(Collectors.toSet());
        QueryWrapper<Comment> childWrapper = new QueryWrapper<>();
        childWrapper.eq("post_id", postId);
        childWrapper.in("parent_id", topIds);
        childWrapper.orderByAsc("create_time");
        List<Comment> children = this.list(childWrapper);

        // 3. 按 parentId 分组
        Map<Long, List<Comment>> childrenMap = children.stream()
                .collect(Collectors.groupingBy(Comment::getParentId));

        // 4. 批量查询用户信息
        Set<Long> userIds = new HashSet<>();
        topPage.getRecords().forEach(c -> userIds.add(c.getUserId()));
        children.forEach(c -> userIds.add(c.getUserId()));

        Map<Long, UserVO> userMap = new HashMap<>();
        if (!userIds.isEmpty()) {
            List<User> users = userService.listByIds(userIds);
            userMap = users.stream()
                    .collect(Collectors.toMap(User::getId, UserVO::objToVo, (a, b) -> a));
        }

        // 5. 构建评论树
        Map<Long, UserVO> finalUserMap = userMap;
        List<CommentVO> voList = topPage.getRecords().stream().map(top -> {
            CommentVO vo = CommentVO.objToVo(top);
            vo.setUser(finalUserMap.get(top.getUserId()));

            List<Comment> childList = childrenMap.getOrDefault(top.getId(), new ArrayList<>());
            List<CommentVO> childVOs = childList.stream().map(child -> {
                CommentVO childVO = CommentVO.objToVo(child);
                childVO.setUser(finalUserMap.get(child.getUserId()));
                return childVO;
            }).collect(Collectors.toList());
            vo.setChildren(childVOs);
            return vo;
        }).collect(Collectors.toList());

        Page<CommentVO> voPage = new Page<>(current, size, topPage.getTotal());
        voPage.setRecords(voList);
        return voPage;
    }
}
