package com.petlumina.backend.utils;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.petlumina.backend.common.PageRequest;

import java.util.Map;

/**
 * 分页排序工具。
 *
 * <p>{@link PageRequest} 里的 {@code sortField} / {@code sortOrder} 之前从来没被任何
 * Service 读取过 —— 前端传了也不生效，属于"接口骗人"。这里把它接上，并强制走白名单：
 * 只允许排序列出的字段，其余一律回落默认排序（不抛错，避免老调用方炸）。</p>
 *
 * <p>白名单的 key 是接口字段名（camelCase），value 是数据库列名（snake_case），
 * 列名不来自用户输入，所以不存在 SQL 注入面。</p>
 */
public final class SortUtils {

    private SortUtils() {
    }

    /**
     * 按 {@code request} 里的排序参数给 wrapper 追加 order by；未指定或不在白名单时不做任何事。
     *
     * @param wrapper  查询条件
     * @param request  分页请求
     * @param allowed  接口字段 -> 数据库列
     * @param fallback 默认排序（可为空字符串表示不追加）
     * @param <T>      实体类型
     */
    public static <T> void apply(QueryWrapper<T> wrapper, PageRequest request,
                                 Map<String, String> allowed, String fallback) {
        String column = resolveColumn(request == null ? null : request.getSortField(), allowed);
        if (column == null) {
            if (StrUtil.isNotBlank(fallback)) {
                wrapper.orderBy(true, isAsc(request == null ? null : request.getSortOrder()), fallback);
            }
            return;
        }
        wrapper.orderBy(true, isAsc(request.getSortOrder()), column);
    }

    /**
     * 解析出排序列；不在白名单 / 为空返回 {@code null}。
     */
    public static String resolveColumn(String sortField, Map<String, String> allowed) {
        if (StrUtil.isBlank(sortField) || allowed == null) {
            return null;
        }
        return allowed.get(sortField.trim());
    }

    /**
     * {@code ascend}/{@code asc}/大小写混写都算升序，其余（含 null）按降序。
     */
    public static boolean isAsc(String sortOrder) {
        if (StrUtil.isBlank(sortOrder)) {
            return false;
        }
        String value = sortOrder.trim();
        return "ascend".equalsIgnoreCase(value) || "asc".equalsIgnoreCase(value);
    }
}
