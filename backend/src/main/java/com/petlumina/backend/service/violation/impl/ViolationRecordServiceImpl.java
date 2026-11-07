package com.petlumina.backend.service.violation.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.ViolationRecordMapper;
import com.petlumina.backend.model.dto.violation.ViolationRecordQueryRequest;
import com.petlumina.backend.model.entity.ViolationRecord;
import com.petlumina.backend.service.violation.ViolationRecordService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 违规记录服务实现
 */
@Service
@Slf4j
public class ViolationRecordServiceImpl extends ServiceImpl<ViolationRecordMapper, ViolationRecord>
        implements ViolationRecordService {

    @Override
    public Page<ViolationRecord> listPage(ViolationRecordQueryRequest request) {
        long current = request.getCurrent() <= 0 ? 1 : request.getCurrent();
        long size = request.getPageSize() <= 0 ? 10 : Math.min(request.getPageSize(), 100);

        LambdaQueryWrapper<ViolationRecord> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(request.getStatus() != null, ViolationRecord::getStatus, request.getStatus())
                .eq(StrUtil.isNotBlank(request.getTargetType()),
                        ViolationRecord::getTargetType, request.getTargetType())
                .orderByDesc(ViolationRecord::getCreateTime);
        return page(new Page<>(current, size), queryWrapper);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean handle(Long id) {
        ThrowUtils.throwIf(id == null, ErrorCode.PARAMS_ERROR);
        ViolationRecord record = getById(id);
        ThrowUtils.throwIf(record == null, ErrorCode.NOT_FOUND_ERROR, "违规记录不存在");
        // 幂等：已处理直接返回成功
        if (Integer.valueOf(1).equals(record.getStatus())) {
            return true;
        }
        return update(new LambdaUpdateWrapper<ViolationRecord>()
                .eq(ViolationRecord::getId, id)
                .set(ViolationRecord::getStatus, 1));
    }
}
