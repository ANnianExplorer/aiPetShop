package com.petlumina.backend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.petlumina.backend.model.dto.dashboard.DailyCount;
import com.petlumina.backend.model.entity.Post;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 帖子 Mapper
 */
public interface PostMapper extends BaseMapper<Post> {

    /**
     * 按天统计有效帖子数（仪表盘 7 天趋势）。
     *
     * <p>用一条 GROUP BY 代替"循环 7 次 count(*)"；只返回有数据的天，
     * 缺的日期由 Service 补 0，避免这里再拼日历逻辑。</p>
     *
     * @param start 起始时间，含（格式 yyyy-MM-dd HH:mm:ss）
     */
    @Select("SELECT DATE_FORMAT(create_time, '%Y-%m-%d') AS day, COUNT(*) AS total "
            + "FROM post "
            + "WHERE is_delete = 0 AND create_time >= #{start} "
            + "GROUP BY DATE_FORMAT(create_time, '%Y-%m-%d')")
    List<DailyCount> countByDay(@Param("start") String start);
}
