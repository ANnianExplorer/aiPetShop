package com.petlumina.backend.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.entity.FavoriteRecord;

import java.util.Map;
import java.util.Set;

/**
 * 收藏记录服务接口
 */
public interface FavoriteRecordService extends IService<FavoriteRecord> {

    /**
     * 切换收藏状态 (收藏/取消收藏)
     *
     * @return true=已收藏, false=已取消收藏
     */
    boolean toggleFavorite(Long userId, Long targetId, String targetType);

    /**
     * 批量查询收藏状态
     */
    Map<Long, Boolean> getFavoriteMap(Long userId, Set<Long> targetIds, String targetType);
}
