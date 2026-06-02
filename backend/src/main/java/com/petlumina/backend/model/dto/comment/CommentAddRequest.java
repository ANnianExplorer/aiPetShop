package com.petlumina.backend.model.dto.comment;

import lombok.Data;

import java.io.Serializable;

/**
 * 评论添加请求
 */
@Data
public class CommentAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long postId;

    private String content;

    private Long parentId;
}
