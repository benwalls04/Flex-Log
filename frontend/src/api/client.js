/**
 * API client for FlexLog backend.
 * All request/response shapes match the test fixtures (tests/test-utils.js, test-fixture.js).
 * Token is read by the API gateway authorizer; no X-User-Id header.
 */

const BASE = import.meta.env.VITE_API_BASE_URL || '';

function getToken() {
  return localStorage.getItem('flexlog_token');
}

function getAuthHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function handleResponse(response) {
  if (response.status === 401) {
    localStorage.removeItem('flexlog_token');
    window.location.href = '/';
    throw new Error('Unauthorized');
  }
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

export async function getExercises() {
  const res = await fetch(`${BASE}/exercises`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function createWorkout(name, date) {
  const res = await fetch(`${BASE}/workouts`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ name, date }),
  });
  return handleResponse(res);
}

export async function getAllWorkouts() {
  const res = await fetch(`${BASE}/workouts`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function getWorkout(id) {
  const res = await fetch(`${BASE}/workouts/${id}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function createLog(workoutId, exerciseId, weight, reps, first, workoutPosition) {
  const url = new URL(`${BASE}/logs`);
  url.searchParams.set('workoutPosition', String(workoutPosition));
  const res = await fetch(url.toString(), {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      workout: { id: workoutId },
      exercise: { id: exerciseId },
      weight: Number(weight),
      reps: Number(reps),
      first: first ? 1 : 0,
      timestamp: new Date().toISOString(),
    }),
  });
  return handleResponse(res);
}

export async function getAllLogs() {
  const res = await fetch(`${BASE}/logs`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function getRecommendation(workoutId, workoutName, exerciseId, workoutPosition) {
  const res = await fetch(`${BASE}/recommendation`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      workout_id: String(workoutId),
      workout_name: workoutName,
      exercise_id: String(exerciseId),
      workout_position: String(workoutPosition),
    }),
  });
  return handleResponse(res);
}

export { getToken };
