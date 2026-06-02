package com.petlumina.backend.service.user.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.mapper.FavoriteRecordMapper;
import com.petlumina.backend.model.entity.FavoriteRecord;
import com.petlumina.backend.service.user.FavoriteRecordService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 收藏记录服务实现
 */
@Service
@Slf4j
public class FavoriteRecordServiceImpl extends ServiceImpl<FavoriteRecordMapper, FavoriteRecord>
        implements FavoriteRecordService {

    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public boolean toggleFavorite(Long userId, Long targetId, String targetType) {
        QueryWrapper<FavoriteRecord> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId);
        queryWrapper.eq("target_id", targetId);
        queryWrapper.eq("target_type", targetType);

        FavoriteRecord existing = this.getOne(queryWrapper);
        if (existing != null) {
            // 已收藏，取消收藏
            this.removeById(existing.getId());
            return false;
        } else {
            // 未收藏，添加收藏
            FavoriteRecord record = new FavoriteRecord();
            record.setUserId(userId);
            record.setTargetId(targetId);
            record.setTargetType(targetType);
            this.save(record);
            return true;
        }
    }

    @Override
    public Map<Long, Boolean> getFavoriteMap(Long userId, Set<Long> targetIds, String targetType) {
        if (targetIds == null || targetIds.isEmpty()) {
            return new HashMap<>();
        }
        QueryWrapper<FavoriteRecord> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId);
        queryWrapper.eq("target_type", targetType);
        queryWrapper.in("target_id", targetIds);

        List<FavoriteRecord> records = this.list(queryWrapper);
        return records.stream()
                .collect(Collectors.toMap(FavoriteRecord::getTargetId, r -> true, (a, b) -> a));
    }
}
