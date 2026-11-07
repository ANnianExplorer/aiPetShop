package com.petlumina.backend.service.violation;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.violation.ViolationRecordQueryRequest;
import com.petlumina.backend.model.entity.ViolationRecord;

/**
 * 违规记录服务
 */
public interface ViolationRecordService extends IService<ViolationRecord> {

    /**
     * 管理端分页查询违规记录
     */
    Page<ViolationRecord> listPage(ViolationRecordQueryRequest request);

    /**
     * 标记违规记录为已处理（幂等）
     */
    boolean handle(Long id);
}
