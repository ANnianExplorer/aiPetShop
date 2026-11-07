package com.petlumina.backend.model.dto.violation;

import lombok.Data;

import java.io.Serializable;

/**
 * 更新敏感词请求
 */
@Data
public class SensitiveWordUpdateRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    private String word;

    private String category;

    private String level;

    /** 状态：1 启用，0 禁用；不传则不修改 */
    private Integer status;
}
