package com.petlumina.backend.utils;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.petlumina.backend.common.PageRequest;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 排序白名单：只有声明过的字段能进 SQL，其余回落默认排序。
 */
class SortUtilsTest {

    private static final Map<String, String> ALLOWED = Map.of(
            "createTime", "create_time",
            "likes", "likes"
    );

    @Test
    @DisplayName("白名单内的字段能解析成列名")
    void resolvesWhitelistedField() {
        assertEquals("create_time", SortUtils.resolveColumn("createTime", ALLOWED));
        assertEquals("likes", SortUtils.resolveColumn("  likes  ", ALLOWED));
    }

    @Test
    @DisplayName("白名单外的字段（含 SQL 片段）一律不解析")
    void rejectsUnknownField() {
        assertNull(SortUtils.resolveColumn("password", ALLOWED));
        assertNull(SortUtils.resolveColumn("create_time; DROP TABLE user", ALLOWED));
        assertNull(SortUtils.resolveColumn("", ALLOWED));
        assertNull(SortUtils.resolveColumn(null, ALLOWED));
        assertNull(SortUtils.resolveColumn("createTime", null));
    }

    @Test
    @DisplayName("排序方向：ascend/asc 升序，其余降序")
    void parsesSortOrder() {
        assertTrue(SortUtils.isAsc("ascend"));
        assertTrue(SortUtils.isAsc("ASC"));
        assertTrue(SortUtils.isAsc(" asc "));
        assertFalse(SortUtils.isAsc("descend"));
        assertFalse(SortUtils.isAsc("desc"));
        assertFalse(SortUtils.isAsc(null));
        assertFalse(SortUtils.isAsc(""));
        assertFalse(SortUtils.isAsc("随便写"));
    }

    @Test
    @DisplayName("未指定排序时回落默认列，指定时按指定列")
    void appliesOrderBy() {
        QueryWrapper<Object> fallbackWrapper = new QueryWrapper<>();
        SortUtils.apply(fallbackWrapper, new PageRequest(), ALLOWED, "create_time");
        assertTrue(fallbackWrapper.getSqlSegment().contains("ORDER BY create_time DESC"),
                "实际 SQL 片段: " + fallbackWrapper.getSqlSegment());

        PageRequest request = new PageRequest();
        request.setSortField("likes");
        request.setSortOrder("ascend");
        QueryWrapper<Object> wrapper = new QueryWrapper<>();
        SortUtils.apply(wrapper, request, ALLOWED, "create_time");
        assertTrue(wrapper.getSqlSegment().contains("ORDER BY likes ASC"),
                "实际 SQL 片段: " + wrapper.getSqlSegment());
    }

    @Test
    @DisplayName("白名单外字段被忽略并回落默认列，不会拼进 SQL")
    void ignoresUnknownFieldAndFallsBack() {
        PageRequest request = new PageRequest();
        request.setSortField("(select 1)");
        QueryWrapper<Object> wrapper = new QueryWrapper<>();
        SortUtils.apply(wrapper, request, ALLOWED, "create_time");
        String sql = wrapper.getSqlSegment();
        assertTrue(sql.contains("ORDER BY create_time DESC"), "实际 SQL 片段: " + sql);
        assertFalse(sql.contains("select 1"), "非法字段不能出现在 SQL 里: " + sql);
    }
}
