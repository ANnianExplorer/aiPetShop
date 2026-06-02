package com.petlumina.backend.service.admin.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.petlumina.backend.model.entity.*;
import com.petlumina.backend.service.admin.DashboardService;
import com.petlumina.backend.service.user.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.stream.Collectors;

@Service
@Slf4j
public class DashboardServiceImpl implements DashboardService {

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

    @Override
    public Map<String, Object> getStats() {
        Map<String, Object> stats = new HashMap<>();

        // User stats
        long userTotal = userService.count();
        stats.put("userTotal", userTotal);

        // Pet stats
        long petTotal = petService.count();
        stats.put("petTotal", petTotal);

        // Post stats
        long postTotal = postService.count();
        stats.put("postTotal", postTotal);

        // Comment stats
        long commentTotal = commentService.count();
        stats.put("commentTotal", commentTotal);

        // Topic stats
        long topicTotal = topicService.count();
        stats.put("topicTotal", topicTotal);

        // Log stats
        long logTotal = logEntryService.count();
        stats.put("logTotal", logTotal);

        // Pet type distribution
        List<Pet> allPets = petService.list();
        Map<String, Long> petTypeDistribution = allPets.stream()
                .collect(Collectors.groupingBy(pet -> pet.getType() != null ? pet.getType() : "其他", Collectors.counting()));
        stats.put("petTypeDistribution", petTypeDistribution);

        // Active user trend (last 7 days - based on post creation)
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        List<Map<String, Object>> activeUserTrend = new ArrayList<>();
        Calendar cal = Calendar.getInstance();
        for (int i = 6; i >= 0; i--) {
            Calendar dayCal = Calendar.getInstance();
            dayCal.add(Calendar.DAY_OF_MONTH, -i);
            String dateStr = sdf.format(dayCal.getTime());

            // Count posts created on this day as activity proxy
            long dailyPosts = postService.count(new QueryWrapper<Post>()
                    .ge("createTime", dateStr + " 00:00:00")
                    .lt("createTime", dateStr + " 23:59:59"));

            Map<String, Object> dayData = new HashMap<>();
            dayData.put("date", dateStr);
            dayData.put("count", dailyPosts);
            activeUserTrend.add(dayData);
        }
        stats.put("activeUserTrend", activeUserTrend);

        // Recent posts (top 5)
        List<Post> recentPosts = postService.list(new QueryWrapper<Post>()
                .eq("isDelete", 0)
                .orderByDesc("createTime")
                .last("LIMIT 5"));
        List<Map<String, Object>> hotPosts = recentPosts.stream().map(post -> {
            Map<String, Object> item = new HashMap<>();
            item.put("id", post.getId());
            item.put("content", post.getContent() != null && post.getContent().length() > 50
                    ? post.getContent().substring(0, 50) + "..." : post.getContent());
            item.put("likes", post.getLikes());
            item.put("comments", post.getComments());
            User author = userService.getById(post.getAuthorId());
            item.put("author", author != null ? author.getNickname() : "未知");
            item.put("createTime", post.getCreateTime());
            return item;
        }).collect(Collectors.toList());
        stats.put("hotPosts", hotPosts);

        // Recent topics (top 5)
        List<Topic> recentTopics = topicService.list(new QueryWrapper<Topic>()
                .eq("isDelete", 0)
                .orderByDesc("createTime")
                .last("LIMIT 5"));
        List<Map<String, Object>> hotTopics = recentTopics.stream().map(topic -> {
            Map<String, Object> item = new HashMap<>();
            item.put("id", topic.getId());
            item.put("title", topic.getTitle());
            item.put("postCount", topic.getPostCount());
            item.put("followerCount", topic.getFollowerCount());
            item.put("createTime", topic.getCreateTime());
            return item;
        }).collect(Collectors.toList());
        stats.put("hotTopics", hotTopics);

        return stats;
    }
}
