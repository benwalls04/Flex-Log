package com.flexlog.tracking;

@RestController
@RequestMapping("/api/logs")
public class UserLogController {

    @GetMapping("/")
    public String fetchUserLogs(integer userId) {
        return "Hello World";
    }
}
