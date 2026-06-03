package com.petlumina.backend.model.dto.reminder;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 日程提醒添加请求
 */
@Data
public class ReminderAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long petId;

    private String title;

    private String type;

    private Date remindTime;

    private String location;

    private String repeatType;

    private String notes;
}
