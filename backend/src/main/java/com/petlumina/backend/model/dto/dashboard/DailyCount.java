package com.petlumina.backend.model.dto.dashboard;

import lombok.Data;

/**
 * 按天聚合的行（仪表盘趋势用）。
 *
 * <p>只用于 Service ← Mapper 之间传递，不由 Controller 直接返回，
 * 因此不带 VO 的字段描述。</p>
 */
@Data
public class DailyCount {

    /** yyyy-MM-dd */
    private String day;

    /** 当天的记录数 */
    private Long total;
}
