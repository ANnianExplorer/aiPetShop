package com.petlumina.backend.model.dto.post;

import com.petlumina.backend.common.PageRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;

/**
 * 帖子查询请求
 */
@EqualsAndHashCode(callSuper = true)
@Data
public class PostQueryRequest extends PageRequest implements Serializable {

    private static final long serialVersionUID = 1L;

    private String category;

    private String searchText;

    private Long topicId;

    /** 作者昵称（用于筛选某作者的帖子） */
    private String authorName;
}
