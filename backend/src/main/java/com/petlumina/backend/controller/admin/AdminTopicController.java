package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.topic.TopicAddRequest;
import com.petlumina.backend.model.dto.topic.TopicEditRequest;
import com.petlumina.backend.model.dto.topic.TopicQueryRequest;
import com.petlumina.backend.model.entity.Topic;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.TopicVO;
import com.petlumina.backend.service.user.TopicService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/admin/topic")
@Slf4j
public class AdminTopicController {

    @Resource
    private TopicService topicService;

    @Resource
    private UserService userService;

    @PostMapping("/list/page/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<TopicVO>> listTopicVOByPage(@RequestBody TopicQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Topic> queryWrapper = topicService.getQueryWrapper(request);
        Page<Topic> page = topicService.page(new Page<>(current, size), queryWrapper);
        Page<TopicVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(TopicVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    @PostMapping("/add")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Long> addTopic(@RequestBody TopicAddRequest request,
                                       javax.servlet.http.HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        Topic topic = new Topic();
        topic.setTitle(request.getTitle());
        topic.setDescription(request.getDescription());
        topic.setImage(request.getImage());
        topic.setCategory(request.getCategory());
        long id = topicService.addTopic(topic, loginUser);
        return ResultUtils.success(id);
    }

    @PostMapping("/edit")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> editTopic(@RequestBody TopicEditRequest request,
                                           javax.servlet.http.HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        Topic topic = new Topic();
        topic.setId(request.getId());
        topic.setTitle(request.getTitle());
        topic.setDescription(request.getDescription());
        topic.setImage(request.getImage());
        topic.setCategory(request.getCategory());
        boolean result = topicService.editTopic(topic, loginUser);
        return ResultUtils.success(result);
    }

    @PostMapping("/delete")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> deleteTopic(@RequestBody DeleteRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() <= 0, ErrorCode.PARAMS_ERROR);
        Topic topic = topicService.getById(request.getId());
        ThrowUtils.throwIf(topic == null, ErrorCode.NOT_FOUND_ERROR);
        boolean result = topicService.removeById(request.getId());
        return ResultUtils.success(result);
    }
}
