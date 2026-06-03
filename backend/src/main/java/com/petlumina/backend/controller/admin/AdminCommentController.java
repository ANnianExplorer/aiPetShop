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
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.CommentVO;
import com.petlumina.backend.model.vo.UserVO;
import com.petlumina.backend.service.user.CommentService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/admin/comment")
@Slf4j
public class AdminCommentController {

    @Resource
    private CommentService commentService;

    @Resource
    private UserService userService;

    @PostMapping("/list/page/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<CommentVO>> listCommentVOByPage(@RequestBody CommentQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Comment> queryWrapper = new QueryWrapper<>();
        if (request.getPostId() != null) {
            queryWrapper.eq("post_id", request.getPostId());
        }
        if (request.getSearchText() != null && !request.getSearchText().isEmpty()) {
            queryWrapper.like("content", request.getSearchText());
        }
        queryWrapper.orderByDesc("create_time");
        Page<Comment> page = commentService.page(new Page<>(current, size), queryWrapper);

        List<CommentVO> voList = page.getRecords().stream().map(CommentVO::objToVo).collect(Collectors.toList());

        // 批量填充用户信息
        Set<Long> userIds = page.getRecords().stream().map(Comment::getUserId).collect(Collectors.toSet());
        if (!userIds.isEmpty()) {
            List<User> users = userService.listByIds(userIds);
            Map<Long, UserVO> userMap = users.stream()
                    .collect(Collectors.toMap(User::getId, UserVO::objToVo, (a, b) -> a));
            voList.forEach(vo -> vo.setUser(userMap.get(vo.getUserId())));
        }

        Page<CommentVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(voList);
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
