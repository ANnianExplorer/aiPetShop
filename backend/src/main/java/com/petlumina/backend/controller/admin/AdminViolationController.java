package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.violation.SensitiveWordAddRequest;
import com.petlumina.backend.model.dto.violation.SensitiveWordQueryRequest;
import com.petlumina.backend.model.dto.violation.SensitiveWordUpdateRequest;
import com.petlumina.backend.model.dto.violation.ViolationHandleRequest;
import com.petlumina.backend.model.dto.violation.ViolationRecordQueryRequest;
import com.petlumina.backend.model.entity.SensitiveWord;
import com.petlumina.backend.model.entity.ViolationRecord;
import com.petlumina.backend.service.violation.SensitiveWordService;
import com.petlumina.backend.service.violation.ViolationRecordService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;

/**
 * 管理端违规管理接口（BACKLOG E9）
 */
@RestController
@RequestMapping("/api/v1/admin/violation")
@Slf4j
public class AdminViolationController {

    @Resource
    private SensitiveWordService sensitiveWordService;

    @Resource
    private ViolationRecordService violationRecordService;

    @PostMapping("/word/list/page")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<SensitiveWord>> listWordByPage(@RequestBody SensitiveWordQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        return ResultUtils.success(sensitiveWordService.listPage(request));
    }

    @PostMapping("/word/add")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> addWord(@RequestBody SensitiveWordAddRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        return ResultUtils.success(sensitiveWordService.addWord(request));
    }

    @PostMapping("/word/update")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> updateWord(@RequestBody SensitiveWordUpdateRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        return ResultUtils.success(sensitiveWordService.updateWord(request));
    }

    @PostMapping("/word/delete")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> deleteWord(@RequestBody DeleteRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() == null || request.getId() <= 0,
                ErrorCode.PARAMS_ERROR);
        return ResultUtils.success(sensitiveWordService.deleteWord(request.getId()));
    }

    @PostMapping("/record/list/page")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<ViolationRecord>> listRecordByPage(
            @RequestBody ViolationRecordQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        return ResultUtils.success(violationRecordService.listPage(request));
    }

    @PostMapping("/record/handle")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> handleRecord(@RequestBody ViolationHandleRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        return ResultUtils.success(violationRecordService.handle(request.getId()));
    }
}
