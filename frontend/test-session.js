import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

// Load test environment variables
dotenv.config({ path: '.env.test' });

// ==========================================
// CONFIGURATION
// ==========================================
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://kauffaiclsbufnwyiuau.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const TRACKING_API_URL = process.env.TRACKING_API_URL || 'http://localhost:8080/api';
const RECOMMENDATION_API_URL = process.env.RECOMMENDATION_API_URL || 'http://localhost:8000';

// Test user credentials
const EMAIL = process.env.TEST_EMAIL;
const PASSWORD = process.env.TEST_PASSWORD;

// Exercise names to test (variant + name format)
const TEST_EXERCISE_NAMES = [
    'barbell bench press',    
    'machine overhead press',            
    'pec-dec fly'          
];

// ==========================================
// LOGGING UTILITIES
// ==========================================
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    blue: '\x1b[34m',
    yellow: '\x1b[33m',
    cyan: '\x1b[36m',
    magenta: '\x1b[35m',
};

function log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    let color = colors.blue;
    let prefix = 'ℹ️';

    switch(type) {
        case 'success':
            color = colors.green;
            prefix = '✅';
            break;
        case 'error':
            color = colors.red;
            prefix = '❌';
            break;
        case 'info':
            color = colors.blue;
            prefix = '📝';
            break;
        case 'workout':
            color = colors.magenta;
            prefix = '💪';
            break;
        case 'recommendation':
            color = colors.cyan;
            prefix = '🎯';
            break;
    }

    console.log(`${color}[${timestamp}] ${prefix} ${message}${colors.reset}`);
}

function section(title) {
    console.log('\n' + colors.yellow + '='.repeat(60) + colors.reset);
    console.log(colors.yellow + `  ${title}` + colors.reset);
    console.log(colors.yellow + '='.repeat(60) + colors.reset + '\n');
}

// ==========================================
// SUPABASE AUTH
// ==========================================
async function signInUser(supabase) {
    log(`Signing in with email: ${EMAIL}`, 'info');

    const { data, error } = await supabase.auth.signInWithPassword({
        email: EMAIL,
        password: PASSWORD,
    });

    if (error) {
        throw new Error(`Supabase sign-in failed: ${error.message}`);
    }

    if (!data.user || !data.session?.access_token) {
        throw new Error('No session/token returned from sign-in');
    }

    log(`Signed in! User ID: ${data.user.id}`, 'success');
    return {
        user: data.user,
        token: data.session.access_token
    };
}

// ==========================================
// TRACKING SERVICE API (Spring Boot)
// ==========================================
async function getAllExercises(token) {
    const response = await fetch(`${TRACKING_API_URL}/exercises/`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Get exercises failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
}

function buildExerciseLookup(exercises) {
    const lookup = new Map();
    
    for (const exercise of exercises) {
        const variant = exercise.variant || '';
        const name = exercise.name || '';
        const key = `${variant} ${name}`.toLowerCase().trim();
        
        lookup.set(key, {
            id: exercise.id,
            name: exercise.name,
            variant: exercise.variant,
            muscle: exercise.muscleGroup?.toLowerCase() || 'unknown'
        });
    }
    
    return lookup;
}

async function createWorkout(token, workoutName) {
    const workoutData = {
        name: workoutName,
        date: new Date().toISOString(),
    };

    const response = await fetch(`${TRACKING_API_URL}/workouts/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(workoutData)
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Create workout failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
}

async function createLog(token, workoutId, exerciseId, weight, reps, isFirst) {
    const logData = {
        workout: { id: workoutId },
        exercise: { id: exerciseId },
        weight: weight,
        reps: reps,
        first: isFirst ? 1 : 0,
        timestamp: new Date().toISOString()
    };

    const response = await fetch(`${TRACKING_API_URL}/logs/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(logData)
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Create log failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
}

// ==========================================
// RECOMMENDATION SERVICE API (FastAPI)
// ==========================================
async function getRecommendation(token, workoutId, workoutName, lastExerciseId) {
    const params = new URLSearchParams({
        workout_id: workoutId,
        workout_name: workoutName,
        exercise_id: lastExerciseId
    });

    const response = await fetch(`${RECOMMENDATION_API_URL}/recommendation?${params}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Get recommendation failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
}

// ==========================================
// TEST HELPERS
// ==========================================
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ==========================================
// MAIN TEST FLOW
// ==========================================
async function runSessionTest() {
    console.log('\n' + colors.magenta + '━'.repeat(70) + colors.reset);
    console.log(colors.magenta + '  🏋️  FlexLog Session & Recommendation Test' + colors.reset);
    console.log(colors.magenta + '━'.repeat(70) + colors.reset + '\n');

    // Validate configuration
    if (!SUPABASE_ANON_KEY) {
        log('Missing SUPABASE_ANON_KEY in .env.test!', 'error');
        log('Copy .env.test.example to .env.test and fill in your values', 'info');
        process.exit(1);
    }
    if (!EMAIL || !PASSWORD) {
        log('Missing TEST_EMAIL or TEST_PASSWORD in .env.test!', 'error');
        log('Copy .env.test.example to .env.test and fill in your values', 'info');
        process.exit(1);
    }
    if (TEST_EXERCISE_NAMES.length === 0) {
        log('No test exercise names configured!', 'error');
        log('Update TEST_EXERCISE_NAMES in test-session.js', 'info');
        process.exit(1);
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

    try {
        // ==========================================
        // STEP 1: AUTHENTICATION
        // ==========================================
        section('STEP 1: Authentication');
        const { user, token } = await signInUser(supabase);

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
        const TEST_EXERCISES = [];
        for (const exerciseName of TEST_EXERCISE_NAMES) {
            const exercise = exerciseLookup.get(exerciseName.toLowerCase());
            if (!exercise) {
                log(`⚠️  Exercise not found: "${exerciseName}"`, 'error');
                log('Available exercises:', 'info');
                const sample = Array.from(exerciseLookup.keys()).slice(0, 10);
                sample.forEach(key => console.log(`  - ${key}`));
                throw new Error(`Exercise "${exerciseName}" not found in database`);
            }
            TEST_EXERCISES.push(exercise);
            log(`  ✓ Found: "${exerciseName}" → ID ${exercise.id} (${exercise.muscle})`, 'success');
        }

        // ==========================================
        // STEP 3: CREATE WORKOUT
        // ==========================================
        section('STEP 3: Create Workout Session');
        const workoutName = 'chest shoulders triceps';
        log(`Creating workout: "${workoutName}"`, 'workout');
        const workout = await createWorkout(token, workoutName);
        log(`Workout created with ID: ${workout.id}`, 'success');
        console.log(JSON.stringify(workout, null, 2));

        const workoutId = workout.id;

        // ==========================================
        // STEP 4: LOG EXERCISES & GET RECOMMENDATIONS
        // ==========================================
        section('STEP 4: Log Exercises & Track Recommendations');

        const recommendations = [];

        // Log 3 different exercises, 3 sets each
        for (let exerciseIdx = 0; exerciseIdx < 3; exerciseIdx++) {
            const exercise = TEST_EXERCISES[exerciseIdx];
            
            log(`\n🏋️  Exercise ${exerciseIdx + 1}: ${exercise.name} (${exercise.muscle})`, 'workout');
            
            // Log 3 sets for this exercise
            for (let set = 1; set <= 3; set++) {
                const isFirst = (exerciseIdx === 0); 
                const weight = 135;
                const reps = 12;
                
                log(`  Set ${set}: ${weight}lbs x ${reps} reps (first=${isFirst ? 1 : 0})`, 'info');
                
                const logEntry = await createLog(
                    token,
                    workoutId,
                    exercise.id,
                    weight,
                    reps,
                    isFirst
                );
                
                // Small delay to ensure timestamp ordering
                await sleep(100);
            }
            
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
                
                log(`  Recommended: ${recommendation.top_muscle} / ${recommendation.top_machine} / ${recommendation.top_type}`, 'recommendation');
                
                if (recommendation.recommendations && recommendation.recommendations.length > 0) {
                    log(`  Top recommendation: ${recommendation.recommendations[0].name || 'Exercise ' + recommendation.recommendations[0].id}`, 'recommendation');
                }
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
        
        log('⚠️  MANUAL CHECK NEEDED:', 'info');
        log('You need to add an endpoint to check Redis session state.', 'info');
        console.log('\n' + colors.yellow + 'Expected Redis Keys:' + colors.reset);
        console.log(`  session:${workoutId}:exercises     → Set of exercise IDs: {${TEST_EXERCISES.map(e => e.id).join(', ')}}`);
        console.log(`  session:${workoutId}:count         → Total count: ${TEST_EXERCISES.length}`);
        console.log(`  session:${workoutId}:muscle_counts → Hash: {chest: 1, back: 1, biceps: 1}`);
        
        console.log('\n' + colors.yellow + 'To verify manually, run:' + colors.reset);
        console.log(`  redis-cli -h redis-17726.c262.us-east-1-3.ec2.cloud.redislabs.com -p 17726 -a YOUR_PASSWORD`);
        console.log(`  SMEMBERS session:${workoutId}:exercises`);
        console.log(`  GET session:${workoutId}:count`);
        console.log(`  HGETALL session:${workoutId}:muscle_counts`);

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
