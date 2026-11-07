package com.petlumina.backend.model.dto.post;

import lombok.Data;

import java.io.Serializable;

/**
 * 帖子添加请求
 */
@Data
public class PostAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String content;

    private String images;

    private String tags;

    private String category;

    /** 从话题页发帖时带上，服务端校验话题存在后写入 post.topic_id */
    private Long topicId;
}
