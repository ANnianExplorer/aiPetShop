package com.petlumina.backend.model.dto.violation;

import lombok.Data;

import java.io.Serializable;

/**
 * 添加敏感词请求
 */
@Data
public class SensitiveWordAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String word;

    private String category;

    private String level;
}
