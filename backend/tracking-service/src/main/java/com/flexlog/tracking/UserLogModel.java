package com.flexlog.tracking;

import jakarta.persistence.*;

@Entity
@Table(name = "user_logs")
public class UserLogModel {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Integer userId;

    @Column(name = "timestamp", nullable = false)
    private String timestamp;

    @Column(name = "exercise_id", nullable = false)
    private Integer exerciseId;

    @Column(name = "weight")
    private Double weight;

    @Column(name = "reps")
    private Integer reps;

    @Column(name = "workout_id")
    private Integer workoutId;

    @Column(name = "first")
    private Integer first;

    public UserLogModel() {}

    // Full constructor
    public UserLogModel(Long id, Integer userId, String timestamp, Integer exerciseId,
                        Double weight, Integer reps, Integer workoutId, Integer first) {
        this.id = id;
        this.userId = userId;
        this.timestamp = timestamp;
        this.exerciseId = exerciseId;
        this.weight = weight;
        this.reps = reps;
        this.workoutId = workoutId;
        this.first = first;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Integer getUserId() {
        return userId;
    }

    public void setUserId(Integer userId) {
        this.userId = userId;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public Integer getExerciseId() {
        return exerciseId;
    }

    public void setExerciseId(Integer exerciseId) {
        this.exerciseId = exerciseId;
    }

    public Double getWeight() {
        return weight;
    }

    public void setWeight(Double weight) {
        this.weight = weight;
    }

    public Integer getReps() {
        return reps;
    }

    public void setReps(Integer reps) {
        this.reps = reps;
    }

    public Integer getWorkoutId() {
        return workoutId;
    }

    public void setWorkoutId(Integer workoutId) {
        this.workoutId = workoutId;
    }

    public Integer getFirst() {
        return first;
    }

    public void setFirst(Integer first) {
        this.first = first;
    }
}