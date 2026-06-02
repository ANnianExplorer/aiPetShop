package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 日程提醒实体
 */
@Data
@TableName("reminder")
public class Reminder implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private Long userId;

    private Long petId;

    private String title;

    private String type;

    private Date remindTime;

    private String location;

    private String repeatType;

    private String notes;

    private Integer isCompleted;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private Date updateTime;

    @TableLogic
    private Integer isDelete;
}
