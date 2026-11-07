package com.petlumina.backend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.petlumina.backend.model.entity.SensitiveWord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

/**
 * 敏感词 Mapper
 */
@Mapper
public interface SensitiveWordMapper extends BaseMapper<SensitiveWord> {

    /**
     * 按词面查询（含已逻辑删除的记录），用于唯一键冲突时复活旧词
     */
    @Select("SELECT * FROM sensitive_word WHERE word = #{word} LIMIT 1")
    SensitiveWord selectByWordIncludeDeleted(@Param("word") String word);

    /**
     * 复活一条已逻辑删除的敏感词，避免 word 唯一键冲突
     */
    @Update("UPDATE sensitive_word SET is_delete = 0, category = #{category}, level = #{level}, " +
            "status = 1, update_time = NOW() WHERE id = #{id}")
    int reviveDeleted(@Param("id") Long id,
                      @Param("category") String category,
                      @Param("level") String level);
}
