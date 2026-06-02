package com.petlumina.backend.model.dto.logentry;

import lombok.Data;

import java.io.Serializable;

/**
 * 生活记录添加请求
 */
@Data
public class LogEntryAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long petId;

    private String type;

    private String title;

    private String content;

    private String images;

    private String tags;
}
