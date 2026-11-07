package com.petlumina.backend.service.admin.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.petlumina.backend.mapper.PetMapper;
import com.petlumina.backend.mapper.PostMapper;
import com.petlumina.backend.model.dto.dashboard.DailyCount;
import com.petlumina.backend.model.dto.dashboard.TypeCount;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.Topic;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.admin.DashboardService;
import com.petlumina.backend.service.user.CommentService;
import com.petlumina.backend.service.user.LogEntryService;
import com.petlumina.backend.service.user.PetService;
import com.petlumina.backend.service.user.PostService;
import com.petlumina.backend.service.user.TopicService;
import com.petlumina.backend.service.user.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
@Slf4j
public class DashboardServiceImpl implements DashboardService {

    /** 趋势窗口：含今天在内共 7 天 */
    private static final int TREND_DAYS = 7;

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    @Resource
    private UserService userService;

    @Resource
    private PetService petService;

    @Resource
    private PostService postService;

    @Resource
    private CommentService commentService;

    @Resource
    private TopicService topicService;

    @Resource
    private LogEntryService logEntryService;

    @Resource
    private PostMapper postMapper;

    @Resource
    private PetMapper petMapper;

    @Override
    public Map<String, Object> getStats() {
        Map<String, Object> stats = new HashMap<>();

        // 各表总量
        stats.put("userTotal", userService.count());
        stats.put("petTotal", petService.count());
        stats.put("postTotal", postService.count());
        stats.put("commentTotal", commentService.count());
        stats.put("topicTotal", topicService.count());
        stats.put("logTotal", logEntryService.count());

        stats.put("petTypeDistribution", petTypeDistribution());
        stats.put("activeUserTrend", activeUserTrend());
        stats.put("hotPosts", recentPosts());
        stats.put("hotTopics", recentTopics());

        return stats;
    }

    /**
     * 宠物类型分布：一条 GROUP BY，不再把整张宠物表捞进内存分组。
     */
    private Map<String, Long> petTypeDistribution() {
        Map<String, Long> distribution = new HashMap<>();
        List<TypeCount> rows = petMapper.countByType();
        if (rows == null) {
            return distribution;
        }
        for (TypeCount row : rows) {
            String type = row.getType() != null ? row.getType() : "其他";
            long total = row.getTotal() != null ? row.getTotal() : 0L;
            distribution.merge(type, total, Long::sum);
        }
        return distribution;
    }

    /**
     * 近 7 天发帖趋势：一条 GROUP BY 取回有数据的天，再在内存里补 0。
     *
     * <p>旧实现是在 for 循环里每天发一次 count(*)，7 天就是 7 次往返；
     * 而且 `< 23:59:59` 会漏掉当天最后一秒内的帖子。</p>
     */
    private List<Map<String, Object>> activeUserTrend() {
        LocalDate today = LocalDate.now();
        LocalDate start = today.minusDays(TREND_DAYS - 1L);

        Map<String, Long> counts = new HashMap<>();
        List<DailyCount> rows = postMapper.countByDay(start.format(DAY) + " 00:00:00");
        if (rows != null) {
            for (DailyCount row : rows) {
                if (row.getDay() != null) {
                    counts.put(row.getDay(), row.getTotal() != null ? row.getTotal() : 0L);
                }
            }
        }

        List<Map<String, Object>> trend = new ArrayList<>(TREND_DAYS);
        for (int i = 0; i < TREND_DAYS; i++) {
            String day = start.plusDays(i).format(DAY);
            Map<String, Object> item = new HashMap<>();
            item.put("date", day);
            item.put("count", counts.getOrDefault(day, 0L));
            trend.add(item);
        }
        return trend;
    }

    /**
     * 最近 5 条帖子：作者昵称一次性批量查，避免每条帖子一次 getById。
     */
    private List<Map<String, Object>> recentPosts() {
        List<Post> recentPosts = postService.list(new QueryWrapper<Post>()
                .eq("is_delete", 0)
                .orderByDesc("create_time")
                .last("LIMIT 5"));

        Map<Long, String> nicknames = authorNicknames(recentPosts);

        return recentPosts.stream().map(post -> {
            Map<String, Object> item = new HashMap<>();
            item.put("id", post.getId());
            item.put("content", post.getContent() != null && post.getContent().length() > 50
                    ? post.getContent().substring(0, 50) + "..." : post.getContent());
            item.put("likes", post.getLikes());
            item.put("comments", post.getComments());
            item.put("author", nicknames.getOrDefault(post.getAuthorId(), "未知"));
            item.put("createTime", post.getCreateTime());
            return item;
        }).collect(Collectors.toList());
    }

    /**
     * 批量取作者昵称；帖子为空或作者 id 全空时不查库。
     */
    private Map<Long, String> authorNicknames(List<Post> posts) {
        if (posts == null || posts.isEmpty()) {
            return Collections.emptyMap();
        }
        List<Long> authorIds = posts.stream()
                .map(Post::getAuthorId)
                .filter(Objects::nonNull)
                .distinct()
                .collect(Collectors.toList());
        if (authorIds.isEmpty()) {
            return Collections.emptyMap();
        }
        List<User> authors = userService.listByIds(authorIds);
        Map<Long, String> nicknames = new HashMap<>(authors.size());
        for (User author : authors) {
            if (author != null && author.getId() != null) {
                nicknames.put(author.getId(), author.getNickname() != null ? author.getNickname() : "未知");
            }
        }
        return nicknames;
    }

    /**
     * 最近 5 个话题。
     */
    private List<Map<String, Object>> recentTopics() {
        List<Topic> recentTopics = topicService.list(new QueryWrapper<Topic>()
                .eq("is_delete", 0)
                .orderByDesc("create_time")
                .last("LIMIT 5"));
        return recentTopics.stream().map(topic -> {
            Map<String, Object> item = new HashMap<>();
            item.put("id", topic.getId());
            item.put("title", topic.getTitle());
            item.put("postCount", topic.getPostCount());
            item.put("followerCount", topic.getFollowerCount());
            item.put("createTime", topic.getCreateTime());
            return item;
        }).collect(Collectors.toList());
    }
}
