package com.flexlog.tracking;

import com.flexlog.tracking.models.MuscleGroup;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Service
public class RedisSessionService {
    private static final Logger logger = LoggerFactory.getLogger(RedisSessionService.class);
    private static final int SESSION_TTL_SECONDS = 18000;

    private final StringRedisTemplate redisTemplate;

    @Autowired
    public RedisSessionService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
        logger.info("✅ RedisSessionService initialized with StringRedisTemplate");
    }

    /**
     * Updates Redis session state when an exercise is added to a workout.
     * Mirrors the Python sessions.py:add_exercise_to_session() logic.
     */
    public void addExerciseToSession(Integer workoutId, Integer exerciseId, MuscleGroup muscleGroup) {
        logger.info("📝 [REDIS] addExerciseToSession called: workout_id={}, exercise_id={}, muscle_group={}",
                workoutId, exerciseId, muscleGroup);

        if (workoutId == null || exerciseId == null || muscleGroup == null) {
            logger.warn("⚠️  [REDIS] Null values detected, skipping Redis update");
            return;
        }

        try {
            // 1. Add exercise ID to the set of exercises in this session
            String exercisesKey = String.format("session:%d:exercises", workoutId);
            logger.info("📝 [REDIS] Adding to SET: {} → {}", exercisesKey, exerciseId);
            Long addResult = redisTemplate.opsForSet().add(exercisesKey, exerciseId.toString());
            logger.info("📝 [REDIS] SET add result: {} (1=new, 0=already exists)", addResult);
            redisTemplate.expire(exercisesKey, SESSION_TTL_SECONDS, TimeUnit.SECONDS);

            // 2. Increment the exercise count for this session
            String countKey = String.format("session:%d:count", workoutId);
            logger.info("📝 [REDIS] Incrementing STRING: {}", countKey);
            Long newCount = redisTemplate.opsForValue().increment(countKey);
            logger.info("📝 [REDIS] New count value: {}", newCount);
            redisTemplate.expire(countKey, SESSION_TTL_SECONDS, TimeUnit.SECONDS);

            // 3. Increment the muscle group count for this session
            String muscleCountsKey = String.format("session:%d:muscle_counts", workoutId);
            String muscleGroupName = muscleGroup.name();
            logger.info("📝 [REDIS] Incrementing HASH: {} → field: {}", muscleCountsKey, muscleGroupName);
            Long newMuscleCount = redisTemplate.opsForHash().increment(muscleCountsKey, muscleGroupName, 1);
            logger.info("📝 [REDIS] New muscle count for {}: {}", muscleGroupName, newMuscleCount);
            redisTemplate.expire(muscleCountsKey, SESSION_TTL_SECONDS, TimeUnit.SECONDS);

            logger.info("✅ [REDIS] Successfully updated all Redis keys for workout {}", workoutId);
        } catch (Exception e) {
            logger.error("❌ [REDIS] ERROR updating Redis: {}", e.getMessage(), e);
        }
    }

    public Boolean inSession(Integer workoutId, Integer exerciseId) {
        String exercisesKey = String.format("session:%d:exercises", workoutId);
        logger.info("🔍 [REDIS] Checking if exercise in session: key={}, exercise_id={}", exercisesKey, exerciseId);

        try {
            Boolean isMember = redisTemplate.opsForSet().isMember(exercisesKey, exerciseId.toString());
            logger.info("🔍 [REDIS] isMember result: {}", isMember);
            return isMember;
        } catch (Exception e) {
            logger.error("❌ [REDIS] ERROR checking inSession: {}", e.getMessage(), e);
            return false; // Default to false on error so we try to add
        }
    }
}