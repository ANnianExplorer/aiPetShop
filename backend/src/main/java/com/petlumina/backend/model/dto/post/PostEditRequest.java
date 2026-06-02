package com.petlumina.backend.model.dto.post;

import lombok.Data;

import java.io.Serializable;

/**
 * 帖子编辑请求
 */
@Data
public class PostEditRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    private String content;

    private String images;

    private String tags;

    private String category;
}
