import { useState, useMemo } from 'react';
import * as api from '../api/client';
import { useApp } from '../context/AppContext';

const MUSCLE_GROUPS = ['chest', 'back', 'legs', 'shoulders', 'biceps', 'triceps'];

function exerciseName(ex) {
  const v = ex.variant ? `${ex.variant} ` : '';
  return `${v}${ex.name || ''}`.trim() || `Exercise ${ex.id}`;
}

function muscleGroupMatch(ex, groups) {
  const mg = (ex.muscleGroup || ex.muscle_group || '').toString().toLowerCase();
  return groups.some((g) => mg === g.toLowerCase());
}

export default function WorkoutTab() {
  const { exercises, exercisesLoaded, appendLog } = useApp();
  const [selectedMuscles, setSelectedMuscles] = useState([]);
  const [workout, setWorkout] = useState(null);
  const [workoutPosition, setWorkoutPosition] = useState(0);
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [search, setSearch] = useState('');
  const [weight, setWeight] = useState('');
  const [reps, setReps] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const workoutMuscleGroups = useMemo(
    () => (workout?.name || '').toLowerCase().split(/\s+/).filter(Boolean),
    [workout?.name]
  );

  const filteredExercises = useMemo(() => {
    if (!exercises.length) return [];
    const byMuscle = workoutMuscleGroups.length
      ? exercises.filter((ex) => muscleGroupMatch(ex, workoutMuscleGroups))
      : exercises;
    if (!search.trim()) return byMuscle;
    const q = search.toLowerCase();
    return byMuscle.filter(
      (ex) =>
        (ex.name || '').toLowerCase().includes(q) ||
        (ex.variant || '').toLowerCase().includes(q)
    );
  }, [exercises, workoutMuscleGroups, search]);

  const exerciseListWithRecs = useMemo(() => {
    const recIds = new Set((recommendations || []).map((r) => r.id));
    const rest = filteredExercises.filter((ex) => !recIds.has(ex.id));
    return [...(recommendations || []), ...rest];
  }, [recommendations, filteredExercises]);

  const toggleMuscle = (m) => {
    setSelectedMuscles((prev) =>
      prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]
    );
  };

  const startWorkout = async () => {
    if (!selectedMuscles.length) {
      setError('Select at least one muscle group');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const name = selectedMuscles.join(' ').toLowerCase();
      const date = new Date().toISOString();
      const created = await api.createWorkout(name, date);
      setWorkout(created);
      setWorkoutPosition(0);
      setRecommendations([]);
      setSelectedExercise(null);
      setSearch('');
    } catch (e) {
      setError(e.message || 'Failed to start workout');
    } finally {
      setLoading(false);
    }
  };

  const selectExercise = async (ex) => {
    setSelectedExercise(ex);
    setWeight('');
    setReps('');
    if (!workout || !ex) return;
    try {
      const recs = await api.getRecommendation(
        workout.id,
        workout.name,
        ex.id,
        workoutPosition
      );
      setRecommendations(Array.isArray(recs?.recommendations) ? recs.recommendations : []);
    } catch {
      setRecommendations([]);
    }
  };

  const submitSet = async (e) => {
    e.preventDefault();
    if (!workout || !selectedExercise) return;
    const w = parseFloat(weight);
    const r = parseInt(reps, 10);
    if (Number.isNaN(w) || Number.isNaN(r)) {
      setError('Enter valid weight and reps');
      return;
    }
    setError('');
    setLoading(true);
    const isFirst = workoutPosition === 0;
    try {
      const created = await api.createLog(
        workout.id,
        selectedExercise.id,
        w,
        r,
        isFirst,
        workoutPosition
      );
      appendLog(created);
      setWorkoutPosition((p) => p + 1);
      setWeight('');
      setReps('');
    } catch (err) {
      setError(err.message || 'Failed to log set');
    } finally {
      setLoading(false);
    }
  };

  const finishWorkout = () => {
    setWorkout(null);
    setWorkoutPosition(0);
    setSelectedExercise(null);
    setRecommendations([]);
    setSearch('');
    setError('');
  };

  if (!exercisesLoaded) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        Loading exercises...
      </div>
    );
  }

  if (!workout) {
    return (
      <div className="max-w-md mx-auto space-y-4">
        <h2 className="text-xl font-semibold">Start Workout</h2>
        <p className="text-sm text-muted-foreground">Select muscle groups for this workout.</p>
        <div className="flex flex-wrap gap-2">
          {MUSCLE_GROUPS.map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => toggleMuscle(m)}
              className={`rounded-lg border px-4 py-2 text-sm font-medium capitalize ${
                selectedMuscles.includes(m)
                  ? 'border-primary bg-primary-muted text-primary'
                  : 'border-border bg-surface hover:bg-muted'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
        <button
          onClick={startWorkout}
          disabled={loading || !selectedMuscles.length}
          className="w-full rounded-lg bg-primary px-4 py-3 font-medium text-white hover:bg-primary-hover disabled:opacity-50"
        >
          {loading ? 'Starting...' : 'Start Workout'}
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">{workout.name}</h2>
        <button
          onClick={finishWorkout}
          className="rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          Finish Workout
        </button>
      </div>

      <div className="rounded-xl border border-border bg-surface p-4 space-y-4">
        <label className="block text-sm font-medium text-muted-foreground">
          Select exercise
        </label>
        <input
          type="text"
          placeholder="Search exercises..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <div className="max-h-48 overflow-y-auto rounded-lg border border-border divide-y divide-border">
          {exerciseListWithRecs.map((ex) => (
            <button
              key={ex.id}
              type="button"
              onClick={() => selectExercise(ex)}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-muted flex justify-between items-center ${
                selectedExercise?.id === ex.id ? 'bg-primary-muted' : ''
              }`}
            >
              <span>{exerciseName(ex)}</span>
              {recommendations.some((r) => r.id === ex.id) && (
                <span className="text-xs text-primary font-medium">Recommended</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {selectedExercise && (
        <div className="rounded-xl border border-border bg-surface p-4 space-y-4">
          <h3 className="font-medium">{exerciseName(selectedExercise)}</h3>
          <form onSubmit={submitSet} className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Weight (lbs)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                placeholder="0"
                className="w-24 rounded-lg border border-border bg-surface px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Reps</label>
              <input
                type="number"
                min="1"
                value={reps}
                onChange={(e) => setReps(e.target.value)}
                placeholder="0"
                className="w-20 rounded-lg border border-border bg-surface px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-primary px-4 py-2 font-medium text-white hover:bg-primary-hover disabled:opacity-50"
            >
              Log Set
            </button>
          </form>
          {error && <p className="text-sm text-danger">{error}</p>}
        </div>
      )}
    </div>
  );
}
