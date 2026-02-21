/**
 * FlexLog Session & Recommendation Test
 * Tests complete workout flow with Redis session tracking
 */

import {
    config,
    validateConfig,
    signInUser,
    getAllExercises,
    buildExerciseLookup,
    resolveExercises,
    createWorkout,
    logExerciseSets,
    getRecommendation,
    checkRedisSession,
    verifyRedisSession,
    displayRecommendation,
    log,
    section,
    colors
} from './test-utils.js';

// Exercise names to test (variant + name format)
const TEST_EXERCISE_NAMES = [
    'barbell bench press',    // chest exercise
    'machine overhead press', // shoulders exercise
    'pec-dec fly'             // chest exercise
];

// ==========================================
// MAIN TEST FLOW
// ==========================================
async function runSessionTest() {
    console.log('\n' + colors.magenta + '━'.repeat(70) + colors.reset);
    console.log(colors.magenta + '  🏋️  FlexLog Session & Recommendation Test' + colors.reset);
    console.log(colors.magenta + '━'.repeat(70) + colors.reset + '\n');

    // Validate configuration
    validateConfig();

    if (TEST_EXERCISE_NAMES.length === 0) {
        log('No test exercise names configured!', 'error');
        log('Update TEST_EXERCISE_NAMES in test-session.js', 'info');
        process.exit(1);
    }

    try {
        // ==========================================
        // STEP 1: AUTHENTICATION
        // ==========================================
        section('STEP 1: Authentication');
        const { user, token } = await signInUser();

        // ==========================================
        // STEP 2: FETCH & BUILD EXERCISE LOOKUP
        // ==========================================
        section('STEP 2: Fetch Exercises from Database');
        log('Fetching all exercises...', 'info');
        const allExercises = await getAllExercises(token);
        log(`Fetched ${allExercises.length} exercises from database`, 'success');
        
        const exerciseLookup = buildExerciseLookup(allExercises);
        log(`Built exercise lookup with ${exerciseLookup.size} entries`, 'success');
        
        // Resolve test exercise IDs from names
        const TEST_EXERCISES = resolveExercises(exerciseLookup, TEST_EXERCISE_NAMES);

        // ==========================================
        // STEP 3: CREATE WORKOUT
        // ==========================================
        section('STEP 3: Create Workout Session');
        const workoutName = 'chest shoulders triceps';
        log(`Creating workout: "${workoutName}"`, 'workout');
        const workout = await createWorkout(token, user.id, workoutName);
        log(`Workout created with ID: ${workout.id}`, 'success');
        console.log(JSON.stringify(workout, null, 2));

        const workoutId = workout.id;

        // ==========================================
        // STEP 4: LOG EXERCISES & GET RECOMMENDATIONS
        // ==========================================
        section('STEP 4: Log Exercises & Track Recommendations');

        const recommendations = [];

        // Log 3 different exercises, 3 sets each
        for (let exerciseIdx = 0; exerciseIdx < TEST_EXERCISES.length; exerciseIdx++) {
            const exercise = TEST_EXERCISES[exerciseIdx];
            
            log(`\n🏋️  Exercise ${exerciseIdx + 1}: ${exercise.name} (${exercise.muscle})`, 'workout');
            
            // Log 3 sets for this exercise
            const isFirst = (exerciseIdx === 0);
            const workoutPosition = exerciseIdx * 3;
            await logExerciseSets(token, user.id, workoutId, exercise, 3, isFirst, workoutPosition);
            
            log(`  ✓ Completed 3 sets of ${exercise.name}`, 'success');
            
            // Get recommendation after completing this exercise
            log(`  Getting recommendation after exercise ${exerciseIdx + 1}...`, 'recommendation');
            
            try {
                const recommendation = await getRecommendation(
                    token,
                    workoutId,
                    workoutName,
                    exercise.id
                );
                
                recommendations.push({
                    afterExercise: exercise.name,
                    recommendation: recommendation
                });
                
                displayRecommendation(recommendation, exercise.name);
            } catch (error) {
                log(`  ⚠️  Recommendation failed: ${error.message}`, 'error');
                log(`  This is expected if you haven't trained models yet`, 'info');
            }
        }

        // ==========================================
        // STEP 5: DISPLAY RESULTS
        // ==========================================
        section('STEP 5: Test Results Summary');
        
        log('Workout Summary:', 'success');
        console.log(`  Workout ID: ${workoutId}`);
        console.log(`  Workout Name: ${workoutName}`);
        console.log(`  Exercises Logged: ${TEST_EXERCISES.length}`);
        console.log(`  Total Sets: ${TEST_EXERCISES.length * 3}`);
        
        console.log('\n' + colors.cyan + 'Recommendations Received:' + colors.reset);
        recommendations.forEach((rec, idx) => {
            console.log(`\n  After ${rec.afterExercise}:`);
            console.log(`    Top Muscle: ${rec.recommendation.top_muscle}`);
            console.log(`    Top Machine: ${rec.recommendation.top_machine}`);
            console.log(`    Top Type: ${rec.recommendation.top_type}`);
            if (rec.recommendation.recommendations) {
                console.log(`    Recommendations: ${rec.recommendation.recommendations.length} exercises`);
            }
        });

        // ==========================================
        // STEP 6: CHECK REDIS SESSION STATE
        // ==========================================
        section('STEP 6: Redis Session State Check');
        
        const redisData = await checkRedisSession(workoutId);
        
        if (redisData) {
            log('✅ Successfully retrieved Redis session state!', 'success');
            verifyRedisSession(redisData, TEST_EXERCISES.length);
        } else {
            log('⚠️  Could not check Redis session state', 'info');
            console.log('\n' + colors.yellow + 'Expected Redis Keys:' + colors.reset);
            console.log(`  session:${workoutId}:exercises     → Set of exercise IDs: {${TEST_EXERCISES.map(e => e.id).join(', ')}}`);
            console.log(`  session:${workoutId}:count         → Total count: ${TEST_EXERCISES.length}`);
            console.log(`  session:${workoutId}:muscle_counts → Hash with muscle group counts`);
        }

        // ==========================================
        // SUCCESS
        // ==========================================
        console.log('\n' + colors.green + '━'.repeat(70) + colors.reset);
        log('🎉 Session test completed successfully!', 'success');
        console.log(colors.green + '━'.repeat(70) + colors.reset + '\n');

    } catch (error) {
        console.log('\n' + colors.red + '━'.repeat(70) + colors.reset);
        log(`Test failed: ${error.message}`, 'error');
        console.log(colors.red + '━'.repeat(70) + colors.reset + '\n');
        console.error('Full error:', error);
        process.exit(1);
    }
}

// ==========================================
// RUN THE TEST
// ==========================================
runSessionTest();
