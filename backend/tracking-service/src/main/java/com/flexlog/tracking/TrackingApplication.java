package com.flexlog.tracking;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.core.env.Environment;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class TrackingApplication {

	public static void main(String[] args) {
		SpringApplication.run(TrackingApplication.class, args);
	}

	// Optional: Print Spring properties after Spring context loads
	@Bean
	public CommandLineRunner printSpringProperties(Environment env) {
		return args -> {
			System.out.println("\n========== SPRING PROPERTIES ==========");
			System.out.println("spring.profiles.active = " + env.getProperty("spring.profiles.active"));
			System.out.println("spring.datasource.url = " + env.getProperty("spring.datasource.url"));
			System.out.println("spring.datasource.username = " + env.getProperty("spring.datasource.username"));
			System.out.println("spring.datasource.password = ***MASKED***");
			System.out.println("=======================================\n");
		};
	}
}