package com.petlumina.backend.model.dto.health;

import lombok.Data;

import java.io.Serializable;

/**
 * 健康计划添加请求
 */
@Data
public class HealthPlanAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long petId;

    private String type;

    private String title;

    private String time;

    private String frequency;

    private String standard;

    private Integer standardValue;

    private String notes;
}
