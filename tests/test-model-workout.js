/**
 * FlexLog Model-Driven Workout Test
 * Builds a complete workout based on recommendation engine suggestions
 * 
 * Usage: node test-model-workout.js <workout_name> <num_exercises> <sets_per_exercise>
 * Example: node test-model-workout.js "chest back arms" 5 3
 */

import {
    validateConfig,
    signInUser,
    getAllExercises,
    buildExerciseLookup,
    createWorkout,
    logExerciseSets,
    getRecommendation,
    formatExerciseName,
    log,
    section,
    colors,
    sleep
} from './test-utils.js';

// ==========================================
// PARSE COMMAND LINE ARGUMENTS
// ==========================================
const WORKOUT_NAME = process.argv[2] || 'back triceps';
const NUM_EXERCISES = parseInt(process.argv[3]) || 5;
const SETS_PER_EXERCISE = parseInt(process.argv[4]) || 3;

// Dummy values for weight and reps
const DUMMY_WEIGHT = 135;
const DUMMY_REPS = 12;

// ==========================================
// MAIN TEST FLOW
// ==========================================
async function runModelWorkoutTest() {
    console.log('\n' + colors.magenta + '━'.repeat(70) + colors.reset);
    console.log(colors.magenta + '  🤖 FlexLog Model-Driven Workout Builder' + colors.reset);
    console.log(colors.magenta + '━'.repeat(70) + colors.reset + '\n');

    log(`Workout Name: "${WORKOUT_NAME}"`, 'info');
    log(`Number of Exercises: ${NUM_EXERCISES}`, 'info');
    log(`Sets per Exercise: ${SETS_PER_EXERCISE}`, 'info');
    log(`Weight/Reps: ${DUMMY_WEIGHT}lbs x ${DUMMY_REPS} reps (dummy values)`, 'info');

    // Validate configuration
    validateConfig();

    try {
        // ==========================================
        // STEP 1: AUTHENTICATION
        // ==========================================
        section('STEP 1: Authentication');
        const { user, token } = await signInUser();

        // ==========================================
        // STEP 2: FETCH EXERCISES
        // ==========================================
        section('STEP 2: Fetch Exercise Database');
        log('Fetching all exercises...', 'info');
        const allExercises = await getAllExercises(token);
        log(`Fetched ${allExercises.length} exercises from database`, 'success');
        
        // Build lookup map by ID for quick access
        const exerciseById = new Map();
        allExercises.forEach(ex => {
            exerciseById.set(ex.id, ex);
        });

        // ==========================================
        // STEP 3: CREATE WORKOUT SESSION
        // ==========================================
        section('STEP 3: Create Workout Session');
        log(`Creating workout: "${WORKOUT_NAME}"`, 'workout');
        const workout = await createWorkout(token, WORKOUT_NAME);
        log(`Workout created with ID: ${workout.id}`, 'success');

        const workoutId = workout.id;

        // ==========================================
        // STEP 4: BUILD WORKOUT FROM RECOMMENDATIONS
        // ==========================================
        section('STEP 4: Build Workout from Model Recommendations');

        const completedExercises = [];
        let lastExerciseId = null;

        for (let exerciseNum = 1; exerciseNum <= NUM_EXERCISES; exerciseNum++) {
            log(`\n🎯 Getting recommendation for exercise ${exerciseNum}/${NUM_EXERCISES}...`, 'recommendation');
            
            try {
                // Get recommendation from model
                // For first exercise, we need to pass any valid exercise ID
                const exerciseIdForRecommendation = lastExerciseId || 1;
                
                const recommendation = await getRecommendation(
                    token,
                    workoutId,
                    WORKOUT_NAME,
                    exerciseIdForRecommendation
                );

                // Extract the top recommended exercise
                if (!recommendation.recommendations || recommendation.recommendations.length === 0) {
                    log('⚠️  No exercise recommendations returned, cannot continue', 'error');
                    throw new Error('Model did not return any exercise recommendations');
                }

                const recommendedExercise = recommendation.recommendations[0];
                const exerciseId = recommendedExercise.id;
                const exerciseName = formatExerciseName(recommendedExercise);
                
                log(`✅ Model recommended: ${exerciseName} (ID: ${exerciseId})`, 'recommendation');
                log(`   Top Muscle: ${recommendation.top_muscle}`, 'info');
                log(`   Top Machine: ${recommendation.top_machine}`, 'info');
                log(`   Top Type: ${recommendation.top_type}`, 'info');

                // Log sets for this exercise
                log(`\n💪 Logging ${SETS_PER_EXERCISE} sets...`, 'workout');
                
                const exercise = {
                    id: exerciseId,
                    name: recommendedExercise.name,
                    variant: recommendedExercise.variant,
                    muscle: recommendedExercise.muscleGroup?.toLowerCase() || 'unknown'
                };

                const isFirst = (exerciseNum === 1);
                await logExerciseSets(
                    token,
                    workoutId,
                    exercise,
                    SETS_PER_EXERCISE,
                    isFirst,
                    { weight: DUMMY_WEIGHT, reps: DUMMY_REPS, delayMs: 50 }
                );

                log(`✓ Completed ${SETS_PER_EXERCISE} sets`, 'success');

                // Store for summary
                completedExercises.push({
                    order: exerciseNum,
                    id: exerciseId,
                    name: exerciseName,
                    muscle: exercise.muscle,
                    sets: SETS_PER_EXERCISE,
                    topMuscle: recommendation.top_muscle,
                    topMachine: recommendation.top_machine,
                    topType: recommendation.top_type
                });

                // Update last exercise ID for next recommendation
                lastExerciseId = exerciseId;

                // Small delay before next recommendation
                await sleep(200);

            } catch (error) {
                log(`❌ Failed to get recommendation: ${error.message}`, 'error');
                log('This likely means your user models haven\'t been trained yet', 'info');
                throw error;
            }
        }

        // ==========================================
        // STEP 5: DISPLAY WORKOUT SUMMARY
        // ==========================================
        section('STEP 5: Workout Summary');

        console.log('\n' + colors.cyan + '📋 Model-Built Workout Plan:' + colors.reset);
        console.log(colors.cyan + `   Workout: ${WORKOUT_NAME}` + colors.reset);
        console.log(colors.cyan + `   Workout ID: ${workoutId}` + colors.reset);
        console.log(colors.cyan + `   Total Exercises: ${completedExercises.length}` + colors.reset);
        console.log(colors.cyan + `   Total Sets: ${completedExercises.length * SETS_PER_EXERCISE}` + colors.reset);
        console.log();

        completedExercises.forEach((ex, idx) => {
            console.log(colors.green + `${idx + 1}. ${ex.name}` + colors.reset);
            console.log(`   ${colors.yellow}Muscle Group:${colors.reset} ${ex.muscle}`);
            console.log(`   ${colors.yellow}Sets:${colors.reset} ${ex.sets} x ${DUMMY_WEIGHT}lbs x ${DUMMY_REPS} reps`);
            console.log(`   ${colors.yellow}Recommendation Context:${colors.reset} ${ex.topMuscle} / ${ex.topMachine} / ${ex.topType}`);
            console.log();
        });

        // Display muscle distribution
        const muscleDistribution = {};
        completedExercises.forEach(ex => {
            muscleDistribution[ex.muscle] = (muscleDistribution[ex.muscle] || 0) + 1;
        });

        console.log(colors.cyan + '💪 Muscle Group Distribution:' + colors.reset);
        Object.entries(muscleDistribution)
            .sort((a, b) => b[1] - a[1])
            .forEach(([muscle, count]) => {
                const percentage = ((count / completedExercises.length) * 100).toFixed(1);
                console.log(`   ${muscle}: ${count} exercise${count > 1 ? 's' : ''} (${percentage}%)`);
            });

        // ==========================================
        // SUCCESS
        // ==========================================
        console.log('\n' + colors.green + '━'.repeat(70) + colors.reset);
        log('🎉 Model-driven workout completed successfully!', 'success');
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
runModelWorkoutTest();
