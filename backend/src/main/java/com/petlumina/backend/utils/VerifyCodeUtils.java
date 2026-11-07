package com.petlumina.backend.utils;

import cn.hutool.core.util.StrUtil;

import java.security.SecureRandom;

/**
 * 验证码生成工具。
 *
 * <p>默认生成 6 位随机数字；只有在配置了 {@code petlumina.auth.fixed-verify-code}
 * （本地开发 / 自动化测试）时才返回固定值。生产环境该配置留空，保证验证码不可预测。</p>
 */
public final class VerifyCodeUtils {

    /** 默认验证码位数 */
    public static final int DEFAULT_LENGTH = 6;

    private static final SecureRandom RANDOM = new SecureRandom();

    private VerifyCodeUtils() {
    }

    /**
     * 生成验证码：固定码非空则原样返回，否则生成 {@link #DEFAULT_LENGTH} 位随机数字。
     *
     * @param fixedCode 配置里的固定码，可为 null / 空串
     * @return 验证码字符串
     */
    public static String generate(String fixedCode) {
        if (StrUtil.isNotBlank(fixedCode)) {
            return fixedCode.trim();
        }
        return randomDigits(DEFAULT_LENGTH);
    }

    /**
     * 生成指定长度的随机数字串（不足位数时前补 0）。
     *
     * @param length 长度，必须大于 0
     * @return 纯数字字符串
     */
    public static String randomDigits(int length) {
        if (length <= 0) {
            throw new IllegalArgumentException("length must be positive");
        }
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append(RANDOM.nextInt(10));
        }
        return sb.toString();
    }
}
