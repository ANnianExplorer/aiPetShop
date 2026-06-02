package com.petlumina.backend.service.user;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.comment.CommentQueryRequest;
import com.petlumina.backend.model.entity.Comment;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.CommentVO;

/**
 * 评论服务接口
 */
public interface CommentService extends IService<Comment> {

    /**
     * 添加评论
     */
    long addComment(Comment comment, User loginUser);

    /**
     * 删除评论 (校验权限)
     */
    boolean deleteComment(long id, User loginUser);

    /**
     * 分页查询评论 (含子评论树)
     */
    IPage<CommentVO> listCommentVOByPage(CommentQueryRequest request);
}
