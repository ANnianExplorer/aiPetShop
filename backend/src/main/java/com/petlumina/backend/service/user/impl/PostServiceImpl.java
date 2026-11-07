package com.petlumina.backend.service.user.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.PostMapper;
import com.petlumina.backend.model.dto.post.PostQueryRequest;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.user.FavoriteRecordService;
import com.petlumina.backend.service.user.LikeRecordService;
import com.petlumina.backend.service.user.PostService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.SortUtils;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 帖子服务实现
 */
@Service
@Slf4j
public class PostServiceImpl extends ServiceImpl<PostMapper, Post>
        implements PostService {

    @Resource
    private UserService userService;

    @Resource
    private LikeRecordService likeRecordService;

    @Resource
    private FavoriteRecordService favoriteRecordService;

    @Resource
    private com.petlumina.backend.mapper.TopicMapper topicMapper;

    private static final String TARGET_TYPE = "post";

    /** 旧数据里话题藏在 tags 的 "topic:<id>" 元素里，统一在这里清掉（E12） */
    private static String stripTopicTags(String tags) {
        if (StrUtil.isBlank(tags)) {
            return tags;
        }
        try {
            cn.hutool.json.JSONArray arr = cn.hutool.json.JSONUtil.parseArray(tags);
            java.util.List<String> kept = new java.util.ArrayList<>();
            for (Object item : arr) {
                String text = String.valueOf(item);
                if (!text.startsWith("topic:")) {
                    kept.add(text);
                }
            }
            return cn.hutool.json.JSONUtil.toJsonStr(kept);
        } catch (Exception e) {
            log.warn("tags 不是合法 JSON 数组，原样保留: {}", tags);
            return tags;
        }
    }

    @Override
    public QueryWrapper<Post> getQueryWrapper(PostQueryRequest request) {
        QueryWrapper<Post> queryWrapper = new QueryWrapper<>();
        String category = request.getCategory();
        String searchText = request.getSearchText();
        String authorName = request.getAuthorName();

        queryWrapper.eq(StrUtil.isNotBlank(category), "category", category);
        if (StrUtil.isNotBlank(searchText)) {
            queryWrapper.and(w -> w
                    .like("content", searchText)
                    .or()
                    .like("tags", searchText));
        }
        // 话题归属走显式列，不再依赖 tags 里的字符串约定（E12）
        if (request.getTopicId() != null) {
            queryWrapper.eq("topic_id", request.getTopicId());
        }
        // 按作者昵称筛选
        if (StrUtil.isNotBlank(authorName)) {
            List<User> authors = userService.list(
                    new QueryWrapper<User>().like("nickname", authorName).select("id"));
            if (!authors.isEmpty()) {
                queryWrapper.in("author_id", authors.stream().map(User::getId).collect(Collectors.toList()));
            } else {
                // 没有匹配的作者，返回空结果
                queryWrapper.eq("author_id", -1);
            }
        }
        // 接口字段白名单：sortField 只认这些，列名不来自用户输入
        SortUtils.apply(queryWrapper, request, java.util.Map.of(
                "createTime", "create_time", "likes", "likes", "comments", "comments"), "create_time");
        return queryWrapper;
    }

    @Override
    public long addPost(Post post, User loginUser) {
        post.setAuthorId(loginUser.getId());
        post.setLikes(0);
        post.setComments(0);
        // 话题必须先存在，否则会写出一条永远挂不上话题的帖子（E12）
        if (post.getTopicId() != null) {
            com.petlumina.backend.model.entity.Topic topic = topicMapper.selectById(post.getTopicId());
            ThrowUtils.throwIf(topic == null, ErrorCode.NOT_FOUND_ERROR, "话题不存在");
        }
        // tags 字段如果是普通字符串，转为 JSON 数组格式
        if (StrUtil.isNotBlank(post.getTags()) && !post.getTags().startsWith("[")) {
            String[] tagArr = post.getTags().split("[,，]");
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < tagArr.length; i++) {
                if (i > 0) sb.append(",");
                sb.append("\"").append(tagArr[i].trim()).append("\"");
            }
            sb.append("]");
            post.setTags(sb.toString());
        }
        // 客户端的旧版本可能还在往 tags 里塞 "topic:<id>"，落库前统一清掉
        post.setTags(stripTopicTags(post.getTags()));
        // images 字段同理
        if (StrUtil.isNotBlank(post.getImages()) && !post.getImages().startsWith("[")) {
            String[] imgArr = post.getImages().split(",");
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < imgArr.length; i++) {
                if (i > 0) sb.append(",");
                sb.append("\"").append(imgArr[i].trim()).append("\"");
            }
            sb.append("]");
            post.setImages(sb.toString());
        }
        boolean saved = this.save(post);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "发布帖子失败");
        return post.getId();
    }

    @Override
    public boolean deletePost(long id, User loginUser) {
        Post post = this.getById(id);
        ThrowUtils.throwIf(post == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!post.getAuthorId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.removeById(id);
    }

    @Override
    public boolean editPost(Post post, User loginUser) {
        Post existing = this.getById(post.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!existing.getAuthorId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.updateById(post);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean toggleLike(long postId, User loginUser) {
        Post post = this.getById(postId);
        ThrowUtils.throwIf(post == null, ErrorCode.NOT_FOUND_ERROR, "帖子不存在");

        boolean isLiked = likeRecordService.toggleLike(loginUser.getId(), postId, TARGET_TYPE);
        // 更新帖子点赞数
        if (isLiked) {
            this.lambdaUpdate()
                    .eq(Post::getId, postId)
                    .setSql("likes = likes + 1")
                    .update();
        } else {
            this.lambdaUpdate()
                    .eq(Post::getId, postId)
                    .setSql("likes = GREATEST(likes - 1, 0)")
                    .update();
        }
        return isLiked;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean toggleFavorite(long postId, User loginUser) {
        Post post = this.getById(postId);
        ThrowUtils.throwIf(post == null, ErrorCode.NOT_FOUND_ERROR, "帖子不存在");

        return favoriteRecordService.toggleFavorite(loginUser.getId(), postId, TARGET_TYPE);
    }
}
