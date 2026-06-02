package com.petlumina.backend.model.dto.logentry;

import lombok.Data;

import java.io.Serializable;

/**
 * 生活记录编辑请求
 */
@Data
public class LogEntryEditRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    private String title;

    private String content;

    private String images;

    private String tags;
}
