package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 通知已读记录。
 *
 * <p>广播通知（{@code user_id = 0}）不再给每个用户复制一份，而是把"谁读过"记在这里；
 * 唯一键 {@code (user_id, notification_id)} 保证重复点开不会产生多条。</p>
 */
@Data
@TableName("notification_read")
public class NotificationRead implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private Long userId;

    private Long notificationId;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;
}
