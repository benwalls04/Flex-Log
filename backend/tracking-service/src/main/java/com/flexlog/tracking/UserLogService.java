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
    public Log getLog(Long id) {
        return logRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Log not found"));
    }

    public List<Log> getAllLogs() {
        return logRepository.findAll();
    }

    public Log createLog(Log log) {
        return logRepository.save(log);
    }

    public void deleteLog(Long id) {
        logRepository.deleteById(id);
    }
}
