package com.petlumina.backend.utils;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 验证码生成：默认必须随机，只有显式配置固定码时才固定。
 */
class VerifyCodeUtilsTest {

    @Test
    @DisplayName("配置了固定码时原样返回（两端空白被裁掉）")
    void usesFixedCodeWhenConfigured() {
        assertEquals("123456", VerifyCodeUtils.generate("123456"));
        assertEquals("8888", VerifyCodeUtils.generate("  8888  "));
    }

    @Test
    @DisplayName("未配置固定码时生成 6 位纯数字")
    void generatesRandomCodeByDefault() {
        String code = VerifyCodeUtils.generate(null);
        assertEquals(VerifyCodeUtils.DEFAULT_LENGTH, code.length());
        assertTrue(code.matches("\\d{6}"), "验证码必须全是数字，实际: " + code);
        assertEquals(6, VerifyCodeUtils.generate("").length());
        assertEquals(6, VerifyCodeUtils.generate("   ").length());
    }

    @Test
    @DisplayName("随机码不是常量：1000 次生成至少出现 900 个不同值")
    void randomCodesAreNotConstant() {
        Set<String> seen = new HashSet<>();
        for (int i = 0; i < 1000; i++) {
            seen.add(VerifyCodeUtils.generate(null));
        }
        assertTrue(seen.size() > 900, "随机码重复过多: " + seen.size());
    }

    @Test
    @DisplayName("指定位数按位生成")
    void honoursRequestedLength() {
        assertEquals(4, VerifyCodeUtils.randomDigits(4).length());
        assertEquals(8, VerifyCodeUtils.randomDigits(8).length());
    }

    @Test
    @DisplayName("非法位数直接报错，不做静默降级")
    void rejectsNonPositiveLength() {
        assertThrows(IllegalArgumentException.class, () -> VerifyCodeUtils.randomDigits(0));
        assertThrows(IllegalArgumentException.class, () -> VerifyCodeUtils.randomDigits(-1));
    }
}
