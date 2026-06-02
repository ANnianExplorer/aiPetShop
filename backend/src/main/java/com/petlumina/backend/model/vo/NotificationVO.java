package com.petlumina.backend.model.vo;

import com.petlumina.backend.model.entity.Notification;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.Date;

/**
 * 通知 VO
 */
@Data
public class NotificationVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    private Long userId;
    private String type;
    private String title;
    private String content;
    private Integer isRead;
    private Long relatedId;
    private Date createTime;

    public static NotificationVO objToVo(Notification notification) {
        if (notification == null) {
            return null;
        }
        NotificationVO vo = new NotificationVO();
        BeanUtils.copyProperties(notification, vo);
        return vo;
    }
}
