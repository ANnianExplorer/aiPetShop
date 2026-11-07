package com.petlumina.backend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.petlumina.backend.model.entity.ViolationRecord;
import org.apache.ibatis.annotations.Mapper;

/**
 * 违规记录 Mapper
 */
@Mapper
public interface ViolationRecordMapper extends BaseMapper<ViolationRecord> {
}
