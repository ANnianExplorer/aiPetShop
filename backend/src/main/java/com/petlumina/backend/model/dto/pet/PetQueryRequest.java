package com.petlumina.backend.model.dto.pet;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 宠物查询请求
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class PetQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 宠物名称 */
    private String name;

    /** 类型: dog/cat/other */
    private String type;

    /** 所属用户ID */
    private Long userId;
}
