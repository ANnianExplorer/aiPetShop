package com.petlumina.backend.model.dto.topic;

import lombok.Data;

import java.io.Serializable;

/**
 * 话题添加请求
 */
@Data
public class TopicAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String title;

    private String description;

    private String image;

    private String category;
}
