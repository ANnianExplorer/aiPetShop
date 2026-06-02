package com.petlumina.backend.model.vo;

import cn.hutool.json.JSONUtil;
import com.petlumina.backend.model.entity.Post;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.Date;
import java.util.List;

/**
 * 帖子 VO
 */
@Data
public class PostVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    private Long authorId;
    private String content;
    private List<String> imageList;
    private List<String> tagList;
    private String category;
    private Integer likes;
    private Integer comments;
    private Integer isLiked;
    private Integer isFavorited;
    private UserVO user;
    private Date createTime;

    public static PostVO objToVo(Post post) {
        if (post == null) {
            return null;
        }
        PostVO vo = new PostVO();
        BeanUtils.copyProperties(post, vo);
        if (post.getImages() != null) {
            vo.setImageList(JSONUtil.toList(post.getImages(), String.class));
        }
        if (post.getTags() != null) {
            vo.setTagList(JSONUtil.toList(post.getTags(), String.class));
        }
        return vo;
    }
}
