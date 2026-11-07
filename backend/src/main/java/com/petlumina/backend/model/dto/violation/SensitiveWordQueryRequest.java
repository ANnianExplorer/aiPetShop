package com.petlumina.backend.model.dto.violation;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 敏感词分页查询请求
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class SensitiveWordQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 敏感词模糊搜索 */
    private String word;

    /** 分类过滤 */
    private String category;

    /** 状态过滤：1 启用，0 禁用 */
    private Integer status;
}
