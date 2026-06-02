package com.petlumina.backend.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.mapper.LikeRecordMapper;
import com.petlumina.backend.model.entity.LikeRecord;
import com.petlumina.backend.service.LikeRecordService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 点赞记录服务实现
 */
@Service
@Slf4j
public class LikeRecordServiceImpl extends ServiceImpl<LikeRecordMapper, LikeRecord>
        implements LikeRecordService {

    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public boolean toggleLike(Long userId, Long targetId, String targetType) {
        QueryWrapper<LikeRecord> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId);
        queryWrapper.eq("target_id", targetId);
        queryWrapper.eq("target_type", targetType);

        LikeRecord existing = this.getOne(queryWrapper);
        if (existing != null) {
            // 已点赞，取消点赞
            this.removeById(existing.getId());
            return false;
        } else {
            // 未点赞，添加点赞
            LikeRecord record = new LikeRecord();
            record.setUserId(userId);
            record.setTargetId(targetId);
            record.setTargetType(targetType);
            this.save(record);
            return true;
        }
    }

    @Override
    public Map<Long, Boolean> getLikeMap(Long userId, Set<Long> targetIds, String targetType) {
        if (targetIds == null || targetIds.isEmpty()) {
            return new HashMap<>();
        }
        QueryWrapper<LikeRecord> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId);
        queryWrapper.eq("target_type", targetType);
        queryWrapper.in("target_id", targetIds);

        List<LikeRecord> records = this.list(queryWrapper);
        return records.stream()
                .collect(Collectors.toMap(LikeRecord::getTargetId, r -> true, (a, b) -> a));
    }
}
