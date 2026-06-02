package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.comment.CommentQueryRequest;
import com.petlumina.backend.model.entity.Comment;
import com.petlumina.backend.model.vo.CommentVO;
import com.petlumina.backend.service.user.CommentService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/admin/comment")
@Slf4j
public class AdminCommentController {

    @Resource
    private CommentService commentService;

    @PostMapping("/list/page/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<CommentVO>> listCommentVOByPage(@RequestBody CommentQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Comment> queryWrapper = new QueryWrapper<>();
        if (request.getPostId() != null) {
            queryWrapper.eq("postId", request.getPostId());
        }
        queryWrapper.orderByDesc("createTime");
        Page<Comment> page = commentService.page(new Page<>(current, size), queryWrapper);
        Page<CommentVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(CommentVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    @PostMapping("/delete")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> deleteComment(@RequestBody DeleteRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() <= 0, ErrorCode.PARAMS_ERROR);
        Comment comment = commentService.getById(request.getId());
        ThrowUtils.throwIf(comment == null, ErrorCode.NOT_FOUND_ERROR);
        boolean result = commentService.removeById(request.getId());
        return ResultUtils.success(result);
    }
}
