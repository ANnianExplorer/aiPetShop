package com.petlumina.backend.model.dto.pet;

import lombok.Data;

import java.io.Serializable;

/**
 * 添加宠物请求
 */
@Data
public class PetAddRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 宠物名称 */
    private String name;

    /** 类型: dog/cat/other */
    private String type;

    /** 品种 */
    private String breed;

    /** 年龄 */
    private String age;

    /** 备注 */
    private String notes;
}
