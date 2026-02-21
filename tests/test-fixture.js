/**
 * FlexLog Full Endpoint Test Fixture
 * Runs all tracking API endpoints in order (auth required for all except sign-in).
 * Base URL: TRACKING_API_URL from .env.test
 *
 * Usage: node test-fixture.js
 */

import {
    validateConfig,
    signInUser,
    getAllExercises,
    createWorkout,
    getAllWorkouts,
    getWorkout,
    createLog,
    getAllLogs,
    getLog,
    updateLog,
    deleteLog,
    log,
    section,
    colors
} from './test-utils.js';

async function runFixture() {
    section('FlexLog Full Endpoint Test Fixture');

    validateConfig();

    let token;
    let userId;
    let workoutId;
    let logId;
    let exercises;

    try {
        // --- 1. Sign in (auth) ---
        log('1. Sign in', 'info');
        const { user, token: t } = await signInUser();
        token = t;
        userId = user.id;
        log(`Signed in: ${userId}`, 'success');

        // --- 2. GET all exercises ---
        log('2. GET /exercises/', 'info');
        exercises = await getAllExercises(token);
        log(`Got ${Array.isArray(exercises) ? exercises.length : 0} exercises`, 'success');
        if (!Array.isArray(exercises) || exercises.length === 0) {
            throw new Error('Need at least one exercise for create log test');
        }
        const firstExercise = exercises[0];
        const exerciseId = firstExercise.id;

        // --- 3. POST create workout ---
        log('3. POST /workouts/ (create workout)', 'info');
        const workout = await createWorkout(token, userId, 'Fixture workout');
        workoutId = workout.id;
        log(`Created workout id=${workoutId}`, 'success');

        // --- 4. GET all workouts ---
        log('4. GET /workouts/', 'info');
        const allWorkouts = await getAllWorkouts(token, userId);
        log(`Got ${Array.isArray(allWorkouts) ? allWorkouts.length : 0} workouts`, 'success');

        // --- 5. GET workout by id ---
        log('5. GET /workouts/{id}', 'info');
        const singleWorkout = await getWorkout(token, userId, workoutId);
        log(`Got workout: ${singleWorkout?.name ?? workoutId}`, 'success');

        // --- 6. POST create log ---
        log('6. POST /logs/ (create log)', 'info');
        const logEntry = await createLog(
            token,
            userId,
            workoutId,
            exerciseId,
            135,
            10,
            true,
            0
        );
        logId = logEntry.id;
        log(`Created log id=${logId}`, 'success');

        // --- 7. GET all logs ---
        log('7. GET /logs/', 'info');
        const allLogs = await getAllLogs(token, userId);
        log(`Got ${Array.isArray(allLogs) ? allLogs.length : 0} logs`, 'success');

        // --- 8. GET log by id ---
        log('8. GET /logs/{id}', 'info');
        const singleLog = await getLog(token, userId, logId);
        log(`Got log: reps=${singleLog?.reps ?? '?'}`, 'success');

        // --- 9. PUT update log ---
        log('9. PUT /logs/{id} (update log)', 'info');
        const updated = await updateLog(token, userId, logId, { reps: 12, weight: 140 });
        log(`Updated log: reps=${updated?.reps ?? '?'}, weight=${updated?.weight ?? '?'}`, 'success');

        // --- 10. DELETE log ---
        log('10. DELETE /logs/{id}', 'info');
        await deleteLog(token, userId, logId);
        log('Deleted log (204)', 'success');

        console.log('\n' + colors.green + '='.repeat(60) + colors.reset);
        log('All endpoint tests passed.', 'success');
        console.log(colors.green + '='.repeat(60) + colors.reset + '\n');
    } catch (err) {
        log(err.message || String(err), 'error');
        if (err.stack) console.error(err.stack);
        process.exit(1);
    }
}

runFixture();
