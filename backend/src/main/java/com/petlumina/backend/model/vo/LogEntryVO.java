package com.petlumina.backend.model.vo;

import cn.hutool.json.JSONUtil;
import com.petlumina.backend.model.entity.LogEntry;
import lombok.Data;
import org.springframework.beans.BeanUtils;

import java.io.Serializable;
import java.util.Date;
import java.util.List;

/**
 * 生活记录 VO
 */
@Data
public class LogEntryVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    private Long userId;
    private Long petId;
    private String type;
    private String title;
    private String content;
    private List<String> imageList;
    private List<String> tagList;
    private Integer likes;
    private UserVO user;
    private Date createTime;

    public static LogEntryVO objToVo(LogEntry logEntry) {
        if (logEntry == null) {
            return null;
        }
        LogEntryVO vo = new LogEntryVO();
        BeanUtils.copyProperties(logEntry, vo);
        // JSON 字符串转 List
        if (logEntry.getImages() != null) {
            vo.setImageList(JSONUtil.toList(logEntry.getImages(), String.class));
        }
        if (logEntry.getTags() != null) {
            vo.setTagList(JSONUtil.toList(logEntry.getTags(), String.class));
        }
        return vo;
    }
}
