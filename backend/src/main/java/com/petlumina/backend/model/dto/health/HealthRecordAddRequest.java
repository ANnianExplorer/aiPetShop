package com.petlumina.backend.model.dto.health;

import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 健康记录添加请求
 */
@Data
public class HealthRecordAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

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
}
