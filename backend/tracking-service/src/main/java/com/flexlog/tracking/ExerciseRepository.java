package com.flexlog.tracking;

import org.springframework.data.jpa.repository.JpaRepository;
import com.flexlog.tracking.models.Exercise;
import org.springframework.stereotype.Repository;

@Repository
public interface ExerciseRepository extends JpaRepository<Exercise, Integer> {
}
