
package com.flexlog.tracking;

import com.flexlog.tracking.models.Exercise;
import com.flexlog.tracking.models.Log;
import com.flexlog.tracking.models.Workout;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/")
public class Controller {

  public static final String USER_ID_HEADER = "X-User-Id";

  private final LogService logService;
  private final WorkoutService workoutService;
  private final ExerciseService exerciseService;

  @Autowired
  public Controller(LogService logService, WorkoutService workoutService, ExerciseService exerciseService) {
    this.logService = logService;
    this.workoutService = workoutService;
    this.exerciseService = exerciseService;
  }

  @GetMapping("/exercises/")
  public List<Exercise> getAllExercises() {
    return exerciseService.getAllExercises();
  }

  @PostMapping("/exercises/")
  public ResponseEntity<Exercise> createExercise(@RequestBody Exercise newExercise) {
    Exercise createdExercise = exerciseService.createExercise(newExercise);
    return ResponseEntity.status(HttpStatus.CREATED).body(createdExercise);
  }

  @PostMapping("/workouts/")
  public ResponseEntity<Workout> createWorkout(
      @RequestHeader(USER_ID_HEADER) UUID userId,
      @RequestBody Workout newWorkout) {
    newWorkout.setUserId(userId);

    Workout createdWorkout = workoutService.createWorkout(newWorkout);
    return ResponseEntity.status(HttpStatus.CREATED).body(createdWorkout);
  }

  @GetMapping("/workouts/")
  public List<Workout> fetchUserWorkouts(@RequestHeader(USER_ID_HEADER) UUID userId) {
    return workoutService.getWorkoutsByUserId(userId);
  }

  @GetMapping("/workouts/{id}")
  public ResponseEntity<Workout> getWorkout(
      @RequestHeader(USER_ID_HEADER) UUID userId,
      @PathVariable Integer id) {
    Workout workout = workoutService.getWorkout(id);

    // Verify the workout belongs to the authenticated user
    if (!workout.getUserId().equals(userId)) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
    }

    return ResponseEntity.ok(workout);
  }

  @GetMapping("/logs/")
  public List<Log> fetchUserLogs(@RequestHeader(USER_ID_HEADER) UUID userId) {
    return logService.getLogsByUserId(userId);
  }

  @GetMapping("/logs/{id}")
  public ResponseEntity<Log> getLog(
      @RequestHeader(USER_ID_HEADER) UUID userId,
      @PathVariable Integer id) {
    Log log = logService.getLog(id);

    // Verify the log belongs to the authenticated user
    if (!log.getUserId().equals(userId)) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
    }

    return ResponseEntity.ok(log);
  }

  @PostMapping("/logs/")
  public ResponseEntity<Log> createUserLog(
      @RequestHeader(USER_ID_HEADER) UUID userId,
      @RequestBody Log newLog,
      @RequestParam Integer workoutPosition) {
    newLog.setUserId(userId);

    Log createdLog = logService.createLog(newLog, userId, workoutPosition);
    return ResponseEntity.status(HttpStatus.CREATED).body(createdLog);
  }

  @PutMapping("/logs/{id}")
  public ResponseEntity<Log> updateLog(
      @RequestHeader(USER_ID_HEADER) UUID userId,
      @PathVariable Integer id,
      @RequestBody Log updatedLog) {
    Log existingLog = logService.getLog(id);
    if (!existingLog.getUserId().equals(userId)) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
    }

    Log log = logService.updateLog(id, updatedLog);
    return ResponseEntity.ok(log);
  }

  @DeleteMapping("/logs/{id}")
  public ResponseEntity<Void> deleteLog(
      @RequestHeader(USER_ID_HEADER) UUID userId,
      @PathVariable Integer id) {
    Log existingLog = logService.getLog(id);
    if (!existingLog.getUserId().equals(userId)) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
    }

    logService.deleteLog(id);
    return ResponseEntity.noContent().build();
  }
}