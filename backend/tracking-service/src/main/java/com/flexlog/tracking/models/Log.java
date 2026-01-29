package com.flexlog.tracking.models;

import jakarta.persistence.*;

@Entity
@Table(name = "logs")
public class Log {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne
    @JoinColumn(name="exercise_id", nullable = false)
    private Exercise exercise;

    @ManyToOne
    @JoinColumn(name="workout_id")
    private Workout workout;

    @Column(name = "timestamp", nullable = false)
    private String timestamp;

    @Column(name = "weight")
    private Double weight;

    @Column(name = "reps")
    private Integer reps;

    @Column(name = "first")
    private Integer first;

    public Log() {}

    // Full constructor with relationships
    public Log(Integer id, User user, String timestamp, Exercise exercise, Workout workout,
               Double weight, Integer reps, Integer first) {
        this.id = id;
        this.user = user;
        this.timestamp = timestamp;
        this.exercise = exercise;
        this.workout = workout;
        this.weight = weight;
        this.reps = reps;
        this.first = first;
    }

    public Integer getId() {
        return id;
    }

    public User getUser() {
        return user;
    }

    public Exercise getExercise() {
        return exercise;
    }

    public void setExercise(Exercise exercise) {
        this.exercise = exercise;
    }

    public Workout getWorkout() {
        return workout;
    }

    public String getTimestamp() {
        return timestamp;
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

    public Integer getFirst() {
        return first;
    }

    public void setFirst(Integer first) {
        this.first = first;
    }
}