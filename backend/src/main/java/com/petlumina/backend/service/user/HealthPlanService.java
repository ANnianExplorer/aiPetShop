package com.petlumina.backend.service.user;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.health.HealthPlanQueryRequest;
import com.petlumina.backend.model.entity.HealthPlan;
import com.petlumina.backend.model.entity.User;

/**
 * 健康计划服务接口
 */
public interface HealthPlanService extends IService<HealthPlan> {

    /**
     * 构建健康计划查询条件
     */
    QueryWrapper<HealthPlan> getQueryWrapper(HealthPlanQueryRequest request);

    /**
     * 添加健康计划
     */
    long addHealthPlan(HealthPlan plan, User loginUser);

    /**
     * 删除健康计划 (校验权限)
     */
    boolean deleteHealthPlan(long id, User loginUser);

    /**
     * 编辑健康计划 (校验权限)
     */
    boolean editHealthPlan(HealthPlan plan, User loginUser);
}
