package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 收藏记录实体
 */
@Data
@TableName("favorite_record")
public class FavoriteRecord implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private Long userId;

    private Long targetId;

    private String targetType;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;
}
