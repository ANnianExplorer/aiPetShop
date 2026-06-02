package com.petlumina.backend.model.dto.notification;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 通知查询请求
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class NotificationQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String type;

    private Integer isRead;
}
