package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 话题关注实体
 */
@Data
@TableName("topic_follow")
public class TopicFollow implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private Long userId;

    private Long topicId;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;
}
