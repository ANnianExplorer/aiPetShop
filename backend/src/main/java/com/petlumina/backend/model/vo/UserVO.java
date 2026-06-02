package com.petlumina.backend.model.vo;

import com.petlumina.backend.model.entity.User;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.Date;

/**
 * 用户 VO
 */
@Data
public class UserVO implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 用户ID */
    private Long id;

    /** 昵称 */
    private String nickname;

    /** 头像 */
    private String avatar;

    /** 个人简介 */
    private String bio;

    /** 所在地 */
    private String location;

    /** 创建时间 */
    private Date createTime;

    /**
     * Entity → VO
     */
    public static UserVO objToVo(User user) {
        if (user == null) {
            return null;
        }
        UserVO vo = new UserVO();
        BeanUtils.copyProperties(user, vo);
        return vo;
    }
}
