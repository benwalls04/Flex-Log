import { useMemo, useState } from 'react';
import { useApp } from '../context/AppContext';

function exerciseName(logEntry) {
  const ex = logEntry.exercise;
  if (!ex) return `Exercise ${logEntry.exercise?.id ?? '?'}`;
  const v = ex.variant ? `${ex.variant} ` : '';
  return `${v}${ex.name || ''}`.trim() || `Exercise ${ex.id}`;
}

function muscleGroup(logEntry) {
  const ex = logEntry.exercise;
  const mg = ex?.muscleGroup ?? ex?.muscle_group;
  return (mg || '').toString().toLowerCase();
}

function workoutName(logEntry) {
  const w = logEntry.workout;
  return w?.name || `Workout ${w?.id ?? '?'}`;
}

function workoutDate(logEntry) {
  const w = logEntry.workout;
  if (!w?.date) return '';
  const d = new Date(w.date);
  return d.toLocaleDateString(undefined, { dateStyle: 'medium' });
}

export default function LogsTab() {
  const { logs, logsLoaded } = useApp();
  const [filterMuscle, setFilterMuscle] = useState('');
  const [filterExerciseName, setFilterExerciseName] = useState('');

  const muscleGroupsFromLogs = useMemo(() => {
    const set = new Set();
    logs.forEach((logEntry) => {
      const mg = muscleGroup(logEntry);
      if (mg) set.add(mg);
    });
    return Array.from(set).sort();
  }, [logs]);

  const filteredLogs = useMemo(() => {
    return logs.filter((logEntry) => {
      if (filterMuscle && muscleGroup(logEntry) !== filterMuscle) return false;
      if (filterExerciseName.trim()) {
        const name = exerciseName(logEntry).toLowerCase();
        if (!name.includes(filterExerciseName.toLowerCase())) return false;
      }
      return true;
    });
  }, [logs, filterMuscle, filterExerciseName]);

  const groupedByWorkout = useMemo(() => {
    const map = new Map();
    filteredLogs.forEach((logEntry) => {
      const wid = logEntry.workout?.id ?? 'none';
      if (!map.has(wid)) {
        map.set(wid, {
          workoutId: logEntry.workout?.id,
          workoutName: workoutName(logEntry),
          workoutDate: workoutDate(logEntry),
          logs: [],
        });
      }
      map.get(wid).logs.push(logEntry);
    });
    return Array.from(map.values());
  }, [filteredLogs]);

  if (!logsLoaded) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        Loading logs...
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <h2 className="text-xl font-semibold">Logs</h2>

      <div className="rounded-xl border border-border bg-surface p-4 space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground">Filters</h3>
        <div className="flex flex-wrap gap-3 items-center">
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Muscle group</label>
            <select
              value={filterMuscle}
              onChange={(e) => setFilterMuscle(e.target.value)}
              className="rounded-lg border border-border bg-surface px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">All</option>
              {muscleGroupsFromLogs.map((mg) => (
                <option key={mg} value={mg}>
                  {mg}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-muted-foreground mb-1">Exercise name</label>
            <input
              type="text"
              placeholder="Search exercise..."
              value={filterExerciseName}
              onChange={(e) => setFilterExerciseName(e.target.value)}
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {groupedByWorkout.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">No logs to show.</p>
        ) : (
          groupedByWorkout.map((group) => (
            <section key={group.workoutId ?? 'unknown'} className="rounded-xl border border-border bg-surface overflow-hidden">
              <div className="px-4 py-2 bg-muted border-b border-border">
                <div className="font-medium">{group.workoutName}</div>
                {group.workoutDate && (
                  <div className="text-sm text-muted-foreground">{group.workoutDate}</div>
                )}
              </div>
              <ul className="divide-y divide-border">
                {group.logs.map((logEntry) => (
                  <li
                    key={logEntry.id}
                    className="px-4 py-3 flex justify-between items-center"
                    data-log-id={logEntry.id}
                    data-exercise-id={logEntry.exercise?.id}
                    data-workout-id={logEntry.workout?.id}
                  >
                    <span className="font-medium">{exerciseName(logEntry)}</span>
                    <span className="text-muted-foreground">
                      {logEntry.weight != null && `${logEntry.weight} lbs`}
                      {logEntry.weight != null && logEntry.reps != null && ' × '}
                      {logEntry.reps != null && `${logEntry.reps} reps`}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ))
        )}
      </div>
    </div>
  );
}
