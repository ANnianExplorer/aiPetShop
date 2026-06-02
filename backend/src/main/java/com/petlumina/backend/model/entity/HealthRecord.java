package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 健康记录实体
 */
@Data
@TableName("health_record")
public class HealthRecord implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private Long petId;

    private Date date;

    private Integer heartRate;

    private Double sleepHours;

    private Integer steps;

    private Integer calories;

    private Integer exercise;

    private Double weight;

    private Integer waterIntake;

    private String mood;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;
}
