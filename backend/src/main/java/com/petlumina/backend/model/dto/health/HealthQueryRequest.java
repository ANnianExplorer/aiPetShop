package com.petlumina.backend.model.dto.health;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 健康记录查询请求
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class HealthQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long petId;

    private String mood;
}
