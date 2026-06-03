package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.health.HealthQueryRequest;
import com.petlumina.backend.model.entity.HealthRecord;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.vo.HealthRecordVO;
import com.petlumina.backend.service.user.HealthService;
import com.petlumina.backend.service.user.PetService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/admin/health")
@Slf4j
public class AdminHealthController {

    @Resource
    private HealthService healthService;

    @Resource
    private PetService petService;

    @PostMapping("/record/list/page")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<HealthRecordVO>> listHealthRecords(@RequestBody HealthQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<HealthRecord> queryWrapper = new QueryWrapper<>();
        if (request.getPetId() != null) {
            queryWrapper.eq("pet_id", request.getPetId());
        }
        if (request.getMood() != null && !request.getMood().isEmpty()) {
            queryWrapper.eq("mood", request.getMood());
        }
        queryWrapper.orderByDesc("date");
        Page<HealthRecord> page = healthService.page(new Page<>(current, size), queryWrapper);
        Page<HealthRecordVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(HealthRecordVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    @GetMapping("/record/detail")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Map<String, Object>> getRecordDetail(@RequestParam(value = "id") Long id) {
        HealthRecord record = healthService.getById(id);
        ThrowUtils.throwIf(record == null, ErrorCode.NOT_FOUND_ERROR);

        Map<String, Object> result = new HashMap<>();
        result.put("record", HealthRecordVO.objToVo(record));

        Pet pet = petService.getById(record.getPetId());
        if (pet != null) {
            Map<String, Object> petInfo = new HashMap<>();
            petInfo.put("id", pet.getId());
            petInfo.put("name", pet.getName());
            petInfo.put("avatar", pet.getAvatar());
            petInfo.put("type", pet.getType());
            result.put("pet", petInfo);
        }

        QueryWrapper<HealthRecord> wrapper = new QueryWrapper<HealthRecord>()
                .eq("pet_id", record.getPetId())
                .orderByDesc("date")
                .last("LIMIT 7");
        result.put("recentRecords", healthService.list(wrapper));

        return ResultUtils.success(result);
    }
}
