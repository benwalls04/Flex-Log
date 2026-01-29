package com.flexlog.tracking;
import com.flexlog.tracking.models.Log;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class UserLogService {
    private final UserLogRepository logRepository;

    @Autowired
    public UserLogService(UserLogRepository logRepository) {
        this.logRepository = logRepository;
    }
    public Log getLog(Integer id) {
        return logRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Log not found"));
    }

    public List<Log> getAllLogs() {
        return logRepository.findAll();
    }

    public List<Log> getLogsByUserId(Integer userId) {
        return logRepository.findByUserId(userId);
    }

    public Log createLog(Log log) {
        return logRepository.save(log);
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
