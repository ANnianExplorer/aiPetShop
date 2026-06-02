package com.petlumina.backend.model.vo;

import lombok.Data;

import java.io.Serializable;
import java.util.List;

/**
 * 健康仪表盘 VO
 */
@Data
public class HealthDashboardVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Double weight;
    private String weightChange;
    private Integer heartRate;
    private Double sleepHours;
    private Integer steps;
    private Integer calories;
    private Integer exercise;
    private Integer waterIntake;
    private String mood;
    private HealthRecordVO yesterdayData;
    private List<HealthRecordVO> weeklyData;
}
