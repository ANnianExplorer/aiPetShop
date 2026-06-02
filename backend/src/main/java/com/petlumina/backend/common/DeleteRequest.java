package com.petlumina.backend.common;

import lombok.Data;

import java.io.Serializable;

/**
 * 通用删除请求
 */
@Data
public class DeleteRequest implements Serializable {

    /** 要删除的记录ID */
    private Long id;
}
