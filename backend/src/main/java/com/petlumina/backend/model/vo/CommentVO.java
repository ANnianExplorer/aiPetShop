package com.petlumina.backend.model.vo;

import com.petlumina.backend.model.entity.Comment;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * 评论 VO
 */
@Data
public class CommentVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    private Long postId;
    private Long userId;
    private String content;
    private Long parentId;
    private Integer likes;
    private UserVO user;
    private List<CommentVO> children;
    private Date createTime;

    public static CommentVO objToVo(Comment comment) {
        if (comment == null) {
            return null;
        }
        CommentVO vo = new CommentVO();
        BeanUtils.copyProperties(comment, vo);
        vo.setChildren(new ArrayList<>());
        return vo;
    }
}
