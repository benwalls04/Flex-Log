package com.flexlog.tracking;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ApplicationContext;

@SpringBootApplication
public class TrackingApplication {
	public static void main(String[] args) {
		ApplicationContext context = SpringApplication.run(TrackingApplication.class, args);
		//context.getBean();
	}
}
