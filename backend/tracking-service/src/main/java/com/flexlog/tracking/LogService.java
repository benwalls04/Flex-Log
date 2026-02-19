package com.flexlog.tracking;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.flexlog.tracking.models.Exercise;
import com.flexlog.tracking.models.Log;
import com.flexlog.tracking.models.MuscleGroup;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class LogService {
    private static final Logger logger = LoggerFactory.getLogger(LogService.class);

    private final LogRepository logRepository;
    private final RedisSessionService redisClient;
    private final ExerciseRepository exerciseRepository;
    private final SqsService sqsService;
    private final ObjectMapper objectMapper = new ObjectMapper();  // reused, not recreated each call

    @Autowired
    public LogService(LogRepository logRepository, RedisSessionService redisClient,
            ExerciseRepository exerciseRepository, SqsService sqsService) {
        this.logRepository = logRepository;
        this.redisClient = redisClient;
        this.exerciseRepository = exerciseRepository;
        this.sqsService = sqsService;
    }

    public Log getLog(Integer id) {
        return logRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Log not found"));
    }

    public List<Log> getAllLogs() {
        return logRepository.findAll();
    }

    public List<Log> getLogsByUserId(UUID userId) {
        return logRepository.findByUserId(userId);
    }

    public Log createLog(Log log, UUID userId, Integer workoutPosition) {
        Integer exerciseId = log.getExercise().getId();
        Exercise fullExercise = exerciseRepository.findById(exerciseId)
                .orElseThrow(() -> new RuntimeException("Exercise not found: " + exerciseId));

        logger.info("🔍 [REDIS DEBUG] Fetched full exercise from DB: id={}, name={}, muscleGroup={}",
                fullExercise.getId(), fullExercise.getName(), fullExercise.getMuscleGroup());

        log.setExercise(fullExercise);

        Log savedLog = logRepository.save(log);
        Integer workoutId = savedLog.getWorkout().getId();

        logger.info("🔍 [REDIS DEBUG] Processing log for workout_id={}, exercise_id={}", workoutId, exerciseId);

        boolean alreadyInSession = redisClient.inSession(workoutId, exerciseId);
        logger.info("🔍 [REDIS DEBUG] inSession() returned: {}", alreadyInSession);

        if (!alreadyInSession) {
            MuscleGroup muscleGroup = fullExercise.getMuscleGroup();
            logger.info("🔍 [REDIS DEBUG] Exercise NOT in session, adding to Redis. MuscleGroup: {}", muscleGroup);
            redisClient.addExerciseToSession(workoutId, exerciseId, muscleGroup);
            logger.info("✅ [REDIS DEBUG] Successfully called addExerciseToSession()");
        } else {
            logger.info("⏭️  [REDIS DEBUG] Exercise already in session, skipping Redis update");
        }

        try {
            Map<String, Object> message = new HashMap<>();
            message.put("user_id", userId.toString());
            message.put("workout_id", savedLog.getWorkout().getId());
            message.put("workout_name", savedLog.getWorkout().getName());
            message.put("exercise_id", fullExercise.getId());
            message.put("workout_position", workoutPosition);

            sqsService.sendMessage(objectMapper.writeValueAsString(message));
            logger.info("✅ SQS message sent for workout_id={}, exercise_id={}", workoutId, exerciseId);
        } catch (Exception e) {
            logger.error("Failed to send SQS message for workout_id={}, exercise_id={}: {}", workoutId, exerciseId, e.getMessage());
            // not re-throwing — SQS failure shouldn't roll back the saved log
        }

        return savedLog;
    }

    public void deleteLog(Integer id) {
        logRepository.deleteById(id);
    }

    public Log updateLog(Integer id, Log updatedLog) {
        Log existingLog = logRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Log not found"));

        existingLog.setReps(updatedLog.getReps());
        existingLog.setWeight(updatedLog.getWeight());
        existingLog.setExercise(updatedLog.getExercise());
        existingLog.setFirst(updatedLog.getFirst());

        return logRepository.save(existingLog);
    }
}