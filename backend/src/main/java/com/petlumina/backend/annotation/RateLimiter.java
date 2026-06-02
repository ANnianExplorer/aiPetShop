package com.petlumina.backend.annotation;

import java.lang.annotation.*;

/**
 * 接口限流注解
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface RateLimiter {

    /** 限流 key */
    String key() default "";

    /** 时间窗口 (秒) */
    int time() default 60;

    /** 最大请求数 */
    int count() default 10;

    /** 限流提示消息 */
    String message() default "请求过于频繁";
}
