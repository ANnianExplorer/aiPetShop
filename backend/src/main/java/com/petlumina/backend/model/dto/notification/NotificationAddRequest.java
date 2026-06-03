package com.petlumina.backend.model.dto.notification;

import lombok.Data;

import java.io.Serializable;

/**
 * 通知添加请求
 */
@Data
public class NotificationAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String title;

    private String content;

    private String type;
}
