package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 健康计划实体
 */
@Data
@TableName("health_plan")
public class HealthPlan implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private Long petId;

    private String type;

    private String title;

    private String time;

    private String frequency;

    private String standard;

    private Integer standardValue;

    private String notes;

    private Integer isActive;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;
}
