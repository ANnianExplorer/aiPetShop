package com.petlumina.backend.service.user;

import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.entity.LikeRecord;

import java.util.Map;
import java.util.Set;

/**
 * 点赞记录服务接口
 */
public interface LikeRecordService extends IService<LikeRecord> {

    /**
     * 切换点赞状态 (点赞/取消点赞)
     *
     * @return true=已点赞, false=已取消点赞
     */
    boolean toggleLike(Long userId, Long targetId, String targetType);

    /**
     * 批量查询点赞状态
     */
    Map<Long, Boolean> getLikeMap(Long userId, Set<Long> targetIds, String targetType);
}
