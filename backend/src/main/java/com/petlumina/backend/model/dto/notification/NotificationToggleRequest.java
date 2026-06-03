package com.petlumina.backend.model.dto.notification;

import lombok.Data;

import java.io.Serializable;

/**
 * 通知状态切换请求
 */
@Data
public class NotificationToggleRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    /** 目标状态: 0=取消发布 1=发布 */
    private Integer status;
}
