package com.petlumina.backend.model.dto.reminder;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;
import java.util.Date;

/**
 * 日程提醒查询请求
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class ReminderQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String type;

    private Long petId;

    private Long userId;

    private Integer isCompleted;

    private Date startDate;

    private Date endDate;
}
