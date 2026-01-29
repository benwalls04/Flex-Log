package com.flexlog.tracking;

import com.flexlog.tracking.models.Log;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/logs")
public class UserLogController {

    private final UserLogService logService;

    @Autowired
    public UserLogController(UserLogService logService) {
        this.logService = logService;
    }

    // Get all logs for a user
    @GetMapping("/")
    public List<Log> fetchUserLogs(@RequestParam Integer userId) {
        return logService.getLogsByUserId(userId);
    }

    // Get a single log by ID
    @GetMapping("/{id}")
    public ResponseEntity<Log> getLog(@PathVariable Integer id) {
        Log log = logService.getLog(id);
        return ResponseEntity.ok(log);
    }

    // Create a new log
    @PostMapping("/")
    public ResponseEntity<Log> createUserLog(@RequestBody Log newLog) {
        Log createdLog = logService.createLog(newLog);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdLog);
    }

    // Update an existing log
    @PutMapping("/{id}")
    public ResponseEntity<Log> updateLog(@PathVariable Integer id, @RequestBody Log updatedLog) {
        Log log = logService.updateLog(id, updatedLog);
        return ResponseEntity.ok(log);
    }

    // Delete a log
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteLog(@PathVariable Integer id) {
        logService.deleteLog(id);
        return ResponseEntity.noContent().build();
    }
}