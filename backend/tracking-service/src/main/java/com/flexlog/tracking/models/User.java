// User.java
package com.flexlog.tracking.models;

import jakarta.persistence.*;
import java.util.Set;

@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "username")
    private String username;

    @OneToMany(mappedBy = "user")
    private Set<Workout> workouts;

    @OneToMany(mappedBy = "user")
    private Set<Log> logs;

    // Constructors
    public User() {}

    public User(Integer id, String username) {
        this.id = id;
        this.username = username;
    }

    // Getters and Setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public Set<Workout> getWorkouts() { return workouts; }
    public void setWorkouts(Set<Workout> workouts) { this.workouts = workouts; }

    public Set<Log> getLogs() { return logs; }
    public void setLogs(Set<Log> logs) { this.logs = logs; }
}