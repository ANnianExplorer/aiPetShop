package com.petlumina.backend.service.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.HealthPlanMapper;
import com.petlumina.backend.model.dto.health.HealthPlanQueryRequest;
import com.petlumina.backend.model.entity.HealthPlan;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.HealthPlanService;
import com.petlumina.backend.service.PetService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;

/**
 * 健康计划服务实现
 */
@Service
@Slf4j
public class HealthPlanServiceImpl extends ServiceImpl<HealthPlanMapper, HealthPlan>
        implements HealthPlanService {

    @Resource
    private PetService petService;

    @Resource
    private UserService userService;

    @Override
    public QueryWrapper<HealthPlan> getQueryWrapper(HealthPlanQueryRequest request) {
        QueryWrapper<HealthPlan> queryWrapper = new QueryWrapper<>();
        Long petId = request.getPetId();
        String type = request.getType();
        Integer isActive = request.getIsActive();

        queryWrapper.eq(petId != null, "pet_id", petId);
        queryWrapper.eq(StrUtil.isNotBlank(type), "type", type);
        queryWrapper.eq(isActive != null, "is_active", isActive);
        queryWrapper.orderByDesc("create_time");
        return queryWrapper;
    }

    @Override
    public long addHealthPlan(HealthPlan plan, User loginUser) {
        // 校验宠物归属
        Pet pet = petService.getById(plan.getPetId());
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR, "宠物不存在");
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);

        plan.setIsActive(1);
        boolean saved = this.save(plan);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "添加健康计划失败");
        return plan.getId();
    }

    @Override
    public boolean deleteHealthPlan(long id, User loginUser) {
        HealthPlan plan = this.getById(id);
        ThrowUtils.throwIf(plan == null, ErrorCode.NOT_FOUND_ERROR);
        // 通过 petId 校验归属
        Pet pet = petService.getById(plan.getPetId());
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR, "宠物不存在");
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.removeById(id);
    }

    @Override
    public boolean editHealthPlan(HealthPlan plan, User loginUser) {
        HealthPlan existing = this.getById(plan.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR);
        // 通过 petId 校验归属
        Pet pet = petService.getById(existing.getPetId());
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR, "宠物不存在");
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        return this.updateById(plan);
    }
}
