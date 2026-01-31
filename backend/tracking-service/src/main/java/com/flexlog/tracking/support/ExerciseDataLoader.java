package com.flexlog.tracking.support;

import com.flexlog.tracking.ExerciseRepository;
import com.flexlog.tracking.models.Exercise;
import jakarta.annotation.PostConstruct;
import org.springframework.context.annotation.Profile;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;

import java.io.InputStream;
import java.util.List;


@Component
@Profile("test")
public class ExerciseDataLoader {

    private final ExerciseRepository repository;
    private final ObjectMapper objectMapper;

    public ExerciseDataLoader(
            ExerciseRepository repository,
            ObjectMapper objectMapper
    ) {
        this.repository = repository;
        this.objectMapper = objectMapper;
    }

    @PostConstruct
    public void load() throws Exception {
        if (repository.count() > 0) {
            return;
        }

        InputStream is = new ClassPathResource(
                "data/exercises.json"
        ).getInputStream();

        List<Exercise> exercises = objectMapper.readValue(
                is,
                new TypeReference<List<Exercise>>() {}
        );

        repository.saveAll(exercises);
    }
}
