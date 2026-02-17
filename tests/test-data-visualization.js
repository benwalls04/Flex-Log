/**
 * FlexLog Data Visualization Test
 * Visualizes how raw parameters are transformed into one-hot encoded features
 * and how the model makes predictions.
 * 
 * Usage: node test-data-visualization.js
 * Or: npm run test:visualize
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
    log,
    section,
    colors
} from './test-utils.js';

// Exercise names to test (variant + name format)
const TEST_EXERCISE_NAMES = [
    'barbell bench press',   
    'lat pull down',             
    'standard dumbbell curl'          
];

// ==========================================
// API CALL TO DEBUG ENDPOINT
// ==========================================
async function getRecommendationDebug(token, workoutId, workoutName, exerciseId) {
    const params = new URLSearchParams({
        workout_id: workoutId,
        workout_name: workoutName,
        exercise_id: exerciseId
    });

    const response = await fetch(`${config.RECOMMENDATION_API_URL}/recommendation/debug?${params}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Get recommendation debug failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
}

// ==========================================
// VISUALIZATION FUNCTIONS
// ==========================================
function displayDataTransformation(debugData, exerciseNum) {
    console.log('\n' + colors.magenta + '═'.repeat(80) + colors.reset);
    console.log(colors.magenta + `  📊 EXERCISE ${exerciseNum} - DATA TRANSFORMATION PIPELINE` + colors.reset);
    console.log(colors.magenta + '═'.repeat(80) + colors.reset + '\n');

    // STEP 1: Input Parameters
    section('STEP 1: Input Parameters');
    console.log(colors.cyan + 'Raw API Call:' + colors.reset);
    const input = debugData.step_1_input;
    console.log(`  workout_id:   ${colors.yellow}${input.workout_id}${colors.reset}`);
    console.log(`  workout_name: ${colors.yellow}"${input.workout_name}"${colors.reset}`);
    console.log(`  exercise_id:  ${colors.yellow}${input.exercise_id}${colors.reset}`);
    console.log(`  user_id:      ${colors.yellow}${input.user_id.substring(0, 8)}...${colors.reset}`);

    // STEP 2: Exercise Details
    section('STEP 2: Exercise Details (Database)');
    const exercise = debugData.step_2_exercise_details;
    console.log(colors.green + `Exercise: ${exercise.variant || ''} ${exercise.name}`.trim() + colors.reset);
    console.log(`  ${colors.yellow}ID:${colors.reset}            ${exercise.id}`);
    console.log(`  ${colors.yellow}Muscle Group:${colors.reset}  ${exercise.muscle_group}`);
    console.log(`  ${colors.yellow}Machine Type:${colors.reset}  ${exercise.machine_type}`);
    console.log(`  ${colors.yellow}Exercise Type:${colors.reset} ${exercise.exercise_type}`);

    // STEP 3: One-Hot Encoded Features
    section('STEP 3: One-Hot Encoded Features');
    const encoded = debugData.step_3_encoded_features;
    const mapping = debugData.step_6_feature_mapping;
    
    // Group features by category
    console.log(colors.cyan + '🏋️  Workout Day Flags (from workout_name):' + colors.reset);
    const dayKeys = Object.keys(encoded).filter(k => k.endsWith('_day'));
    dayKeys.forEach(key => {
        const value = encoded[key];
        const icon = value === 1 ? '✓' : '✗';
        const color = value === 1 ? colors.green : colors.reset;
        console.log(`  ${color}${icon} ${key}: ${value}${colors.reset}`);
    });

    console.log(colors.cyan + '\n💪 Muscle Group (one-hot):' + colors.reset);
    const muscleGroups = ['chest', 'back', 'legs', 'shoulders', 'biceps', 'triceps'];
    muscleGroups.forEach(mg => {
        if (encoded.hasOwnProperty(mg)) {
            const value = encoded[mg];
            const icon = value === 1 ? '✓' : '✗';
            const color = value === 1 ? colors.green : colors.reset;
            console.log(`  ${color}${icon} ${mg}: ${value}${colors.reset}`);
        }
    });

    console.log(colors.cyan + '\n🔧 Machine Type (one-hot):' + colors.reset);
    const machines = ['barbell', 'dumbbell', 'machine', 'cable', 'smith', 'misc'];
    machines.forEach(m => {
        if (encoded.hasOwnProperty(m)) {
            const value = encoded[m];
            const icon = value === 1 ? '✓' : '✗';
            const color = value === 1 ? colors.green : colors.reset;
            console.log(`  ${color}${icon} ${m}: ${value}${colors.reset}`);
        }
    });

    console.log(colors.cyan + '\n🎯 Exercise Type (one-hot):' + colors.reset);
    const types = ['isolation', 'compound'];
    types.forEach(t => {
        if (encoded.hasOwnProperty(t)) {
            const value = encoded[t];
            const icon = value === 1 ? '✓' : '✗';
            const color = value === 1 ? colors.green : colors.reset;
            console.log(`  ${color}${icon} ${t}: ${value}${colors.reset}`);
        }
    });

    console.log(colors.cyan + '\n📊 Session Context (from Redis):' + colors.reset);
    const prevKeys = Object.keys(encoded).filter(k => k.startsWith('num_prev_'));
    prevKeys.forEach(key => {
        console.log(`  ${key}: ${colors.yellow}${encoded[key]}${colors.reset}`);
    });
    console.log(`  position: ${colors.yellow}${encoded.position}${colors.reset}`);

    // STEP 4: Feature Vector
    section('STEP 4: Feature Vector (Model Input)');
    const featureVector = debugData.step_4_feature_vector;
    const featureLabels = debugData.step_5_feature_labels;
    
    console.log(colors.cyan + `Length: ${featureVector.length} features` + colors.reset);
    console.log(colors.cyan + 'Vector: [' + colors.reset + featureVector.slice(0, 10).map(v => 
        v === 1 ? colors.green + '1' + colors.reset : 
        v === 0 ? colors.reset + '0' + colors.reset : 
        colors.yellow + v.toFixed(1) + colors.reset
    ).join(', ') + ', ...' + colors.cyan + ']' + colors.reset);
    
    console.log('\n' + colors.yellow + 'Feature Mapping (showing only "hot" features):' + colors.reset);
    featureLabels.forEach((label, i) => {
        const value = featureVector[i];
        if (value !== 0) {  // Only show non-zero features
            const color = value === 1 ? colors.green : colors.yellow;
            console.log(`  ${color}${label}: ${value}${colors.reset}`);
        }
    });

    // STEP 5: Model Predictions
    section('STEP 5: Model Predictions');
    const predictions = debugData.step_7_predictions;
    
    if (predictions.error) {
        log(`⚠️  ${predictions.error}`, 'error');
        log('Train models first using pipeline.py', 'info');
        return;
    }

    // Muscle Group Predictions
    console.log(colors.cyan + '🎯 Muscle Group Predictions:' + colors.reset);
    const muscleProbs = predictions.muscle.probabilities;
    const sortedMuscles = Object.entries(muscleProbs)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3);
    
    sortedMuscles.forEach(([muscle, prob], idx) => {
        const percentage = (prob * 100).toFixed(1);
        const bar = '█'.repeat(Math.floor(prob * 30));
        const isTop = muscle === predictions.muscle.top_prediction;
        const color = isTop ? colors.green : colors.reset;
        console.log(`  ${color}${idx + 1}. ${muscle}: ${percentage}% ${bar}${colors.reset}`);
    });

    // Machine Type Predictions
    console.log(colors.cyan + '\n🔧 Machine Type Predictions:' + colors.reset);
    const machineProbs = predictions.machine.probabilities;
    const sortedMachines = Object.entries(machineProbs)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3);
    
    sortedMachines.forEach(([machine, prob], idx) => {
        const percentage = (prob * 100).toFixed(1);
        const bar = '█'.repeat(Math.floor(prob * 30));
        const isTop = machine === predictions.machine.top_prediction;
        const color = isTop ? colors.green : colors.reset;
        console.log(`  ${color}${idx + 1}. ${machine}: ${percentage}% ${bar}${colors.reset}`);
    });

    // Exercise Type Predictions
    console.log(colors.cyan + '\n🏋️  Exercise Type Predictions:' + colors.reset);
    const typeProbs = predictions.type.probabilities;
    const sortedTypes = Object.entries(typeProbs)
        .sort((a, b) => b[1] - a[1]);
    
    sortedTypes.forEach(([type, prob], idx) => {
        const percentage = (prob * 100).toFixed(1);
        const bar = '█'.repeat(Math.floor(prob * 30));
        const isTop = type === predictions.type.top_prediction;
        const color = isTop ? colors.green : colors.reset;
        console.log(`  ${color}${idx + 1}. ${type}: ${percentage}% ${bar}${colors.reset}`);
    });

    // Summary
    console.log('\n' + colors.green + '✨ Top Recommendation:' + colors.reset);
    console.log(`  ${predictions.muscle.top_prediction} / ${predictions.machine.top_prediction} / ${predictions.type.top_prediction}`);
}

// ==========================================
// MAIN TEST FLOW
// ==========================================
async function runDataVisualizationTest() {
    console.log('\n' + colors.magenta + '━'.repeat(80) + colors.reset);
    console.log(colors.magenta + '  📊 FlexLog Data Visualization Test' + colors.reset);
    console.log(colors.magenta + '  Visualize: Raw Input → One-Hot Encoding → Model Predictions' + colors.reset);
    console.log(colors.magenta + '━'.repeat(80) + colors.reset + '\n');

    // Validate configuration
    validateConfig();

    if (TEST_EXERCISE_NAMES.length === 0) {
        log('No test exercise names configured!', 'error');
        process.exit(1);
    }

    try {
        // ==========================================
        // STEP 1: AUTHENTICATION
        // ==========================================
        section('AUTHENTICATION');
        const { user, token } = await signInUser();

        // ==========================================
        // STEP 2: FETCH EXERCISES
        // ==========================================
        section('FETCH EXERCISES');
        log('Fetching all exercises...', 'info');
        const allExercises = await getAllExercises(token);
        log(`Fetched ${allExercises.length} exercises from database`, 'success');
        
        const exerciseLookup = buildExerciseLookup(allExercises);
        const TEST_EXERCISES = resolveExercises(exerciseLookup, TEST_EXERCISE_NAMES);

        // ==========================================
        // STEP 3: CREATE WORKOUT
        // ==========================================
        section('CREATE WORKOUT');
        const workoutName = 'chest back arms';
        log(`Creating workout: "${workoutName}"`, 'workout');
        const workout = await createWorkout(token, workoutName);
        log(`Workout created with ID: ${workout.id}`, 'success');

        const workoutId = workout.id;

        // ==========================================
        // STEP 4: LOG EXERCISES & VISUALIZE DATA
        // ==========================================
        section('LOG EXERCISES & VISUALIZE TRANSFORMATIONS');

        for (let exerciseIdx = 0; exerciseIdx < TEST_EXERCISES.length; exerciseIdx++) {
            const exercise = TEST_EXERCISES[exerciseIdx];
            
            log(`\n💪 Exercise ${exerciseIdx + 1}: ${exercise.name}`, 'workout');
            
            // Log 3 sets for this exercise
            const isFirst = (exerciseIdx === 0);
            await logExerciseSets(token, workoutId, exercise, 3, isFirst, { delayMs: 50 });
            log(`✓ Completed 3 sets`, 'success');
            
            // Get debug data for this exercise
            log(`\n🔍 Fetching data transformation pipeline...`, 'info');
            
            try {
                const debugData = await getRecommendationDebug(
                    token,
                    workoutId,
                    workoutName,
                    exercise.id
                );
                
                // Display the transformation
                displayDataTransformation(debugData, exerciseIdx + 1);
                
            } catch (error) {
                log(`⚠️  Failed to get debug data: ${error.message}`, 'error');
                log('This is expected if you haven\'t trained models yet', 'info');
            }
        }

        // ==========================================
        // SUCCESS
        // ==========================================
        console.log('\n' + colors.green + '━'.repeat(80) + colors.reset);
        log('🎉 Data visualization test completed!', 'success');
        console.log(colors.green + '━'.repeat(80) + colors.reset + '\n');

    } catch (error) {
        console.log('\n' + colors.red + '━'.repeat(80) + colors.reset);
        log(`Test failed: ${error.message}`, 'error');
        console.log(colors.red + '━'.repeat(80) + colors.reset + '\n');
        console.error('Full error:', error);
        process.exit(1);
    }
}

// ==========================================
// RUN THE TEST
// ==========================================
runDataVisualizationTest();
