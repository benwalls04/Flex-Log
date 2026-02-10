package com.flexlog.tracking;

import com.flexlog.tracking.models.Workout;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface WorkoutRepository extends JpaRepository<Workout, Integer> {
    List<Workout> findByUserId(UUID userId);
}
