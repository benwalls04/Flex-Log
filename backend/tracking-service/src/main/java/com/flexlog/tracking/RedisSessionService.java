package com.flexlog.tracking;

import com.flexlog.tracking.models.MuscleGroup;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Service
public class RedisSessionService {

    private static final int SESSION_TTL_SECONDS = 18000;

    private final StringRedisTemplate redisTemplate;

    @Autowired
    public RedisSessionService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
     * Updates Redis session state when an exercise is added to a workout.
     * Mirrors the Python sessions.py:add_exercise_to_session() logic.
     */
    public void addExerciseToSession(Integer workoutId, Integer exerciseId, MuscleGroup muscleGroup) {
        if (workoutId == null || exerciseId == null || muscleGroup == null) {
            return;
        }

        // 1. Add exercise ID to the set of exercises in this session
        String exercisesKey = String.format("session:%d:exercises", workoutId);
        redisTemplate.opsForSet().add(exercisesKey, exerciseId.toString());
        redisTemplate.expire(exercisesKey, SESSION_TTL_SECONDS, TimeUnit.SECONDS);

        // 2. Increment the exercise count for this session
        String countKey = String.format("session:%d:count", workoutId);
        redisTemplate.opsForValue().increment(countKey);
        redisTemplate.expire(countKey, SESSION_TTL_SECONDS, TimeUnit.SECONDS);

        // 3. Increment the muscle group count for this session
        String muscleCountsKey = String.format("session:%d:muscle_counts", workoutId);
        String muscleGroupName = muscleGroup.name(); // "chest", "back", etc.
        redisTemplate.opsForHash().increment(muscleCountsKey, muscleGroupName, 1);
        redisTemplate.expire(muscleCountsKey, SESSION_TTL_SECONDS, TimeUnit.SECONDS);
    }

    public Boolean inSession(Integer workoutId, Integer exerciseId) {
        String exercisesKey = String.format("session:%d:exercises", workoutId);
        return redisTemplate.opsForSet().isMember(exercisesKey, exerciseId.toString());
    }
}