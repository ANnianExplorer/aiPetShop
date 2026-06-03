package com.petlumina.backend.model.dto.pet;

import lombok.Data;

import java.io.Serializable;

/**
 * 编辑宠物请求
 */
@Data
public class PetEditRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 宠物ID */
    private Long id;

    /** 宠物名称 */
    private String name;

    /** 品种 */
    private String breed;

    /** 年龄 */
    private String age;

    /** 备注 */
    private String notes;

    /** 头像URL */
    private String avatar;
}
