package com.petlumina.backend.service.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.PetMapper;
import com.petlumina.backend.model.dto.pet.PetQueryRequest;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.PetService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;

/**
 * 宠物服务实现
 */
@Service
@Slf4j
public class PetServiceImpl extends ServiceImpl<PetMapper, Pet>
        implements PetService {

    @Resource
    private UserService userService;

    @Override
    public QueryWrapper<Pet> getQueryWrapper(PetQueryRequest request) {
        QueryWrapper<Pet> queryWrapper = new QueryWrapper<>();
        String name = request.getName();
        String type = request.getType();
        Long userId = request.getUserId();

        queryWrapper.like(StrUtil.isNotBlank(name), "name", name);
        queryWrapper.eq(StrUtil.isNotBlank(type), "type", type);
        queryWrapper.eq(userId != null, "user_id", userId);
        queryWrapper.orderByDesc("create_time");
        return queryWrapper;
    }

    @Override
    public long addPet(Pet pet, User loginUser) {
        pet.setUserId(loginUser.getId());
        pet.setHealthScore(100);
        pet.setTodaySteps(0);
        pet.setFeedingCount(0);
        pet.setFeedingTotal(0);
        boolean saved = this.save(pet);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "添加宠物失败");
        return pet.getId();
    }

    @Override
    public boolean deletePet(long id, User loginUser) {
        Pet pet = this.getById(id);
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.removeById(id);
    }

    @Override
    public boolean editPet(Pet pet, User loginUser) {
        Pet existing = this.getById(pet.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!existing.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.updateById(pet);
    }
}
