package com.petlumina.backend.model.dto.dashboard;

import lombok.Data;

/**
 * 按类别聚合的行（宠物类型分布用）。
 *
 * <p>只用于 Service ← Mapper 之间传递，不由 Controller 直接返回。</p>
 */
@Data
public class TypeCount {

    /** 类型原值，可能为 null（库里有空类型的历史数据） */
    private String type;

    /** 该类型数量 */
    private Long total;
}
