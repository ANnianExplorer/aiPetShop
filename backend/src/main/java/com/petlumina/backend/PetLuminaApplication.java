package com.petlumina.backend;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.petlumina.backend.mapper")
public class PetLuminaApplication {

    public static void main(String[] args) {
        SpringApplication.run(PetLuminaApplication.class, args);
    }
}
