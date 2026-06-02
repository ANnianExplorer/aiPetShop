package com.petlumina.backend.controller;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.post.PostQueryRequest;
import com.petlumina.backend.model.dto.topic.TopicAddRequest;
import com.petlumina.backend.model.dto.topic.TopicEditRequest;
import com.petlumina.backend.model.dto.topic.TopicQueryRequest;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.Topic;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.PostVO;
import com.petlumina.backend.model.vo.TopicVO;
import com.petlumina.backend.model.vo.UserVO;
import com.petlumina.backend.service.PostService;
import com.petlumina.backend.service.TopicFollowService;
import com.petlumina.backend.service.TopicService;
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
 * 话题控制器
 */
@RestController
@RequestMapping("/api/v1/topic")
@Slf4j
public class TopicController {

    @Resource
    private TopicService topicService;

    @Resource
    private TopicFollowService topicFollowService;

    @Resource
    private PostService postService;

    @Resource
    private UserService userService;

    /**
     * 创建话题 (管理员)
     */
    @PostMapping("/add")
    @RateLimiter(key = "topic_add", time = 60, count = 5, message = "创建话题操作过于频繁")
    public BaseResponse<Long> addTopic(@RequestBody TopicAddRequest request,
                                       HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(StrUtil.isBlank(request.getTitle()), ErrorCode.PARAMS_ERROR, "话题标题不能为空");

        User loginUser = userService.getLoginUser(httpRequest);
        ThrowUtils.throwIf(!userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);

        Topic topic = new Topic();
        BeanUtils.copyProperties(request, topic);

        long topicId = topicService.addTopic(topic, loginUser);
        log.info("创建话题成功: topicId={}", topicId);
        return ResultUtils.success(topicId);
    }

    /**
     * 删除话题 (管理员)
     */
    @PostMapping("/delete")
    public BaseResponse<Boolean> deleteTopic(@RequestBody DeleteRequest request,
                                             HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = topicService.deleteTopic(request.getId(), loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 编辑话题 (管理员)
     */
    @PostMapping("/edit")
    public BaseResponse<Boolean> editTopic(@RequestBody TopicEditRequest request,
                                           HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);

        Topic topic = new Topic();
        BeanUtils.copyProperties(request, topic);

        boolean result = topicService.editTopic(topic, loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 获取话题详情 (VO)
     */
    @GetMapping("/get/vo")
    public BaseResponse<TopicVO> getTopicVO(@RequestParam long id,
                                            HttpServletRequest httpRequest) {
        Topic topic = topicService.getById(id);
        ThrowUtils.throwIf(topic == null, ErrorCode.NOT_FOUND_ERROR);
        TopicVO vo = TopicVO.objToVo(topic);

        // 填充关注状态
        try {
            User loginUser = userService.getLoginUser(httpRequest);
            vo.setIsFollowed(topicFollowService.isFollowed(loginUser.getId(), id) ? 1 : 0);
        } catch (com.petlumina.backend.exception.BusinessException ignored) {
            vo.setIsFollowed(0);
        }

        return ResultUtils.success(vo);
    }

    /**
     * 话题分页查询
     */
    @PostMapping("/list/page/vo")
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<TopicVO>> listTopicVOByPage(
            @RequestBody TopicQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);

        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Topic> queryWrapper = topicService.getQueryWrapper(request);
        Page<Topic> page = topicService.page(new Page<>(current, size), queryWrapper);

        Page<TopicVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(TopicVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    /**
     * 切换话题关注状态
     */
    @PostMapping("/follow/{id}")
    public BaseResponse<Boolean> toggleFollow(@PathVariable long id,
                                              HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        boolean isFollowed = topicService.toggleFollow(id, loginUser);
        return ResultUtils.success(isFollowed);
    }

    /**
     * 话题下帖子分页查询
     */
    @PostMapping("/list/page/vo/posts")
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<PostVO>> listTopicPosts(
            @RequestBody PostQueryRequest request,
            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(request.getTopicId() == null, ErrorCode.PARAMS_ERROR, "话题ID不能为空");

        long current = request.getCurrent();
        long size = request.getPageSize();

        // 通过 tags 字段查询话题下的帖子
        QueryWrapper<Post> queryWrapper = new QueryWrapper<>();
        queryWrapper.like("tags", "\"topic:" + request.getTopicId() + "\"");
        queryWrapper.orderByDesc("create_time");

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

        Page<PostVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(voList);
        return ResultUtils.success(voPage);
    }
}
