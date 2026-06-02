package com.petlumina.backend.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.pet.PetQueryRequest;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.entity.User;

/**
 * 宠物服务接口
 */
public interface PetService extends IService<Pet> {

    /**
     * 构建查询条件
     */
    QueryWrapper<Pet> getQueryWrapper(PetQueryRequest request);

    /**
     * 添加宠物
     */
    long addPet(Pet pet, User loginUser);

    /**
     * 删除宠物 (校验权限)
     */
    boolean deletePet(long id, User loginUser);

    /**
     * 编辑宠物 (校验权限)
     */
    boolean editPet(Pet pet, User loginUser);
}
