package com.flexlog.tracking;

import com.flexlog.tracking.models.Workout;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

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
}
