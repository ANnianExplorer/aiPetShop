package com.petlumina.backend.service.user;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.health.HealthPlanQueryRequest;
import com.petlumina.backend.model.dto.health.HealthRecordQueryRequest;
import com.petlumina.backend.model.entity.HealthPlan;
import com.petlumina.backend.model.entity.HealthRecord;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.HealthDashboardVO;
import com.petlumina.backend.model.vo.HealthRecordVO;

import java.util.List;

/**
 * 健康服务接口
 */
public interface HealthService extends IService<HealthRecord> {

    /**
     * 构建健康记录查询条件
     */
    QueryWrapper<HealthRecord> getRecordQueryWrapper(HealthRecordQueryRequest request);

    /**
     * 添加健康记录
     */
    long addHealthRecord(HealthRecord record, User loginUser);

    /**
     * 获取健康仪表盘数据
     */
    HealthDashboardVO getDashboard(long petId, User loginUser);

    /**
     * 获取7天周数据
     */
    List<HealthRecordVO> getWeeklyData(long petId, User loginUser);
}
