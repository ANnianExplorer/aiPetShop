package com.petlumina.backend.model.dto.health;

import lombok.Data;

import java.io.Serializable;

/**
 * 健康计划编辑请求
 */
@Data
public class HealthPlanEditRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    private String type;

    private String title;

    private String time;

    private String frequency;

    private String standard;

    private Integer standardValue;

    private String notes;

    private Integer isActive;
}
