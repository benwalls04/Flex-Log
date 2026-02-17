/**
 * FlexLog Test Utilities
 * Shared functions for testing authentication, workouts, and recommendations
 */

import { createClient } from '@supabase/supabase-js';
import { createClient as createRedisClient } from 'redis';
import dotenv from 'dotenv';

// Load test environment variables
dotenv.config({ path: '.env.test' });

// ==========================================
// CONFIGURATION
// ==========================================
export const config = {
    SUPABASE_URL: process.env.SUPABASE_URL || 'https://kauffaiclsbufnwyiuau.supabase.co',
    SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY,
    TRACKING_API_URL: process.env.TRACKING_API_URL || 'http://localhost:8080/api',
    RECOMMENDATION_API_URL: process.env.RECOMMENDATION_API_URL || 'http://localhost:8000',
    EMAIL: process.env.TEST_EMAIL,
    PASSWORD: process.env.TEST_PASSWORD,
    REDIS_HOST: process.env.REDIS_HOST,
    REDIS_PORT: parseInt(process.env.REDIS_PORT),
    REDIS_PASSWORD: process.env.REDIS_PASSWORD,
};

// ==========================================
// LOGGING UTILITIES
// ==========================================
export const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    blue: '\x1b[34m',
    yellow: '\x1b[33m',
    cyan: '\x1b[36m',
    magenta: '\x1b[35m',
};

export function log(message, type = 'info') {
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
        case 'data':
            color = colors.cyan;
            prefix = '📊';
            break;
    }

    console.log(`${color}[${timestamp}] ${prefix} ${message}${colors.reset}`);
}

export function section(title) {
    console.log('\n' + colors.yellow + '='.repeat(60) + colors.reset);
    console.log(colors.yellow + `  ${title}` + colors.reset);
    console.log(colors.yellow + '='.repeat(60) + colors.reset + '\n');
}

// ==========================================
// VALIDATION
// ==========================================
export function validateConfig() {
    const errors = [];
    
    if (!config.SUPABASE_ANON_KEY) {
        errors.push('Missing SUPABASE_ANON_KEY in .env.test!');
    }
    if (!config.EMAIL || !config.PASSWORD) {
        errors.push('Missing TEST_EMAIL or TEST_PASSWORD in .env.test!');
    }
    
    if (errors.length > 0) {
        errors.forEach(err => log(err, 'error'));
        log('Copy .env.test.example to .env.test and fill in your values', 'info');
        process.exit(1);
    }
}

// ==========================================
// SUPABASE AUTH
// ==========================================
export async function signInUser() {
    const supabase = createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY);
    
    log(`Signing in with email: ${config.EMAIL}`, 'info');

    const { data, error } = await supabase.auth.signInWithPassword({
        email: config.EMAIL,
        password: config.PASSWORD,
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
        token: data.session.access_token,
        supabase
    };
}

// ==========================================
// TRACKING SERVICE API (Spring Boot)
// ==========================================

/**
 * Fetch all exercises from the tracking service
 */
export async function getAllExercises(token) {
    const response = await fetch(`${config.TRACKING_API_URL}/exercises/`, {
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

/**
 * Build a lookup map of exercises by "variant name" (lowercase)
 * @param {Array} exercises - Array of exercise objects from API
 * @returns {Map} Map with keys like "barbell bench press" → exercise object
 */
export function buildExerciseLookup(exercises) {
    const lookup = new Map();
    
    for (const exercise of exercises) {
        const variant = exercise.variant || '';
        const name = exercise.name || '';
        const key = `${variant} ${name}`.toLowerCase().trim();
        
        lookup.set(key, {
            id: exercise.id,
            name: exercise.name,
            variant: exercise.variant,
            muscle: exercise.muscleGroup?.toLowerCase() || 'unknown',
            fullExercise: exercise // Store full exercise object for reference
        });
    }
    
    return lookup;
}

/**
 * Create a new workout session
 * @param {string} token - JWT access token
 * @param {string} workoutName - Name of the workout (e.g., "chest back biceps")
 * @returns {Object} Created workout object with id
 */
export async function createWorkout(token, workoutName) {
    const workoutData = {
        name: workoutName,
        date: new Date().toISOString(),
    };

    const response = await fetch(`${config.TRACKING_API_URL}/workouts/`, {
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

/**
 * Log a single set for an exercise
 * @param {string} token - JWT access token
 * @param {number} workoutId - Workout ID
 * @param {number} exerciseId - Exercise ID
 * @param {number} weight - Weight in lbs
 * @param {number} reps - Number of reps
 * @param {boolean} isFirst - Whether this is the first exercise of the workout
 * @returns {Object} Created log object
 */
export async function createLog(token, workoutId, exerciseId, weight, reps, isFirst) {
    const logData = {
        workout: { id: workoutId },
        exercise: { id: exerciseId },
        weight: weight,
        reps: reps,
        first: isFirst ? 1 : 0,
        timestamp: new Date().toISOString()
    };

    const response = await fetch(`${config.TRACKING_API_URL}/logs/`, {
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

/**
 * Log multiple sets for a single exercise
 * @param {string} token - JWT access token
 * @param {number} workoutId - Workout ID
 * @param {Object} exercise - Exercise object with id, name, variant
 * @param {number} numSets - Number of sets to log
 * @param {boolean} isFirst - Whether this is the first exercise of the workout
 * @param {Object} options - Optional parameters (weight, reps, delayMs)
 * @returns {Array} Array of created log objects
 */
export async function logExerciseSets(token, workoutId, exercise, numSets = 3, isFirst = false, options = {}) {
    const {
        weight = 135,
        reps = 12,
        delayMs = 100
    } = options;
    
    const logs = [];
    
    for (let set = 1; set <= numSets; set++) {
        log(`  Set ${set}: ${weight}lbs x ${reps} reps (first=${isFirst ? 1 : 0})`, 'info');
        
        const logEntry = await createLog(
            token,
            workoutId,
            exercise.id,
            weight,
            reps,
            isFirst
        );
        
        logs.push(logEntry);
        
        // Small delay to ensure timestamp ordering
        if (set < numSets && delayMs > 0) {
            await sleep(delayMs);
        }
    }
    
    return logs;
}

// ==========================================
// RECOMMENDATION SERVICE API (FastAPI)
// ==========================================

/**
 * Get exercise recommendations
 * @param {string} token - JWT access token
 * @param {number} workoutId - Workout ID
 * @param {string} workoutName - Workout name (muscle groups)
 * @param {number} lastExerciseId - ID of the last exercise completed
 * @returns {Object} Recommendation response with top_muscle, top_machine, top_type, recommendations
 */
export async function getRecommendation(token, workoutId, workoutName, lastExerciseId) {
    const params = new URLSearchParams({
        workout_id: workoutId,
        workout_name: workoutName,
        exercise_id: lastExerciseId
    });

    const response = await fetch(`${config.RECOMMENDATION_API_URL}/recommendation?${params}`, {
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
// REDIS SESSION MANAGEMENT
// ==========================================

/**
 * Connect to Redis and retrieve session state for a workout (compact version)
 * @param {number} workoutId - Workout ID
 * @returns {Object|null} Object with exercises, count, muscleCounts or null on error
 */
export async function checkRedisSession(workoutId) {
    if (!config.REDIS_HOST || !config.REDIS_PORT || !config.REDIS_PASSWORD) {
        log('⚠️  Redis configuration not found in .env.test', 'info');
        return null;
    }

    log('Connecting to Redis to check session state...', 'info');

    const redisClient = createRedisClient({
        socket: {
            host: config.REDIS_HOST,
            port: config.REDIS_PORT,
        },
        password: config.REDIS_PASSWORD,
        username: 'default',
    });

    try {
        await redisClient.connect();
        log('Connected to Redis!', 'success');

        // Define Redis keys
        const exercisesKey = `session:${workoutId}:exercises`;
        const countKey = `session:${workoutId}:count`;
        const muscleCountsKey = `session:${workoutId}:muscle_counts`;

        // Get all data
        const exercises = await redisClient.sMembers(exercisesKey);
        const count = await redisClient.get(countKey);
        const muscleCounts = await redisClient.hGetAll(muscleCountsKey);

        // Display results
        console.log('\n' + colors.cyan + '📊 Redis Cache State:' + colors.reset);
        console.log(colors.cyan + `  Key: ${exercisesKey}` + colors.reset);
        console.log(`    Type: SET`);
        console.log(`    Value: [${exercises.join(', ')}]`);
        console.log(`    Exercise Count: ${exercises.length}`);

        console.log(colors.cyan + `\n  Key: ${countKey}` + colors.reset);
        console.log(`    Type: STRING`);
        console.log(`    Value: ${count || '(not set)'}`);

        console.log(colors.cyan + `\n  Key: ${muscleCountsKey}` + colors.reset);
        console.log(`    Type: HASH`);
        if (Object.keys(muscleCounts).length > 0) {
            for (const [muscle, muscleCount] of Object.entries(muscleCounts)) {
                console.log(`    ${muscle}: ${muscleCount}`);
            }
        } else {
            console.log(`    (empty hash)`);
        }

        await redisClient.disconnect();
        return {
            exercises,
            count: parseInt(count) || 0,
            muscleCounts
        };
    } catch (error) {
        log(`Redis check failed: ${error.message}`, 'error');
        if (redisClient.isOpen) {
            await redisClient.disconnect();
        }
        return null;
    }
}

/**
 * Connect to Redis and retrieve session state with detailed logging (for standalone script)
 * @param {number} workoutId - Workout ID
 * @returns {Promise<void>}
 */
export async function checkRedisSessionDetailed(workoutId) {
    section('Redis Session State Checker');

    // Validate configuration
    if (!config.REDIS_HOST || !config.REDIS_PORT || !config.REDIS_PASSWORD) {
        log('Missing Redis configuration in .env.test!', 'error');
        log('Required variables: REDIS_HOST, REDIS_PORT, REDIS_PASSWORD', 'info');
        process.exit(1);
    }

    if (!workoutId) {
        log('Usage: npm run check:redis <workout_id>', 'error');
        log('Example: npm run check:redis 26', 'info');
        process.exit(1);
    }

    log(`Checking session state for workout ID: ${workoutId}`, 'info');
    log(`Connecting to Redis at ${config.REDIS_HOST}:${config.REDIS_PORT}...`, 'info');

    // Create Redis client
    const redisClient = createRedisClient({
        socket: {
            host: config.REDIS_HOST,
            port: config.REDIS_PORT,
        },
        password: config.REDIS_PASSWORD,
        username: 'default',
    });

    // Handle errors
    redisClient.on('error', (err) => {
        log(`Redis Client Error: ${err.message}`, 'error');
    });

    try {
        // Connect to Redis
        await redisClient.connect();
        log('Connected to Redis successfully!', 'success');

        // Define Redis keys
        const exercisesKey = `session:${workoutId}:exercises`;
        const countKey = `session:${workoutId}:count`;
        const muscleCountsKey = `session:${workoutId}:muscle_counts`;

        section('Session Data');

        // 1. Get exercises set
        log('Fetching exercises in session...', 'info');
        const exercises = await redisClient.sMembers(exercisesKey);
        
        if (exercises.length === 0) {
            log('No exercises found in session (set is empty or doesn\'t exist)', 'error');
        } else {
            log(`Exercises in session: [${exercises.join(', ')}]`, 'data');
            console.log(colors.cyan + `  ${exercisesKey} → SET with ${exercises.length} exercise(s)` + colors.reset);
            exercises.forEach(ex => {
                console.log(`    - Exercise ID: ${ex}`);
            });
        }

        // 2. Get count
        console.log();
        log('Fetching exercise count...', 'info');
        const count = await redisClient.get(countKey);
        
        if (count === null) {
            log('Count not found (key doesn\'t exist)', 'error');
        } else {
            log(`Total unique exercises: ${count}`, 'data');
            console.log(colors.cyan + `  ${countKey} → ${count}` + colors.reset);
        }

        // 3. Get muscle group counts
        console.log();
        log('Fetching muscle group counts...', 'info');
        const muscleCounts = await redisClient.hGetAll(muscleCountsKey);
        
        if (Object.keys(muscleCounts).length === 0) {
            log('Muscle group counts not found (hash is empty or doesn\'t exist)', 'error');
        } else {
            log('Muscle group distribution:', 'data');
            console.log(colors.cyan + `  ${muscleCountsKey} → HASH` + colors.reset);
            for (const [muscle, muscleCount] of Object.entries(muscleCounts)) {
                console.log(`    - ${muscle}: ${muscleCount} exercise(s)`);
            }
        }

        // Summary
        section('Summary');
        const hasData = exercises.length > 0 || count !== null || Object.keys(muscleCounts).length > 0;
        
        if (hasData) {
            log('✨ Session state found in Redis cache!', 'success');
            console.log('\n' + colors.green + 'Redis Keys:' + colors.reset);
            console.log(`  ${exercisesKey}`);
            console.log(`  ${countKey}`);
            console.log(`  ${muscleCountsKey}`);
        } else {
            log('⚠️  No session data found for this workout ID', 'error');
            log('This could mean:', 'info');
            console.log('  - The workout hasn\'t been started yet');
            console.log('  - No exercises have been logged');
            console.log('  - The session expired (TTL: 5 hours)');
            console.log('  - The workout ID is incorrect');
        }

    } catch (error) {
        section('Error');
        log(`Failed to check Redis session: ${error.message}`, 'error');
        console.error('Full error:', error);
    } finally {
        // Always disconnect
        await redisClient.disconnect();
        log('Disconnected from Redis', 'info');
    }
}

/**
 * Verify Redis session data matches expectations
 * @param {Object} redisData - Data returned from checkRedisSession
 * @param {number} expectedExerciseCount - Expected number of unique exercises
 * @returns {boolean} True if all checks pass
 */
export function verifyRedisSession(redisData, expectedExerciseCount) {
    if (!redisData) {
        log('No Redis data to verify', 'error');
        return false;
    }

    console.log('\n' + colors.yellow + 'Verification:' + colors.reset);
    let allPassed = true;

    const actualExercises = redisData.exercises.length;
    if (actualExercises === expectedExerciseCount) {
        log(`✓ Exercise count matches: ${actualExercises}/${expectedExerciseCount}`, 'success');
    } else {
        log(`✗ Exercise count mismatch: ${actualExercises}/${expectedExerciseCount}`, 'error');
        allPassed = false;
    }
    
    if (redisData.count === expectedExerciseCount) {
        log(`✓ Count key matches: ${redisData.count}`, 'success');
    } else {
        log(`✗ Count key mismatch: ${redisData.count} (expected ${expectedExerciseCount})`, 'error');
        allPassed = false;
    }
    
    const muscleGroupCount = Object.keys(redisData.muscleCounts).length;
    log(`✓ Muscle groups tracked: ${muscleGroupCount}`, 'success');

    return allPassed;
}

// ==========================================
// HELPER FUNCTIONS
// ==========================================

/**
 * Sleep for a specified number of milliseconds
 */
export function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Resolve exercise IDs from names using the lookup map
 * @param {Map} exerciseLookup - Exercise lookup map
 * @param {Array} exerciseNames - Array of exercise names to look up
 * @returns {Array} Array of exercise objects with id, name, variant, muscle
 */
export function resolveExercises(exerciseLookup, exerciseNames) {
    const exercises = [];
    
    for (const exerciseName of exerciseNames) {
        const exercise = exerciseLookup.get(exerciseName.toLowerCase());
        if (!exercise) {
            log(`⚠️  Exercise not found: "${exerciseName}"`, 'error');
            log('Available exercises:', 'info');
            const sample = Array.from(exerciseLookup.keys()).slice(0, 10);
            sample.forEach(key => console.log(`  - ${key}`));
            throw new Error(`Exercise "${exerciseName}" not found in database`);
        }
        exercises.push(exercise);
        log(`  ✓ Found: "${exerciseName}" → ID ${exercise.id} (${exercise.muscle})`, 'success');
    }
    
    return exercises;
}

/**
 * Format exercise name with variant
 */
export function formatExerciseName(exercise) {
    const parts = [];
    if (exercise.variant) parts.push(exercise.variant);
    if (exercise.name) parts.push(exercise.name);
    return parts.join(' ');
}

/**
 * Display recommendation results
 * @param {Object} recommendation - Recommendation response object
 * @param {string} afterExercise - Name of the exercise completed before this recommendation
 */
export function displayRecommendation(recommendation, afterExercise) {
    if (!recommendation) {
        log('No recommendation data', 'error');
        return;
    }

    log(`  Recommended: ${recommendation.top_muscle} / ${recommendation.top_machine} / ${recommendation.top_type}`, 'recommendation');
    
    if (recommendation.recommendations && recommendation.recommendations.length > 0) {
        const topRec = recommendation.recommendations[0];
        const exerciseName = formatExerciseName(topRec);
        log(`  Top recommendation: ${exerciseName}`, 'recommendation');
    }
}
