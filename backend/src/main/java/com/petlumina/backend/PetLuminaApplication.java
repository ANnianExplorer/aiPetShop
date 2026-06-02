package com.petlumina.backend;

import lombok.extern.slf4j.Slf4j;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.core.env.ConfigurableEnvironment;

@SpringBootApplication
@MapperScan("com.petlumina.backend.mapper")
@Slf4j
public class PetLuminaApplication {

    public static void main(String[] args) {
//        SpringApplication.run(PetLuminaApplication.class, args);
        SpringApplication application = new SpringApplication(PetLuminaApplication.class);
        ConfigurableEnvironment env = application.run(args).getEnvironment();
        log.info("启动成功！！");
        log.info("knife4j API URL: \thttp://localhost:{}/api/doc.html", env.getProperty("server.port"));
    }
}
