package com.petlumina.backend.controller;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.post.PostAddRequest;
import com.petlumina.backend.model.dto.post.PostEditRequest;
import com.petlumina.backend.model.dto.post.PostQueryRequest;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.PostVO;
import com.petlumina.backend.model.vo.UserVO;
import com.petlumina.backend.service.FavoriteRecordService;
import com.petlumina.backend.service.LikeRecordService;
import com.petlumina.backend.service.PostService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 帖子控制器
 */
@RestController
@RequestMapping("/api/v1/post")
@Slf4j
public class PostController {

    @Resource
    private PostService postService;

    @Resource
    private UserService userService;

    @Resource
    private LikeRecordService likeRecordService;

    @Resource
    private FavoriteRecordService favoriteRecordService;

    /**
     * 发布帖子
     */
    @PostMapping("/add")
    @RateLimiter(key = "post_add", time = 60, count = 5, message = "发布帖子操作过于频繁")
    public BaseResponse<Long> addPost(@RequestBody PostAddRequest request,
                                      HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(StrUtil.isBlank(request.getContent()), ErrorCode.PARAMS_ERROR, "帖子内容不能为空");

        User loginUser = userService.getLoginUser(httpRequest);

        Post post = new Post();
        BeanUtils.copyProperties(request, post);

        long postId = postService.addPost(post, loginUser);
        log.info("发布帖子成功: postId={}, userId={}", postId, loginUser.getId());
        return ResultUtils.success(postId);
    }

    /**
     * 删除帖子
     */
    @PostMapping("/delete")
    public BaseResponse<Boolean> deletePost(@RequestBody DeleteRequest request,
                                            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = postService.deletePost(request.getId(), loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 编辑帖子
     */
    @PostMapping("/edit")
    public BaseResponse<Boolean> editPost(@RequestBody PostEditRequest request,
                                          HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);

        Post post = new Post();
        BeanUtils.copyProperties(request, post);

        boolean result = postService.editPost(post, loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 获取帖子详情 (VO)
     */
    @GetMapping("/get/vo")
    public BaseResponse<PostVO> getPostVO(@RequestParam long id,
                                          HttpServletRequest httpRequest) {
        Post post = postService.getById(id);
        ThrowUtils.throwIf(post == null, ErrorCode.NOT_FOUND_ERROR);
        PostVO vo = PostVO.objToVo(post);

        // 填充作者信息
        User author = userService.getById(post.getAuthorId());
        if (author != null) {
            vo.setUser(UserVO.objToVo(author));
        }

        // 填充点赞/收藏状态 (登录用户)
        try {
            User loginUser = userService.getLoginUser(httpRequest);
            Map<Long, Boolean> likeMap = likeRecordService.getLikeMap(
                    loginUser.getId(), Set.of(id), "post");
            Map<Long, Boolean> favoriteMap = favoriteRecordService.getFavoriteMap(
                    loginUser.getId(), Set.of(id), "post");
            vo.setIsLiked(likeMap.getOrDefault(id, false) ? 1 : 0);
            vo.setIsFavorited(favoriteMap.getOrDefault(id, false) ? 1 : 0);
        } catch (com.petlumina.backend.exception.BusinessException ignored) {
            // 未登录不影响查看
            vo.setIsLiked(0);
            vo.setIsFavorited(0);
        }

        return ResultUtils.success(vo);
    }

    /**
     * 帖子分页查询
     */
    @PostMapping("/list/page/vo")
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<PostVO>> listPostVOByPage(
            @RequestBody PostQueryRequest request,
            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);

        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Post> queryWrapper = postService.getQueryWrapper(request);
        Page<Post> page = postService.page(new Page<>(current, size), queryWrapper);

        List<PostVO> voList = page.getRecords().stream().map(PostVO::objToVo).collect(Collectors.toList());

        // 批量填充作者信息
        Set<Long> authorIds = page.getRecords().stream().map(Post::getAuthorId).collect(Collectors.toSet());
        if (!authorIds.isEmpty()) {
            List<User> authors = userService.listByIds(authorIds);
            Map<Long, UserVO> authorMap = authors.stream()
                    .collect(Collectors.toMap(User::getId, UserVO::objToVo, (a, b) -> a));
            voList.forEach(vo -> vo.setUser(authorMap.get(vo.getAuthorId())));
        }

        // 批量填充点赞/收藏状态
        try {
            User loginUser = userService.getLoginUser(httpRequest);
            Set<Long> postIds = page.getRecords().stream().map(Post::getId).collect(Collectors.toSet());
            if (!postIds.isEmpty()) {
                Map<Long, Boolean> likeMap = likeRecordService.getLikeMap(loginUser.getId(), postIds, "post");
                Map<Long, Boolean> favoriteMap = favoriteRecordService.getFavoriteMap(loginUser.getId(), postIds, "post");
                voList.forEach(vo -> {
                    vo.setIsLiked(likeMap.getOrDefault(vo.getId(), false) ? 1 : 0);
                    vo.setIsFavorited(favoriteMap.getOrDefault(vo.getId(), false) ? 1 : 0);
                });
            }
        } catch (com.petlumina.backend.exception.BusinessException ignored) {
            voList.forEach(vo -> {
                vo.setIsLiked(0);
                vo.setIsFavorited(0);
            });
        }

        Page<PostVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(voList);
        return ResultUtils.success(voPage);
    }

    /**
     * 切换帖子点赞状态
     */
    @PostMapping("/like/{id}")
    public BaseResponse<Boolean> toggleLike(@PathVariable long id,
                                            HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        boolean isLiked = postService.toggleLike(id, loginUser);
        return ResultUtils.success(isLiked);
    }

    /**
     * 切换帖子收藏状态
     */
    @PostMapping("/favorite/{id}")
    public BaseResponse<Boolean> toggleFavorite(@PathVariable long id,
                                                HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        boolean isFavorited = postService.toggleFavorite(id, loginUser);
        return ResultUtils.success(isFavorited);
    }
}
