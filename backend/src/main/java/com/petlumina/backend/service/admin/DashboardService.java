package com.petlumina.backend.service.admin;

import java.util.Map;

public interface DashboardService {

    /**
     * 获取管理后台统计数据
     */
    Map<String, Object> getStats();
}
