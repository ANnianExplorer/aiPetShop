package com.petlumina.backend.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.HealthRecordMapper;
import com.petlumina.backend.model.dto.health.HealthRecordQueryRequest;
import com.petlumina.backend.model.entity.HealthRecord;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.HealthDashboardVO;
import com.petlumina.backend.model.vo.HealthRecordVO;
import com.petlumina.backend.service.HealthService;
import com.petlumina.backend.service.PetService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 健康服务实现
 */
@Service
@Slf4j
public class HealthServiceImpl extends ServiceImpl<HealthRecordMapper, HealthRecord>
        implements HealthService {

    @Resource
    private PetService petService;

    @Resource
    private UserService userService;

    @Override
    public QueryWrapper<HealthRecord> getRecordQueryWrapper(HealthRecordQueryRequest request) {
        QueryWrapper<HealthRecord> queryWrapper = new QueryWrapper<>();
        Long petId = request.getPetId();

        queryWrapper.eq(petId != null, "pet_id", petId);
        queryWrapper.ge(request.getStartDate() != null, "date", request.getStartDate());
        queryWrapper.le(request.getEndDate() != null, "date", request.getEndDate());
        queryWrapper.orderByDesc("date");
        return queryWrapper;
    }

    @Override
    public long addHealthRecord(HealthRecord record, User loginUser) {
        // 校验宠物归属
        Pet pet = petService.getById(record.getPetId());
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR, "宠物不存在");
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);

        boolean saved = this.save(record);
        ThrowUtils.throwIf(!saved, ErrorCode.OPERATION_ERROR, "添加健康记录失败");
        return record.getId();
    }

    @Override
    public HealthDashboardVO getDashboard(long petId, User loginUser) {
        // 校验宠物归属
        Pet pet = petService.getById(petId);
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR, "宠物不存在");
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);

        HealthDashboardVO dashboard = new HealthDashboardVO();

        // 获取最新一条记录
        QueryWrapper<HealthRecord> latestWrapper = new QueryWrapper<>();
        latestWrapper.eq("pet_id", petId);
        latestWrapper.orderByDesc("date");
        latestWrapper.last("LIMIT 1");
        HealthRecord latest = this.getOne(latestWrapper);

        if (latest != null) {
            dashboard.setWeight(latest.getWeight());
            dashboard.setHeartRate(latest.getHeartRate());
            dashboard.setSleepHours(latest.getSleepHours());
            dashboard.setSteps(latest.getSteps());
            dashboard.setCalories(latest.getCalories());
            dashboard.setExercise(latest.getExercise());
            dashboard.setWaterIntake(latest.getWaterIntake());
            dashboard.setMood(latest.getMood());

            // 计算体重变化
            QueryWrapper<HealthRecord> prevWrapper = new QueryWrapper<>();
            prevWrapper.eq("pet_id", petId);
            prevWrapper.lt("date", latest.getDate());
            prevWrapper.orderByDesc("date");
            prevWrapper.last("LIMIT 1");
            HealthRecord prev = this.getOne(prevWrapper);
            if (prev != null && prev.getWeight() != null && latest.getWeight() != null) {
                double change = latest.getWeight() - prev.getWeight();
                dashboard.setWeightChange(String.format("%+.1f", change));
            } else {
                dashboard.setWeightChange("0.0");
            }
        }

        // 获取昨日数据
        Calendar cal = Calendar.getInstance();
        cal.add(Calendar.DAY_OF_MONTH, -1);
        cal.set(Calendar.HOUR_OF_DAY, 0);
        cal.set(Calendar.MINUTE, 0);
        cal.set(Calendar.SECOND, 0);
        Date yesterdayStart = cal.getTime();
        cal.set(Calendar.HOUR_OF_DAY, 23);
        cal.set(Calendar.MINUTE, 59);
        cal.set(Calendar.SECOND, 59);
        Date yesterdayEnd = cal.getTime();

        QueryWrapper<HealthRecord> yesterdayWrapper = new QueryWrapper<>();
        yesterdayWrapper.eq("pet_id", petId);
        yesterdayWrapper.ge("date", yesterdayStart);
        yesterdayWrapper.le("date", yesterdayEnd);
        yesterdayWrapper.last("LIMIT 1");
        HealthRecord yesterday = this.getOne(yesterdayWrapper);
        if (yesterday != null) {
            dashboard.setYesterdayData(HealthRecordVO.objToVo(yesterday));
        }

        // 获取7天数据
        dashboard.setWeeklyData(getWeeklyData(petId, loginUser));

        return dashboard;
    }

    @Override
    public List<HealthRecordVO> getWeeklyData(long petId, User loginUser) {
        // 校验宠物归属
        Pet pet = petService.getById(petId);
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR, "宠物不存在");
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);

        Calendar cal = Calendar.getInstance();
        cal.add(Calendar.DAY_OF_MONTH, -7);
        cal.set(Calendar.HOUR_OF_DAY, 0);
        cal.set(Calendar.MINUTE, 0);
        cal.set(Calendar.SECOND, 0);
        Date weekAgo = cal.getTime();

        QueryWrapper<HealthRecord> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("pet_id", petId);
        queryWrapper.ge("date", weekAgo);
        queryWrapper.orderByAsc("date");

        return this.list(queryWrapper).stream()
                .map(HealthRecordVO::objToVo)
                .collect(Collectors.toList());
    }
}
