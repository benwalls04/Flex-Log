import { createContext, useContext, useState, useCallback } from 'react';
import * as api from '../api/client';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [exercises, setExercises] = useState([]);
  const [logs, setLogs] = useState([]);
  const [exercisesLoaded, setExercisesLoaded] = useState(false);
  const [logsLoaded, setLogsLoaded] = useState(false);

  const loadExercises = useCallback(async () => {
    try {
      const data = await api.getExercises();
      setExercises(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Failed to load exercises', e);
      setExercises([]);
    } finally {
      setExercisesLoaded(true);
    }
  }, []);

  const loadLogs = useCallback(async () => {
    try {
      const data = await api.getAllLogs();
      setLogs(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Failed to load logs', e);
      setLogs([]);
    } finally {
      setLogsLoaded(true);
    }
  }, []);

  const appendLog = useCallback((logEntry) => {
    setLogs((prev) => [logEntry, ...prev]);
  }, []);

  const value = {
    exercises,
    setExercises,
    exercisesLoaded,
    loadExercises,
    logs,
    setLogs,
    logsLoaded,
    loadLogs,
    appendLog,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
