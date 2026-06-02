package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.post.PostQueryRequest;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.vo.PostVO;
import com.petlumina.backend.service.user.PostService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/admin/post")
@Slf4j
public class AdminPostController {

    @Resource
    private PostService postService;

    @PostMapping("/list/page/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<PostVO>> listPostVOByPage(@RequestBody PostQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Post> queryWrapper = postService.getQueryWrapper(request);
        Page<Post> page = postService.page(new Page<>(current, size), queryWrapper);
        Page<PostVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(PostVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    @PostMapping("/delete")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> deletePost(@RequestBody DeleteRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() <= 0, ErrorCode.PARAMS_ERROR);
        Post post = postService.getById(request.getId());
        ThrowUtils.throwIf(post == null, ErrorCode.NOT_FOUND_ERROR);
        boolean result = postService.removeById(request.getId());
        return ResultUtils.success(result);
    }
}
