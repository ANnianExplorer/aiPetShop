package com.petlumina.backend.model.vo;

import com.petlumina.backend.model.entity.Topic;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.Date;

/**
 * 话题 VO
 */
@Data
public class TopicVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    private String title;
    private String description;
    private String image;
    private String category;
    private Integer postCount;
    private Integer followerCount;
    private Integer isFollowed;
    private Date createTime;

    public static TopicVO objToVo(Topic topic) {
        if (topic == null) {
            return null;
        }
        TopicVO vo = new TopicVO();
        BeanUtils.copyProperties(topic, vo);
        return vo;
    }
}
