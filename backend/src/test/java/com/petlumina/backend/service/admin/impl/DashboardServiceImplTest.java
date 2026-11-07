package com.petlumina.backend.service.admin.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.petlumina.backend.mapper.PetMapper;
import com.petlumina.backend.mapper.PostMapper;
import com.petlumina.backend.model.dto.dashboard.DailyCount;
import com.petlumina.backend.model.dto.dashboard.TypeCount;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.user.CommentService;
import com.petlumina.backend.service.user.LogEntryService;
import com.petlumina.backend.service.user.PetService;
import com.petlumina.backend.service.user.PostService;
import com.petlumina.backend.service.user.TopicService;
import com.petlumina.backend.service.user.UserService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 仪表盘聚合逻辑的单元测试：重点是"一条 SQL 代替 7 次循环"和"作者批量查"，
 * 不是把 Mock 出来的数字再念一遍。
 */
@ExtendWith(MockitoExtension.class)
class DashboardServiceImplTest {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    @Mock
    private UserService userService;
    @Mock
    private PetService petService;
    @Mock
    private PostService postService;
    @Mock
    private CommentService commentService;
    @Mock
    private TopicService topicService;
    @Mock
    private LogEntryService logEntryService;
    @Mock
    private PostMapper postMapper;
    @Mock
    private PetMapper petMapper;

    @InjectMocks
    private DashboardServiceImpl dashboardService;

    @Test
    @DisplayName("7 天趋势：只查一次聚合，缺的日期补 0，日期升序")
    @SuppressWarnings("unchecked")
    void trendUsesSingleAggregateAndZeroFills() {
        LocalDate today = LocalDate.now();
        DailyCount twoDaysAgo = daily(today.minusDays(2), 3L);
        DailyCount todayRow = daily(today, 1L);
        when(postMapper.countByDay(anyString())).thenReturn(Arrays.asList(twoDaysAgo, todayRow));
        when(postService.list(any(Wrapper.class))).thenReturn(Collections.emptyList());
        when(topicService.list(any(Wrapper.class))).thenReturn(Collections.emptyList());
        when(petMapper.countByType()).thenReturn(Collections.emptyList());

        Map<String, Object> stats = dashboardService.getStats();

        List<Map<String, Object>> trend = (List<Map<String, Object>>) stats.get("activeUserTrend");
        assertThat(trend).hasSize(7);
        assertThat(trend.get(0).get("date")).isEqualTo(today.minusDays(6).format(DAY));
        assertThat(trend.get(6).get("date")).isEqualTo(today.format(DAY));
        // 缺数据的两天是 0，有数据的两天按库里返回的值
        assertThat(trend.get(4).get("count")).isEqualTo(3L);
        assertThat(trend.get(5).get("count")).isEqualTo(0L);
        assertThat(trend.get(6).get("count")).isEqualTo(1L);
        // 关键：只打了一次数据库，而不是 7 次 count
        verify(postMapper, times(1)).countByDay(anyString());
    }

    @Test
    @DisplayName("宠物类型分布：null 归到「其他」，同类型合并计数")
    void petTypeDistributionMergesNullAndDuplicates() {
        when(postMapper.countByDay(anyString())).thenReturn(Collections.emptyList());
        when(postService.list(any(Wrapper.class))).thenReturn(Collections.emptyList());
        when(topicService.list(any(Wrapper.class))).thenReturn(Collections.emptyList());
        when(petMapper.countByType()).thenReturn(Arrays.asList(
                type("cat", 2L),
                type("cat", 1L),
                type(null, 4L)
        ));

        Map<String, Object> stats = dashboardService.getStats();

        @SuppressWarnings("unchecked")
        Map<String, Long> distribution = (Map<String, Long>) stats.get("petTypeDistribution");
        assertThat(distribution).containsEntry("cat", 3L).containsEntry("其他", 4L);
    }

    @Test
    @DisplayName("热门帖作者：一次批量查，不再逐条 getById")
    void hotPostsBatchLoadAuthors() {
        Post first = post(11L, 1L, "第一条");
        Post second = post(12L, 2L, "第二条");
        when(postMapper.countByDay(anyString())).thenReturn(Collections.emptyList());
        when(postService.list(any(Wrapper.class))).thenReturn(Arrays.asList(first, second));
        when(topicService.list(any(Wrapper.class))).thenReturn(Collections.emptyList());
        when(petMapper.countByType()).thenReturn(Collections.emptyList());
        when(userService.listByIds(anyList())).thenReturn(Arrays.asList(
                user(1L, "小月亮"),
                user(2L, "阿团")
        ));

        Map<String, Object> stats = dashboardService.getStats();

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> hotPosts = (List<Map<String, Object>>) stats.get("hotPosts");
        assertThat(hotPosts).hasSize(2);
        assertThat(hotPosts.get(0).get("author")).isEqualTo("小月亮");
        assertThat(hotPosts.get(1).get("author")).isEqualTo("阿团");
        verify(userService, times(1)).listByIds(anyList());
        verify(userService, never()).getById(any());
    }

    private static DailyCount daily(LocalDate date, long total) {
        DailyCount row = new DailyCount();
        row.setDay(date.format(DAY));
        row.setTotal(total);
        return row;
    }

    private static TypeCount type(String type, long total) {
        TypeCount row = new TypeCount();
        row.setType(type);
        row.setTotal(total);
        return row;
    }

    private static Post post(Long id, Long authorId, String content) {
        Post post = new Post();
        post.setId(id);
        post.setAuthorId(authorId);
        post.setContent(content);
        post.setLikes(1);
        post.setComments(0);
        return post;
    }

    private static User user(Long id, String nickname) {
        User user = new User();
        user.setId(id);
        user.setNickname(nickname);
        return user;
    }
}
