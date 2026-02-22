import { createContext, useContext, useState, useCallback } from 'react';
import * as api from '../api/client';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [exercises, setExercises] = useState([]);
  const [logs, setLogs] = useState([]);
  const [exercisesLoaded, setExercisesLoaded] = useState(false);
  const [logsLoaded, setLogsLoaded] = useState(false);
  /* Active workout persists across tab switches until user clicks Finish Workout */
  const [activeWorkout, setActiveWorkout] = useState(null);
  const [workoutPosition, setWorkoutPosition] = useState(0);
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

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
      const list = Array.isArray(data) ? data : [];
      list.sort((a, b) => {
        const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        return tb - ta;
      });
      setLogs(list);
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

  const clearActiveWorkout = useCallback(() => {
    setActiveWorkout(null);
    setWorkoutPosition(0);
    setSelectedExercise(null);
    setRecommendations([]);
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
    activeWorkout,
    setActiveWorkout,
    workoutPosition,
    setWorkoutPosition,
    selectedExercise,
    setSelectedExercise,
    recommendations,
    setRecommendations,
    clearActiveWorkout,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
