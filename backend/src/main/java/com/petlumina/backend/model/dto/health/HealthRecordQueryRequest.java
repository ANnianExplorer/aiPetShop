package com.petlumina.backend.model.dto.health;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;
import java.util.Date;

/**
 * 健康记录查询请求
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class HealthRecordQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long petId;

    private Date startDate;

    private Date endDate;
}
