package com.flexlog.tracking;

import com.flexlog.tracking.models.Exercise;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ExerciseService {

    private final ExerciseRepository repository;

    @Autowired
    public ExerciseService(ExerciseRepository repository){
        this.repository = repository;
    }

    public Exercise createExercise(Exercise exercise) {
        return repository.save(exercise);
    }
}
