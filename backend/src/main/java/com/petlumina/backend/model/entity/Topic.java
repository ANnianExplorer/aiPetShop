package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 话题实体
 */
@Data
@TableName("topic")
public class Topic implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private String title;

    private String description;

    private String image;

    private String category;

    private Integer postCount;

    private Integer followerCount;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;

    @TableLogic
    private Integer isDelete;
}
