package com.petlumina.backend.model.dto.reminder;

import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 日程提醒编辑请求
 */
@Data
public class ReminderEditRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    private String title;

    private String type;

    private Date remindTime;

    private String location;

    private String repeatType;

    private String notes;
}
