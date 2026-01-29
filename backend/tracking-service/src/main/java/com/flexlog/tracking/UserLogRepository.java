package com.flexlog.tracking;

import com.flexlog.tracking.models.Log;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface UserLogRepository extends JpaRepository<Log, Integer> {
    List<Log> findByUserId(Integer userId);
}
