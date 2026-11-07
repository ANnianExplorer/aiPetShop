package com.petlumina.backend.service.violation;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.petlumina.backend.model.dto.violation.SensitiveWordAddRequest;
import com.petlumina.backend.model.dto.violation.SensitiveWordQueryRequest;
import com.petlumina.backend.model.dto.violation.SensitiveWordUpdateRequest;
import com.petlumina.backend.model.entity.SensitiveWord;

/**
 * 敏感词服务
 */
public interface SensitiveWordService extends IService<SensitiveWord> {

    /**
     * 管理端分页查询敏感词
     */
    Page<SensitiveWord> listPage(SensitiveWordQueryRequest request);

    /**
     * 新增敏感词
     */
    boolean addWord(SensitiveWordAddRequest request);

    /**
     * 更新敏感词
     */
    boolean updateWord(SensitiveWordUpdateRequest request);

    /**
     * 逻辑删除敏感词
     */
    boolean deleteWord(Long id);

    /**
     * 检测内容是否命中敏感词。
     *
     * <p>命中时：hit_count + 1、写入一条待处理违规记录，然后抛出业务异常拒绝本次请求；
     * 未命中时不产生任何副作用。</p>
     *
     * @param content    待检测内容
     * @param targetType 目标类型：post / comment
     * @param authorId   发布者用户 id
     */
    void checkAndRecord(String content, String targetType, Long authorId);
}
