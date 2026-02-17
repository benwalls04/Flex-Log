package com.flexlog.tracking;

import com.flexlog.tracking.models.Exercise;
import com.flexlog.tracking.models.Log;
import com.flexlog.tracking.models.MuscleGroup;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.UUID;

@Service
public class LogService {
    private static final Logger logger = LoggerFactory.getLogger(LogService.class);

    private final LogRepository logRepository;
    private final RedisSessionService redisClient;
    private final ExerciseRepository exerciseRepository;

    @Autowired
    public LogService(LogRepository logRepository, RedisSessionService redisClient,
            ExerciseRepository exerciseRepository) {
        this.logRepository = logRepository;
        this.redisClient = redisClient;
        this.exerciseRepository = exerciseRepository;
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

    public Log createLog(Log log) {
        Integer exerciseId = log.getExercise().getId();
        Exercise fullExercise = exerciseRepository.findById(exerciseId)
                .orElseThrow(() -> new RuntimeException("Exercise not found: " + exerciseId));

        logger.info("🔍 [REDIS DEBUG] Fetched full exercise from DB: id={}, name={}, muscleGroup={}",
                fullExercise.getId(), fullExercise.getName(), fullExercise.getMuscleGroup());

        // Replace the partial exercise object with the complete one
        log.setExercise(fullExercise);

        // Now save the log with the complete exercise reference
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
