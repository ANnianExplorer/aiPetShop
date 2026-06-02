package com.petlumina.backend.controller.user;

import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.manager.cos.CosManager;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.util.UUID;

/**
 * 文件上传控制器
 */
@RestController
@RequestMapping("/api/v1/file")
@Slf4j
public class FileController {

    @Resource
    private CosManager cosManager;

    /** 允许的图片类型 */
    private static final String[] ALLOWED_IMAGE_TYPES = {
            "image/jpeg", "image/png", "image/gif", "image/webp"
    };

    /** 最大文件大小: 5MB */
    private static final long MAX_FILE_SIZE = 5 * 1024 * 1024;

    /**
     * 通用文件上传
     */
    @PostMapping("/upload")
    public BaseResponse<String> upload(@RequestPart("file") MultipartFile file) {
        ThrowUtils.throwIf(file == null || file.isEmpty(), ErrorCode.PARAMS_ERROR, "文件不能为空");
        ThrowUtils.throwIf(file.getSize() > MAX_FILE_SIZE, ErrorCode.PARAMS_ERROR, "文件大小不能超过5MB");

        String originalFilename = file.getOriginalFilename();
        String extension = "";
        if (originalFilename != null && originalFilename.contains(".")) {
            extension = originalFilename.substring(originalFilename.lastIndexOf("."));
        }

        String key = "petlumina/" + UUID.randomUUID().toString().replace("-", "") + extension;

        try {
            String url = cosManager.upload(key, file.getInputStream());
            log.info("文件上传成功: key={}", key);
            return ResultUtils.success(url);
        } catch (Exception e) {
            log.error("文件上传失败", e);
            throw new BusinessException(ErrorCode.OPERATION_ERROR, "文件上传失败");
        }
    }

    /**
     * 图片上传
     */
    @PostMapping("/upload/image")
    public BaseResponse<String> uploadImage(@RequestPart("file") MultipartFile file) {
        ThrowUtils.throwIf(file == null || file.isEmpty(), ErrorCode.PARAMS_ERROR, "文件不能为空");
        ThrowUtils.throwIf(file.getSize() > MAX_FILE_SIZE, ErrorCode.PARAMS_ERROR, "图片大小不能超过5MB");

        // 校验文件类型
        String contentType = file.getContentType();
        boolean isAllowed = false;
        for (String type : ALLOWED_IMAGE_TYPES) {
            if (type.equals(contentType)) {
                isAllowed = true;
                break;
            }
        }
        ThrowUtils.throwIf(!isAllowed, ErrorCode.PARAMS_ERROR, "仅支持 jpg/png/gif/webp 格式");

        String originalFilename = file.getOriginalFilename();
        String imageExtension = ".jpg";
        if (originalFilename != null && originalFilename.contains(".")) {
            imageExtension = originalFilename.substring(originalFilename.lastIndexOf("."));
        }
        String key = "petlumina/images/" + UUID.randomUUID().toString().replace("-", "") + imageExtension;

        try {
            String url = cosManager.upload(key, file.getInputStream());
            log.info("图片上传成功: key={}", key);
            return ResultUtils.success(url);
        } catch (Exception e) {
            log.error("图片上传失败", e);
            throw new BusinessException(ErrorCode.OPERATION_ERROR, "图片上传失败");
        }
    }
}
