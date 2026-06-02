package com.petlumina.backend.model.vo;

import com.petlumina.backend.model.entity.HealthPlan;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.Date;

/**
 * 健康计划 VO
 */
@Data
public class HealthPlanVO implements Serializable {

    private static final long serialVersionUID = 1L;

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
    private Date createTime;

    public static HealthPlanVO objToVo(HealthPlan plan) {
        if (plan == null) {
            return null;
        }
        HealthPlanVO vo = new HealthPlanVO();
        BeanUtils.copyProperties(plan, vo);
        return vo;
    }
}
