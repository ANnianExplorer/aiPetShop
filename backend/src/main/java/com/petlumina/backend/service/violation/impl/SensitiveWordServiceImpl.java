package com.petlumina.backend.service.violation.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.mapper.SensitiveWordMapper;
import com.petlumina.backend.model.dto.violation.SensitiveWordAddRequest;
import com.petlumina.backend.model.dto.violation.SensitiveWordQueryRequest;
import com.petlumina.backend.model.dto.violation.SensitiveWordUpdateRequest;
import com.petlumina.backend.model.entity.SensitiveWord;
import com.petlumina.backend.model.entity.ViolationRecord;
import com.petlumina.backend.service.violation.SensitiveWordService;
import com.petlumina.backend.service.violation.ViolationRecordService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.List;

/**
 * 敏感词服务实现
 */
@Service
@Slf4j
public class SensitiveWordServiceImpl extends ServiceImpl<SensitiveWordMapper, SensitiveWord>
        implements SensitiveWordService {

    /** 内容快照最大长度，与 violation_record.content_snapshot 保持一致 */
    private static final int SNAPSHOT_MAX_LENGTH = 500;

    @Resource
    private ViolationRecordService violationRecordService;

    @Override
    public Page<SensitiveWord> listPage(SensitiveWordQueryRequest request) {
        long current = request.getCurrent() <= 0 ? 1 : request.getCurrent();
        long size = request.getPageSize() <= 0 ? 10 : Math.min(request.getPageSize(), 100);

        LambdaQueryWrapper<SensitiveWord> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.like(StrUtil.isNotBlank(request.getWord()),
                        SensitiveWord::getWord, StrUtil.trim(request.getWord()))
                .eq(StrUtil.isNotBlank(request.getCategory()),
                        SensitiveWord::getCategory, request.getCategory())
                .eq(request.getStatus() != null, SensitiveWord::getStatus, request.getStatus())
                .orderByDesc(SensitiveWord::getCreateTime);
        return page(new Page<>(current, size), queryWrapper);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean addWord(SensitiveWordAddRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        String word = StrUtil.trim(request.getWord());
        ThrowUtils.throwIf(StrUtil.isBlank(word), ErrorCode.PARAMS_ERROR, "敏感词不能为空");
        ThrowUtils.throwIf(word.length() > 64, ErrorCode.PARAMS_ERROR, "敏感词长度不能超过 64");
        String category = StrUtil.blankToDefault(request.getCategory(), "other");
        String level = StrUtil.blankToDefault(request.getLevel(), "medium");

        // 逻辑删除后 word 仍占用唯一键，重新添加时复活旧记录
        SensitiveWord existing = baseMapper.selectByWordIncludeDeleted(word);
        if (existing != null) {
            if (!Integer.valueOf(1).equals(existing.getIsDelete())) {
                throw new BusinessException(ErrorCode.PARAMS_ERROR, "敏感词已存在");
            }
            baseMapper.reviveDeleted(existing.getId(), category, level);
            return true;
        }

        SensitiveWord sensitiveWord = new SensitiveWord();
        sensitiveWord.setWord(word);
        sensitiveWord.setCategory(category);
        sensitiveWord.setLevel(level);
        sensitiveWord.setHitCount(0);
        sensitiveWord.setStatus(1);
        try {
            return save(sensitiveWord);
        } catch (DuplicateKeyException e) {
            // 并发下可能刚插入同名记录，若是逻辑删除态同样复活
            SensitiveWord duplicate = baseMapper.selectByWordIncludeDeleted(word);
            if (duplicate != null && Integer.valueOf(1).equals(duplicate.getIsDelete())) {
                baseMapper.reviveDeleted(duplicate.getId(), category, level);
                return true;
            }
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "敏感词已存在");
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateWord(SensitiveWordUpdateRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        SensitiveWord existing = getById(request.getId());
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR, "敏感词不存在");

        SensitiveWord update = new SensitiveWord();
        update.setId(request.getId());
        if (request.getWord() != null) {
            String word = StrUtil.trim(request.getWord());
            ThrowUtils.throwIf(StrUtil.isBlank(word), ErrorCode.PARAMS_ERROR, "敏感词不能为空");
            ThrowUtils.throwIf(word.length() > 64, ErrorCode.PARAMS_ERROR, "敏感词长度不能超过 64");
            ThrowUtils.throwIf(existsWord(word, request.getId()), ErrorCode.PARAMS_ERROR, "敏感词已存在");
            update.setWord(word);
        }
        if (request.getCategory() != null) {
            update.setCategory(request.getCategory());
        }
        if (request.getLevel() != null) {
            update.setLevel(request.getLevel());
        }
        if (request.getStatus() != null) {
            update.setStatus(request.getStatus());
        }
        try {
            return updateById(update);
        } catch (DuplicateKeyException e) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "敏感词已存在");
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteWord(Long id) {
        ThrowUtils.throwIf(id == null, ErrorCode.PARAMS_ERROR);
        SensitiveWord existing = getById(id);
        ThrowUtils.throwIf(existing == null, ErrorCode.NOT_FOUND_ERROR, "敏感词不存在");
        return removeById(id);
    }

    @Override
    @Transactional(noRollbackFor = BusinessException.class)
    public void checkAndRecord(String content, String targetType, Long authorId) {
        if (StrUtil.isBlank(content)) {
            return;
        }
        List<SensitiveWord> words = list(new LambdaQueryWrapper<SensitiveWord>()
                .eq(SensitiveWord::getStatus, 1)
                .orderByAsc(SensitiveWord::getId));
        if (words.isEmpty()) {
            return;
        }
        for (SensitiveWord word : words) {
            String value = word.getWord();
            if (StrUtil.isBlank(value) || !content.contains(value)) {
                continue;
            }
            // 命中：计数原子 +1
            update(new LambdaUpdateWrapper<SensitiveWord>()
                    .eq(SensitiveWord::getId, word.getId())
                    .setSql("hit_count = hit_count + 1"));

            // 写待处理违规记录
            ViolationRecord record = new ViolationRecord();
            record.setTargetType(targetType);
            record.setContentSnapshot(content.length() > SNAPSHOT_MAX_LENGTH
                    ? content.substring(0, SNAPSHOT_MAX_LENGTH)
                    : content);
            record.setAuthorId(authorId);
            record.setReason("内容包含违规词");
            record.setWord(value);
            record.setStatus(0);
            violationRecordService.save(record);

            log.info("敏感词命中：word={}, targetType={}, authorId={}", value, targetType, authorId);
            // noRollbackFor 保证上面的计数与记录提交，同时拒绝本次请求
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "内容包含违规词：" + value);
        }
    }

    /**
     * 判断启用中（未逻辑删除）的敏感词是否已存在
     */
    private boolean existsWord(String word, Long excludeId) {
        LambdaQueryWrapper<SensitiveWord> queryWrapper = new LambdaQueryWrapper<SensitiveWord>()
                .eq(SensitiveWord::getWord, word);
        if (excludeId != null) {
            queryWrapper.ne(SensitiveWord::getId, excludeId);
        }
        return count(queryWrapper) > 0;
    }
}
