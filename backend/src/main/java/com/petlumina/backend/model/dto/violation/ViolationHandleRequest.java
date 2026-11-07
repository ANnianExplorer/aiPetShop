package com.petlumina.backend.model.dto.violation;

import lombok.Data;

import java.io.Serializable;

/**
 * 违规记录处理请求
 */
@Data
public class ViolationHandleRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
}
