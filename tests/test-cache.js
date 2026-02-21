/**
 * FlexLog Recommendation Cache Test
 * Logs 3 different exercises (each triggers SQS → worker), waits ~10s after each log,
 * then calls get recommendation and prints the result + response time.
 *
 * Usage: node test-cache.js
 */

import {
    validateConfig,
    signInUser,
    getAllExercises,
    createWorkout,
    createLog,
    getRecommendation,
    sleep,
    log,
    section,
    colors,
    formatExerciseName
} from './test-utils.js';

const WAIT_AFTER_LOG_MS = 10_000; // 10 seconds
const WORKOUT_NAME = 'chest back triceps';

async function runCacheTest() {
    section('FlexLog Recommendation Cache Timing Test');

    validateConfig();

    let token;
    let userId;
    let workoutId;
    let exercises;

    try {
        log('Signing in...', 'info');
        const { user, token: t } = await signInUser();
        token = t;
        userId = user.id;
        log(`Signed in: ${userId}`, 'success');

        log('Fetching exercises...', 'info');
        exercises = await getAllExercises(token);
        if (!Array.isArray(exercises) || exercises.length < 3) {
            throw new Error('Need at least 3 exercises');
        }
        const [ex1, ex2, ex3] = exercises.slice(0, 3);
        const exerciseList = [
            { name: formatExerciseName(ex1), ...ex1 },
            { name: formatExerciseName(ex2), ...ex2 },
            { name: formatExerciseName(ex3), ...ex3 }
        ];
        log(`Using exercises: ${exerciseList.map(e => e.name).join(', ')}`, 'info');

        log('Creating workout...', 'info');
        const workout = await createWorkout(token, userId, WORKOUT_NAME);
        workoutId = workout.id;
        log(`Workout created: id=${workoutId}`, 'success');

        const timings = [];

        for (let i = 0; i < 3; i++) {
            const exercise = exerciseList[i];
            const workoutPosition = i;

            log(`\n--- Exercise ${i + 1}/3: ${exercise.name} (id=${exercise.id}) ---`, 'workout');
            await createLog(token, userId, workoutId, exercise.id, 135, 10, i === 0, workoutPosition);
            log(`Logged 1 set. Waiting ${WAIT_AFTER_LOG_MS / 1000}s for worker/cache...`, 'info');
            await sleep(WAIT_AFTER_LOG_MS);

            const startMs = Date.now();
            let recommendation;
            try {
                recommendation = await getRecommendation(token, workoutId, WORKOUT_NAME, exercise.id, workoutPosition);
            } finally {
                const elapsedMs = Date.now() - startMs;
                timings.push({ exercise: exercise.name, ms: elapsedMs });
                log(`Recommendation returned in ${elapsedMs} ms`, elapsedMs < 2000 ? 'success' : 'info');
            }

            console.log(colors.cyan + '\nRecommendation response:' + colors.reset);
            console.log(JSON.stringify(recommendation, null, 2));
            if (recommendation.recommendations && recommendation.recommendations.length > 0) {
                const top = recommendation.recommendations[0];
                log(`Top recommendation: ${formatExerciseName(top)}`, 'recommendation');
            }
        }

        console.log('\n' + colors.yellow + '--- Timing summary ---' + colors.reset);
        timings.forEach(({ exercise, ms }) => {
            console.log(`  ${exercise}: ${ms} ms`);
        });
        const avg = timings.reduce((s, t) => s + t.ms, 0) / timings.length;
        console.log(`  Average: ${Math.round(avg)} ms\n`);

    } catch (err) {
        log(err.message || String(err), 'error');
        if (err.stack) console.error(err.stack);
        process.exit(1);
    }
}

runCacheTest();
