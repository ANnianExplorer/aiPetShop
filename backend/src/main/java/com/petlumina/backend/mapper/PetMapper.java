package com.petlumina.backend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.petlumina.backend.model.dto.dashboard.TypeCount;
import com.petlumina.backend.model.entity.Pet;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 宠物 Mapper
 */
public interface PetMapper extends BaseMapper<Pet> {

    /**
     * 按类型统计有效宠物数（仪表盘类型分布）。
     *
     * <p>原来是把整张 pet 表捞进内存再用 Stream 分组，宠物多了就是一次全表传输；
     * 这里改成 GROUP BY，数据库只回几行。</p>
     */
    @Select("SELECT type, COUNT(*) AS total FROM pet WHERE is_delete = 0 GROUP BY type")
    List<TypeCount> countByType();
}
