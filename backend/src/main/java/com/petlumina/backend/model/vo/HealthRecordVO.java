package com.petlumina.backend.model.vo;

import com.petlumina.backend.model.entity.HealthRecord;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.Date;

/**
 * 健康记录 VO
 */
@Data
public class HealthRecordVO implements Serializable {

    private static final long serialVersionUID = 1L;

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
    private Date createTime;

    public static HealthRecordVO objToVo(HealthRecord record) {
        if (record == null) {
            return null;
        }
        HealthRecordVO vo = new HealthRecordVO();
        BeanUtils.copyProperties(record, vo);
        return vo;
    }
}
