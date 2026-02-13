package com.flexlog.tracking;

import com.flexlog.tracking.models.Exercise;
import com.flexlog.tracking.models.Log;
import com.flexlog.tracking.models.Workout;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class Controller {

    private final LogService logService;
    private final WorkoutService workoutService;
    private final ExerciseService exerciseService;

    @Autowired
    public Controller(LogService logService, WorkoutService workoutService, ExerciseService exerciseService) {
        this.logService = logService;
        this.workoutService = workoutService;
        this.exerciseService = exerciseService;
    }

    @PostMapping("/exercises/")
    public ResponseEntity<Exercise> createExercise(@RequestBody Exercise newExercise) {
        Exercise createdExercise = exerciseService.createExercise(newExercise);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdExercise);
    }

    @PostMapping("/workouts/")
    public ResponseEntity<Workout> createWorkout(@RequestBody Workout newWorkout) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UUID userId = (UUID) auth.getPrincipal();

        newWorkout.setUserId(userId);

        Workout createdWorkout = workoutService.createWorkout(newWorkout);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdWorkout);
    }

    // Get all workouts for authenticated user
    @GetMapping("/workouts/")
    public List<Workout> fetchUserWorkouts() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UUID userId = (UUID) auth.getPrincipal();

        return workoutService.getWorkoutsByUserId(userId);
    }

    // Get a single workout by ID (verifies ownership)
    @GetMapping("/workouts/{id}")
    public ResponseEntity<Workout> getWorkout(@PathVariable Integer id) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UUID userId = (UUID) auth.getPrincipal();

        Workout workout = workoutService.getWorkout(id);
        
        // Verify the workout belongs to the authenticated user
        if (!workout.getUserId().equals(userId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
        }
        
        return ResponseEntity.ok(workout);
    }

    // Get all logs for authenticated user
    @GetMapping("/logs/")
    public List<Log> fetchUserLogs() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UUID userId = (UUID) auth.getPrincipal();

        return logService.getLogsByUserId(userId);
    }

    // Get a single log by ID (verifies ownership)
    @GetMapping("/logs/{id}")
    public ResponseEntity<Log> getLog(@PathVariable Integer id) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UUID userId = (UUID) auth.getPrincipal();

        Log log = logService.getLog(id);
        
        // Verify the log belongs to the authenticated user
        if (!log.getUserId().equals(userId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
        }
        
        return ResponseEntity.ok(log);
    }

    // Create a new log
    @PostMapping("/logs/")
    public ResponseEntity<Log> createUserLog(@RequestBody Log newLog) {
        // Extract userId from JWT token
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UUID userId = (UUID) auth.getPrincipal();

        newLog.setUserId(userId);

        Log createdLog = logService.createLog(newLog);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdLog);
    }

    // Update an existing log
    @PutMapping("/logs/{id}")
    public ResponseEntity<Log> updateLog(@PathVariable Integer id, @RequestBody Log updatedLog) {
        // Extract userId from JWT token
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UUID userId = (UUID) auth.getPrincipal();

        // Verify the log belongs to the authenticated user
        Log existingLog = logService.getLog(id);
        if (!existingLog.getUserId().equals(userId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
        }

        Log log = logService.updateLog(id, updatedLog);
        return ResponseEntity.ok(log);
    }

    // Delete a log
    @DeleteMapping("/logs/{id}")
    public ResponseEntity<Void> deleteLog(@PathVariable Integer id) {
        // Extract userId from JWT token
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UUID userId = (UUID) auth.getPrincipal();

        // Verify the log belongs to the authenticated user
        Log existingLog = logService.getLog(id);
        if (!existingLog.getUserId().equals(userId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
        }

        logService.deleteLog(id);
        return ResponseEntity.noContent().build();
    }
}