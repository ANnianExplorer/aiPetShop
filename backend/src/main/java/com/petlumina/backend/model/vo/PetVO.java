package com.petlumina.backend.model.vo;

import com.petlumina.backend.model.entity.Pet;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.Date;

/**
 * 宠物 VO
 */
@Data
public class PetVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    private Long userId;
    private String name;
    private String avatar;
    private String type;
    private String breed;
    private String age;
    private Integer healthScore;
    private Integer todaySteps;
    private Integer feedingCount;
    private Integer feedingTotal;
    private String notes;
    private UserVO user;
    private Date createTime;

    public static PetVO objToVo(Pet pet) {
        if (pet == null) {
            return null;
        }
        PetVO vo = new PetVO();
        BeanUtils.copyProperties(pet, vo);
        return vo;
    }
}
