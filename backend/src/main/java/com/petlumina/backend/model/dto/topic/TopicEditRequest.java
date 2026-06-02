package com.petlumina.backend.model.dto.topic;

import lombok.Data;

import java.io.Serializable;

/**
 * 话题编辑请求
 */
@Data
public class TopicEditRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    private String title;

    private String description;

    private String image;

    private String category;
}
