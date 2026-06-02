package com.petlumina.backend.model.vo;

import com.petlumina.backend.model.entity.Reminder;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.Date;

/**
 * 日程提醒 VO
 */
@Data
public class ReminderVO implements Serializable {

    private static final long serialVersionUID = 1L;

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
    private Date createTime;

    public static ReminderVO objToVo(Reminder reminder) {
        if (reminder == null) {
            return null;
        }
        ReminderVO vo = new ReminderVO();
        BeanUtils.copyProperties(reminder, vo);
        return vo;
    }
}
