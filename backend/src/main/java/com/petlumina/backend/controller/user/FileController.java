package com.petlumina.backend.controller.user;

import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.CosConstant;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.manager.cos.CosManager;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
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

    /** 允许的图片后缀（小写） */
    private static final List<String> ALLOWED_IMAGE_SUFFIX = Arrays.asList("jpg", "jpeg", "png", "gif", "webp");

    /** 允许的图片 MIME 类型 */
    private static final List<String> ALLOWED_IMAGE_TYPES = Arrays.asList(
            "image/jpeg", "image/png", "image/gif", "image/webp"
    );

    /** 最大文件大小: 5MB */
    private static final long MAX_FILE_SIZE = 5 * 1024 * 1024;

    /**
     * 通用文件上传
     * @param category 分类目录（如 common, post/image 等），不传则用 common
     */
    @PostMapping("/upload")
    public BaseResponse<String> upload(@RequestPart("file") MultipartFile file,
                                       @RequestParam(required = false, defaultValue = CosConstant.COMMON) String category) {
        ThrowUtils.throwIf(file == null || file.isEmpty(), ErrorCode.PARAMS_ERROR, "文件不能为空");
        ThrowUtils.throwIf(file.getSize() > MAX_FILE_SIZE, ErrorCode.PARAMS_ERROR, "文件大小不能超过5MB");

        String suffix = getFileSuffixSafe(file.getOriginalFilename());
        String key = category + "/" + UUID.randomUUID().toString().replace("-", "") + "." + suffix;

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
     * 图片上传（含魔数校验）
     * @param category 分类目录（如 post/image, pet/image, log/image 等），不传则用 common
     */
    @PostMapping("/upload/image")
    public BaseResponse<String> uploadImage(@RequestPart("file") MultipartFile file,
                                            @RequestParam(required = false, defaultValue = CosConstant.COMMON) String category) {
        ThrowUtils.throwIf(file == null || file.isEmpty(), ErrorCode.PARAMS_ERROR, "文件不能为空");
        ThrowUtils.throwIf(file.getSize() > MAX_FILE_SIZE, ErrorCode.PARAMS_ERROR, "图片大小不能超过5MB");

        // 1. 校验后缀
        String suffix = getFileSuffixSafe(file.getOriginalFilename());
        ThrowUtils.throwIf(!ALLOWED_IMAGE_SUFFIX.contains(suffix),
                ErrorCode.PARAMS_ERROR, "仅支持 jpg/jpeg/png/gif/webp 格式");

        // 2. 校验 MIME 类型
        String contentType = file.getContentType();
        ThrowUtils.throwIf(!ALLOWED_IMAGE_TYPES.contains(contentType),
                ErrorCode.PARAMS_ERROR, "文件类型不合法");

        // 3. 魔数校验
        validateImageMagicBytes(file);

        // 4. 生成 key 并上传
        String key = category + "/" + UUID.randomUUID().toString().replace("-", "") + "." + suffix;

        File tempFile = null;
        try {
            tempFile = File.createTempFile("upload_", "." + suffix);
            file.transferTo(tempFile);

            // TODO: 后续可接入 COS CI 图片处理（webp 压缩 + 缩略图生成）

            String url = cosManager.uploadFile(key, tempFile);
            log.info("图片上传成功: key={}", key);
            return ResultUtils.success(url);
        } catch (Exception e) {
            log.error("图片上传失败", e);
            throw new BusinessException(ErrorCode.OPERATION_ERROR, "图片上传失败");
        } finally {
            deleteTempFile(tempFile);
        }
    }

    /**
     * 通过文件魔数校验真实文件类型
     */
    private void validateImageMagicBytes(MultipartFile file) {
        try {
            byte[] header = new byte[8];
            int readBytes = file.getInputStream().read(header);
            ThrowUtils.throwIf(readBytes < 3, ErrorCode.PARAMS_ERROR, "文件内容过短，无法识别类型");

            String hex = bytesToHex(header).toUpperCase(Locale.ROOT);

            boolean isJpeg = hex.startsWith("FFD8FF");
            boolean isPng = hex.startsWith("89504E47");
            boolean isWebp = hex.startsWith("52494646");
            boolean isGif = hex.startsWith("47494638");

            ThrowUtils.throwIf(!(isJpeg || isPng || isWebp || isGif),
                    ErrorCode.PARAMS_ERROR, "文件内容不是有效的图片格式");
        } catch (BusinessException e) {
            throw e;
        } catch (IOException e) {
            log.error("读取文件头失败", e);
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "文件校验失败");
        }
    }

    private String getFileSuffixSafe(String filename) {
        if (filename == null || filename.trim().isEmpty()) {
            return "bin";
        }
        int lastDot = filename.lastIndexOf('.');
        if (lastDot == -1 || lastDot == filename.length() - 1) {
            return "bin";
        }
        return filename.substring(lastDot + 1).trim().toLowerCase(Locale.ROOT);
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02X", b));
        }
        return sb.toString();
    }

    private void deleteTempFile(File file) {
        if (file != null && file.exists()) {
            boolean deleted = file.delete();
            if (!deleted) {
                log.warn("临时文件删除失败: {}", file.getAbsolutePath());
            }
        }
    }
}
