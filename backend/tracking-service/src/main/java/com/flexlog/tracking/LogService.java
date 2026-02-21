package com.flexlog.tracking;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.flexlog.tracking.models.Exercise;
import com.flexlog.tracking.models.Workout;
import com.flexlog.tracking.models.Log;
import com.flexlog.tracking.models.MuscleGroup;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.SendMessageRequest;

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
    private final WorkoutRepository workoutRepoistory;
    private final SqsClient sqsClient;
    private final String sqsQueueUrl;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Autowired
    public LogService(LogRepository logRepository, RedisSessionService redisClient, WorkoutRepository workoutRepoistory,
            ExerciseRepository exerciseRepository, SqsClient sqsClient,
            @Value("${aws.sqs.queue-url}") String sqsQueueUrl) {
        this.logRepository = logRepository;
        this.redisClient = redisClient;
        this.exerciseRepository = exerciseRepository;
        this.workoutRepoistory = workoutRepoistory;
        this.sqsClient = sqsClient;
        this.sqsQueueUrl = sqsQueueUrl;
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
        Integer workoutId = log.getWorkout().getId();
        Exercise fullExercise = exerciseRepository.findById(exerciseId)
                .orElseThrow(() -> new RuntimeException("Exercise not found: " + exerciseId));
        Workout fullWorkout = workoutRepoistory.findById(workoutId)
                .orElseThrow(() -> new RuntimeException("Workout not found: " + workoutId));
        logger.info("🔍 [REDIS DEBUG] Fetched full exercise from DB: id={}, name={}, muscleGroup={}",
                fullExercise.getId(), fullExercise.getName(), fullExercise.getMuscleGroup());

        log.setExercise(fullExercise);
        log.setWorkout(fullWorkout);

        Log savedLog = logRepository.save(log);

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

            sqsClient.sendMessage(SendMessageRequest.builder()
                    .queueUrl(sqsQueueUrl)
                    .messageBody(objectMapper.writeValueAsString(message))
                    .build());
            logger.info("✅ SQS message sent for workout_id={}, exercise_id={}", workoutId, exerciseId);
        } catch (Exception e) {
            logger.error("Failed to send SQS message for workout_id={}, exercise_id={}: {}", workoutId, exerciseId,
                    e.getMessage());
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

        if (updatedLog.getReps() != null) {
            existingLog.setReps(updatedLog.getReps());
        }
        if (updatedLog.getWeight() != null) {
            existingLog.setWeight(updatedLog.getWeight());
        }
        if (updatedLog.getFirst() != null) {
            existingLog.setFirst(updatedLog.getFirst());
        }

        return logRepository.save(existingLog);
    }
}