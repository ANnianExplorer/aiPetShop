package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 通知实体
 */
@Data
@TableName("notification")
public class Notification implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private Long userId;

    private String type;

    private String title;

    private String content;

    private Integer isRead;

    private Long relatedId;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;
}
