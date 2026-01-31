package com.flexlog.tracking;

import com.flexlog.tracking.models.Exercise;
import com.flexlog.tracking.models.Log;
import com.flexlog.tracking.models.User;
import com.flexlog.tracking.models.Workout;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
public class Controller {

    private final LogService logService;
    private final WorkoutService workoutService;
    private final ExerciseService exerciseService;
    private final UserService userService;

    @Autowired
    public Controller(LogService logService, WorkoutService workoutService, ExerciseService exerciseService, UserService userService) {
        this.logService = logService;
        this.workoutService = workoutService;
        this.exerciseService = exerciseService;
        this.userService = userService;
    }

    @PostMapping("/users/")
    public ResponseEntity<User> createUser(@RequestBody User newUser) {
        User createdUser = userService.createUser(newUser);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdUser);
    }

    @PostMapping("/exercises/")
    public ResponseEntity<Exercise> createExercise(@RequestBody Exercise newExercise) {
        Exercise createdExercise = exerciseService.createExercise(newExercise);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdExercise);
    }

    @PostMapping("/workouts/")
    public ResponseEntity<Workout> createWorkout(@RequestBody Workout newWorkout) {
        Workout createdWorkout = workoutService.createWorkout(newWorkout);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdWorkout);
    }

    // Get all logs for a user
    @GetMapping("/logs/")
    public List<Log> fetchUserLogs(@RequestParam Integer userId) {
        return logService.getLogsByUserId(userId);
    }

    // Get a single log by ID
    @GetMapping("/logs/{id}")
    public ResponseEntity<Log> getLog(@PathVariable Integer id) {
        Log log = logService.getLog(id);
        return ResponseEntity.ok(log);
    }

    // Create a new log
    @PostMapping("/logs/")
    public ResponseEntity<Log> createUserLog(@RequestBody Log newLog) {
        Log createdLog = logService.createLog(newLog);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdLog);
    }

    // Update an existing log
    @PutMapping("/logs/{id}")
    public ResponseEntity<Log> updateLog(@PathVariable Integer id, @RequestBody Log updatedLog) {
        Log log = logService.updateLog(id, updatedLog);
        return ResponseEntity.ok(log);
    }

    // Delete a log
    @DeleteMapping("/logs/{id}")
    public ResponseEntity<Void> deleteLog(@PathVariable Integer id) {
        logService.deleteLog(id);
        return ResponseEntity.noContent().build();
    }
}