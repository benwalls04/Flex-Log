package com.flexlog.tracking;

import com.flexlog.tracking.models.Workout;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
public class WorkoutService {
    private final WorkoutRepository repository;

    @Autowired
    public WorkoutService(WorkoutRepository repository) {
        this.repository = repository;
    }

    public Workout createWorkout(Workout workout) {
        return repository.save(workout);
    }

    public List<Workout> getWorkoutsByUserId(UUID userId) {
        return repository.findByUserId(userId);
    }

    public Workout getWorkout(Integer id) {
        return repository.findById(id)
                .orElseThrow(() -> new RuntimeException("Workout not found"));
    }
}
