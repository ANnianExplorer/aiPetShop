package com.petlumina.backend.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.health.HealthPlanAddRequest;
import com.petlumina.backend.model.dto.health.HealthPlanEditRequest;
import com.petlumina.backend.model.dto.health.HealthPlanQueryRequest;
import com.petlumina.backend.model.dto.health.HealthRecordAddRequest;
import com.petlumina.backend.model.dto.health.HealthRecordQueryRequest;
import com.petlumina.backend.model.entity.HealthPlan;
import com.petlumina.backend.model.entity.HealthRecord;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.HealthDashboardVO;
import com.petlumina.backend.model.vo.HealthPlanVO;
import com.petlumina.backend.model.vo.HealthRecordVO;
import com.petlumina.backend.service.HealthPlanService;
import com.petlumina.backend.service.HealthService;
import com.petlumina.backend.service.PetService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 健康管理控制器
 */
@RestController
@RequestMapping("/api/v1/health")
@Slf4j
public class HealthController {

    @Resource
    private HealthService healthService;

    @Resource
    private HealthPlanService healthPlanService;

    @Resource
    private PetService petService;

    @Resource
    private UserService userService;

    // ==================== 健康仪表盘 ====================

    /**
     * 获取健康仪表盘
     */
    @GetMapping("/dashboard")
    public BaseResponse<HealthDashboardVO> getDashboard(@RequestParam long petId,
                                                        HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        HealthDashboardVO dashboard = healthService.getDashboard(petId, loginUser);
        return ResultUtils.success(dashboard);
    }

    // ==================== 健康记录 ====================

    /**
     * 添加健康记录
     */
    @PostMapping("/record/add")
    @RateLimiter(key = "health_record_add", time = 60, count = 20, message = "添加健康记录操作过于频繁")
    public BaseResponse<Long> addHealthRecord(@RequestBody HealthRecordAddRequest request,
                                              HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(request.getPetId() == null, ErrorCode.PARAMS_ERROR, "宠物ID不能为空");

        User loginUser = userService.getLoginUser(httpRequest);

        HealthRecord record = new HealthRecord();
        BeanUtils.copyProperties(request, record);

        long recordId = healthService.addHealthRecord(record, loginUser);
        log.info("添加健康记录成功: recordId={}, petId={}", recordId, request.getPetId());
        return ResultUtils.success(recordId);
    }

    /**
     * 健康记录分页查询
     */
    @PostMapping("/record/list/page")
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<HealthRecordVO>> listHealthRecordVOByPage(
            @RequestBody HealthRecordQueryRequest request,
            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        ThrowUtils.throwIf(request.getPetId() == null, ErrorCode.PARAMS_ERROR, "宠物ID不能为空");
        // 校验宠物归属
        Pet pet = petService.getById(request.getPetId());
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR, "宠物不存在");
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);

        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<HealthRecord> queryWrapper = healthService.getRecordQueryWrapper(request);
        Page<HealthRecord> page = healthService.page(new Page<>(current, size), queryWrapper);

        Page<HealthRecordVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(HealthRecordVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    /**
     * 获取7天周数据
     */
    @GetMapping("/record/weekly")
    public BaseResponse<List<HealthRecordVO>> getWeeklyData(@RequestParam long petId,
                                                            HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        List<HealthRecordVO> weeklyData = healthService.getWeeklyData(petId, loginUser);
        return ResultUtils.success(weeklyData);
    }

    // ==================== 健康计划 ====================

    /**
     * 添加健康计划
     */
    @PostMapping("/plan/add")
    @RateLimiter(key = "health_plan_add", time = 60, count = 10, message = "添加健康计划操作过于频繁")
    public BaseResponse<Long> addHealthPlan(@RequestBody HealthPlanAddRequest request,
                                            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(request.getPetId() == null, ErrorCode.PARAMS_ERROR, "宠物ID不能为空");
        ThrowUtils.throwIf(request.getTitle() == null || request.getTitle().isBlank(), ErrorCode.PARAMS_ERROR, "计划标题不能为空");

        User loginUser = userService.getLoginUser(httpRequest);

        HealthPlan plan = new HealthPlan();
        BeanUtils.copyProperties(request, plan);

        long planId = healthPlanService.addHealthPlan(plan, loginUser);
        log.info("添加健康计划成功: planId={}, petId={}", planId, request.getPetId());
        return ResultUtils.success(planId);
    }

    /**
     * 删除健康计划
     */
    @PostMapping("/plan/delete")
    public BaseResponse<Boolean> deleteHealthPlan(@RequestBody DeleteRequest request,
                                                  HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = healthPlanService.deleteHealthPlan(request.getId(), loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 编辑健康计划
     */
    @PostMapping("/plan/edit")
    public BaseResponse<Boolean> editHealthPlan(@RequestBody HealthPlanEditRequest request,
                                                HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);

        HealthPlan plan = new HealthPlan();
        BeanUtils.copyProperties(request, plan);

        boolean result = healthPlanService.editHealthPlan(plan, loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 健康计划分页查询
     */
    @PostMapping("/plan/list/page")
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<HealthPlanVO>> listHealthPlanVOByPage(
            @RequestBody HealthPlanQueryRequest request,
            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        ThrowUtils.throwIf(request.getPetId() == null, ErrorCode.PARAMS_ERROR, "宠物ID不能为空");
        // 校验宠物归属
        Pet pet = petService.getById(request.getPetId());
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR, "宠物不存在");
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);

        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<HealthPlan> queryWrapper = healthPlanService.getQueryWrapper(request);
        Page<HealthPlan> page = healthPlanService.page(new Page<>(current, size), queryWrapper);

        Page<HealthPlanVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(HealthPlanVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }
}
