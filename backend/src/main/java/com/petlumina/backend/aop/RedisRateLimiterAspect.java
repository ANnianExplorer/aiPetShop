package com.petlumina.backend.aop;

import cn.dev33.satoken.stp.StpUtil;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.constant.RedisConstant;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.exception.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.Collections;

/**
 * Redis 限流切面
 */
@Slf4j
@Aspect
@Component
public class RedisRateLimiterAspect {

    @Resource
    private StringRedisTemplate stringRedisTemplate;

    private static final String LUA_SCRIPT =
            "local key = KEYS[1] " +
            "local limit = tonumber(ARGV[1]) " +
            "local expire = tonumber(ARGV[2]) " +
            "local current = tonumber(redis.call('get', key) or '0') " +
            "if current + 1 > limit then " +
            "  return 0 " +
            "else " +
            "  redis.call('incrby', key, 1) " +
            "  if current == 0 then " +
            "    redis.call('expire', key, expire) " +
            "  end " +
            "  return 1 " +
            "end";

    @Around("@annotation(rateLimiter)")
    public Object doAround(ProceedingJoinPoint joinPoint, RateLimiter rateLimiter) throws Throwable {
        String key = rateLimiter.key();
        int time = rateLimiter.time();
        int count = rateLimiter.count();
        String message = rateLimiter.message();

        // 获取用户标识
        String userId;
        try {
            userId = StpUtil.getLoginId().toString();
        } catch (Exception e) {
            userId = "anonymous";
        }

        String redisKey = RedisConstant.RATE_LIMIT_PREFIX + key + ":" + userId;

        try {
            DefaultRedisScript<Long> script = new DefaultRedisScript<>(LUA_SCRIPT, Long.class);
            Long result = stringRedisTemplate.execute(script,
                    Collections.singletonList(redisKey),
                    String.valueOf(count),
                    String.valueOf(time));

            if (result != null && result == 0) {
                throw new BusinessException(ErrorCode.TOO_MANY_REQUEST, message);
            }
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.warn("限流服务异常，放行请求: {}", e.getMessage());
        }

        return joinPoint.proceed();
    }
}
