package com.petlumina.backend.model.dto.violation;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 违规记录分页查询请求
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class ViolationRecordQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 状态过滤：0 待处理，1 已处理 */
    private Integer status;

    /** 目标类型过滤：post / comment */
    private String targetType;
}
