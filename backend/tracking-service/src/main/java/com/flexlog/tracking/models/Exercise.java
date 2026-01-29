// Exercise.java
package com.flexlog.tracking.models;

import jakarta.persistence.*;
import java.util.Set;

@Entity
@Table(name = "exercises")
public class Exercise {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "variant")
    private String variant;

    @Column(name = "name")
    private String name;

    @Column(name = "muscle_group")
    @Enumerated(EnumType.STRING)
    private MuscleGroup muscleGroup;

    @Column(name = "machine_type")
    @Enumerated(EnumType.STRING)
    private MachineType machineType;

    @Column(name = "exercise_type")
    @Enumerated(EnumType.STRING)
    private ExerciseType exerciseType;

    @OneToMany(mappedBy = "exercise")
    private Set<Log> logs;

    // Constructors
    public Exercise() {}

    // Getters and Setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public String getVariant() { return variant; }
    public void setVariant(String variant) { this.variant = variant; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public MuscleGroup getMuscleGroup() { return muscleGroup; }
    public void setMuscleGroup(MuscleGroup muscleGroup) { this.muscleGroup = muscleGroup; }

    public MachineType getMachineType() { return machineType; }
    public void setMachineType(MachineType machineType) { this.machineType = machineType; }

    public ExerciseType getExerciseType() { return exerciseType; }
    public void setExerciseType(ExerciseType exerciseType) { this.exerciseType = exerciseType; }

    public Set<Log> getLogs() { return logs; }
    public void setLogs(Set<Log> logs) { this.logs = logs; }
}

