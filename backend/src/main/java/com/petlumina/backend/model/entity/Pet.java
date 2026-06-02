package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 宠物实体
 */
@Data
@TableName("pet")
public class Pet implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    /** 所属用户ID */
    private Long userId;

    /** 宠物名称 */
    private String name;

    /** 头像URL */
    private String avatar;

    /** 类型: dog/cat/other */
    private String type;

    /** 品种 */
    private String breed;

    /** 年龄 */
    private String age;

    /** 健康评分 */
    private Integer healthScore;

    /** 今日步数 */
    private Integer todaySteps;

    /** 已喂食次数 */
    private Integer feedingCount;

    /** 计划喂食次数 */
    private Integer feedingTotal;

    /** 备注 */
    private String notes;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private Date updateTime;

    @TableLogic
    private Integer isDelete;
}
