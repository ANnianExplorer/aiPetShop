package com.petlumina.backend.model.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 违规记录实体（BACKLOG E9）
 */
@Data
@TableName("violation_record")
public class ViolationRecord implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    /** 目标类型：post / comment */
    private String targetType;

    /** 目标 id；发帖/评论在入库前就被拦截时为空 */
    private Long targetId;

    /** 违规内容快照，最多 500 字 */
    private String contentSnapshot;

    /** 发布者用户 id */
    private Long authorId;

    /** 违规原因 */
    private String reason;

    /** 命中的敏感词 */
    private String word;

    /** 状态：0 待处理，1 已处理 */
    private Integer status;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private Date updateTime;

    @TableLogic
    private Integer isDelete;
}
