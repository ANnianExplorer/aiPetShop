package com.petlumina.backend.common;

import lombok.Data;

import java.io.Serializable;

/**
 * 分页请求基类
 */
@Data
public class PageRequest implements Serializable {

    /** 当前页码 */
    private int current = 1;

    /** 每页条数 */
    private int pageSize = 10;

    /** 排序字段 */
    private String sortField;

    /** 排序方式: ascend/descend */
    private String sortOrder = "descend";
}
