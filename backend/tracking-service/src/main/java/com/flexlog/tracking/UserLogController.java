package com.flexlog.tracking;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/logs")
public class UserLogController {

    @GetMapping("/")
    public String fetchUserLogs(@RequestParam Integer userId) {
        return "index.html";
    }
}