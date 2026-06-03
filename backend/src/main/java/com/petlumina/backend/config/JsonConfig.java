package com.petlumina.backend.config;

import com.fasterxml.jackson.databind.ser.std.ToStringSerializer;
import org.springframework.boot.autoconfigure.jackson.Jackson2ObjectMapperBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.text.SimpleDateFormat;

/**
 * JSON 序列化配置
 * - Long → String 防止 JS 精度丢失
 * - Date → yyyy-MM-dd HH:mm:ss 格式
 */
@Configuration
public class JsonConfig {

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {
        return builder -> {
            // Long 转 String 防止 JS 大数字精度丢失
            builder.serializerByType(Long.class, ToStringSerializer.instance);
            builder.serializerByType(Long.TYPE, ToStringSerializer.instance);
            // Date 全局格式化
            builder.simpleDateFormat("yyyy-MM-dd HH:mm:ss");
        };
    }
}
