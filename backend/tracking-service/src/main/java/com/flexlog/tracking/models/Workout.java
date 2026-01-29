// Workout.java
package com.flexlog.tracking.models;

import jakarta.persistence.*;
import java.util.Set;

@Entity
@Table(name = "workouts")
public class Workout {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @Column(name = "name")
    private String name;

    @Column(name = "date")
    private String date;

    @OneToMany(mappedBy = "workout")
    private Set<Log> logs;

    // Constructors
    public Workout() {}

    // Getters and Setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDate() { return date; }
    public void setDate(String date) { this.date = date; }

    public Set<Log> getLogs() { return logs; }
    public void setLogs(Set<Log> logs) { this.logs = logs; }
}