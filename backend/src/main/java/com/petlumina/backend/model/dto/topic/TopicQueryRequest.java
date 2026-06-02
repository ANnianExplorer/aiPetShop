package com.petlumina.backend.model.dto.topic;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 话题查询请求
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class TopicQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String category;

    private String searchText;
}
