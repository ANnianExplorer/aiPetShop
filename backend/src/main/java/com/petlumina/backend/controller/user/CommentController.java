package com.petlumina.backend.controller.user;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.comment.CommentAddRequest;
import com.petlumina.backend.model.dto.comment.CommentQueryRequest;
import com.petlumina.backend.model.entity.Comment;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.CommentVO;
import com.petlumina.backend.service.user.CommentService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;

/**
 * 评论控制器
 */
@RestController
@RequestMapping("/api/v1/comment")
@Slf4j
public class CommentController {

    @Resource
    private CommentService commentService;

    @Resource
    private UserService userService;

    /**
     * 发表评论
     */
    @PostMapping("/add")
    @RateLimiter(key = "comment_add", time = 60, count = 10, message = "评论操作过于频繁")
    public BaseResponse<Long> addComment(@RequestBody CommentAddRequest request,
                                         HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(request.getPostId() == null, ErrorCode.PARAMS_ERROR, "帖子ID不能为空");
        ThrowUtils.throwIf(request.getContent() == null || request.getContent().isBlank(),
                ErrorCode.PARAMS_ERROR, "评论内容不能为空");

        User loginUser = userService.getLoginUser(httpRequest);

        Comment comment = new Comment();
        comment.setPostId(request.getPostId());
        comment.setContent(request.getContent());
        comment.setParentId(request.getParentId());

        long commentId = commentService.addComment(comment, loginUser);
        log.info("评论成功: commentId={}, postId={}, userId={}", commentId, request.getPostId(), loginUser.getId());
        return ResultUtils.success(commentId);
    }

    /**
     * 删除评论
     */
    @PostMapping("/delete")
    public BaseResponse<Boolean> deleteComment(@RequestBody DeleteRequest request,
                                               HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = commentService.deleteComment(request.getId(), loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 评论分页查询 (含子评论树)
     */
    @PostMapping("/list/page/vo")
    public BaseResponse<IPage<CommentVO>> listCommentVOByPage(
            @RequestBody CommentQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        IPage<CommentVO> result = commentService.listCommentVOByPage(request);
        return ResultUtils.success(result);
    }
}
