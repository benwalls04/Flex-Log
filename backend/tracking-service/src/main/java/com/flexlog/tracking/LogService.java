package com.flexlog.tracking;

import com.flexlog.tracking.models.Exercise;
import com.flexlog.tracking.models.Log;
import com.flexlog.tracking.models.MuscleGroup;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.UUID;

@Service
public class LogService {
    private final LogRepository logRepository;
    private final RedisSessionService redisClient;

    @Autowired
    public LogService(LogRepository logRepository, RedisSessionService redisClient) {
        this.logRepository = logRepository;
        this.redisClient = redisClient;
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
        Log savedLog = logRepository.save(log);
        Integer workoutId = savedLog.getWorkout().getId();
        Exercise exercise = savedLog.getExercise();
        Integer exerciseId = exercise.getId();
        /*
         * if (!redisClient.inSession(workoutId, exerciseId)) {
         * MuscleGroup muscleGroup = exercise.getMuscleGroup();
         * redisClient.addExerciseToSession(workoutId, exerciseId, muscleGroup);
         * }
         */
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
