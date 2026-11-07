package com.petlumina.backend.service.user.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.mapper.PostMapper;
import com.petlumina.backend.mapper.TopicMapper;
import com.petlumina.backend.model.dto.post.PostQueryRequest;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.Topic;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.user.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/**
 * E12：帖子与话题的关联改成显式 topic_id 后，落库前必须校验话题存在、
 * 老客户端塞进 tags 的 "topic:id" 必须清掉、查询按列过滤而不是拼字符串。
 */
@ExtendWith(MockitoExtension.class)
class PostServiceImplTest {

    @Mock
    private UserService userService;

    @Mock
    private TopicMapper topicMapper;

    @Mock
    private PostMapper postMapper;

    private PostServiceImpl postService;

    @BeforeEach
    void setUp() {
        postService = new PostServiceImpl();
        ReflectionTestUtils.setField(postService, "userService", userService);
        ReflectionTestUtils.setField(postService, "topicMapper", topicMapper);
        ReflectionTestUtils.setField(postService, "baseMapper", postMapper);
    }

    private User loginUser() {
        User user = new User();
        user.setId(1001L);
        return user;
    }

    @Test
    void addPostRejectsMissingTopic() {
        when(topicMapper.selectById(404L)).thenReturn(null);
        Post post = new Post();
        post.setContent("带话题的帖子");
        post.setTopicId(404L);

        BusinessException ex = assertThrows(BusinessException.class, () -> postService.addPost(post, loginUser()));
        assertEquals("话题不存在", ex.getMessage());
        assertEquals(40400, ex.getCode());
    }

    @Test
    void addPostKeepsExistingTopicAndStripsLegacyTag() {
        Topic topic = new Topic();
        topic.setId(7L);
        when(topicMapper.selectById(7L)).thenReturn(topic);
        when(postMapper.insert(any(Post.class))).thenAnswer(invocation -> {
            Post saved = invocation.getArgument(0);
            saved.setId(7001L);
            return 1;
        });

        Post post = new Post();
        post.setContent("带话题的帖子");
        post.setTopicId(7L);
        post.setTags("[\"topic:7\",\"猫咪\"]");

        postService.addPost(post, loginUser());

        assertEquals(7L, post.getTopicId());
        assertEquals(1001L, post.getAuthorId());
        assertEquals("[\"猫咪\"]", post.getTags());
        assertNotNull(post.getLikes());
        assertEquals(Integer.valueOf(0), post.getLikes());
    }

    @Test
    void stripTopicTagsKeepsOtherTags() {
        Object kept = ReflectionTestUtils.invokeMethod(PostServiceImpl.class, "stripTopicTags", "[\"topic:1\",\"cat\",\"topic:2\"]");
        assertEquals("[\"cat\"]", kept);
    }

    @Test
    void stripTopicTagsLeavesInvalidJsonUntouched() {
        Object kept = ReflectionTestUtils.invokeMethod(PostServiceImpl.class, "stripTopicTags", "not-json");
        assertEquals("not-json", kept);
        Object blank = ReflectionTestUtils.invokeMethod(PostServiceImpl.class, "stripTopicTags", new Object[]{null});
        assertNull(blank);
    }

    @Test
    void getQueryWrapperFiltersByTopicColumn() {
        PostQueryRequest request = new PostQueryRequest();
        request.setTopicId(42L);

        QueryWrapper<Post> wrapper = postService.getQueryWrapper(request);

        // 查询条件必须落在 topic_id 列上，而不是拿 tags 做字符串匹配
        assertTrue(wrapper.getSqlSegment().contains("topic_id"));
        assertTrue(wrapper.getParamNameValuePairs().containsValue(42L));
    }
}
