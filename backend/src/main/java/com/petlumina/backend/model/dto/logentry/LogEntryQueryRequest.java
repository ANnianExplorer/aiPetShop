package com.petlumina.backend.model.dto.logentry;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 生活记录查询请求
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class LogEntryQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String type;

    private Long userId;

    private Long petId;
}
