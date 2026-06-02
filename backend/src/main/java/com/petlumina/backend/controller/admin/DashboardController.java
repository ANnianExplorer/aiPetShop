package com.petlumina.backend.controller.admin;

import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.service.admin.DashboardService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin/dashboard")
@Slf4j
public class DashboardController {

    @Resource
    private DashboardService dashboardService;

    @GetMapping("/stats")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Map<String, Object>> getStats() {
        return ResultUtils.success(dashboardService.getStats());
    }
}
