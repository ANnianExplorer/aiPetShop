package com.petlumina.backend.constant;

/**
 * Redis Key 常量
 */
public interface RedisConstant {

    /** 验证码前缀 */
    String VERIFY_CODE_PREFIX = "petlumina:verify_code:";

    /** 限流前缀 */
    String RATE_LIMIT_PREFIX = "petlumina:rate_limit:";

    /** 验证码有效期 (秒) */
    long VERIFY_CODE_EXPIRE = 300;
}
