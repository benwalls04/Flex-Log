import { createClient } from 'redis';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: '.env.test' });

// ==========================================
// CONFIGURATION
// ==========================================
const REDIS_HOST = process.env.REDIS_HOST;
const REDIS_PORT = parseInt(process.env.REDIS_PORT);
const REDIS_PASSWORD = process.env.REDIS_PASSWORD;

// Get workout ID from command line args or use default
const WORKOUT_ID = process.argv[2] || null;

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
        case 'data':
            color = colors.cyan;
            prefix = '📊';
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
// REDIS CONNECTION
// ==========================================
async function checkRedisSession(workoutId) {
    section('Redis Session State Checker');

    // Validate configuration
    if (!REDIS_HOST || !REDIS_PORT || !REDIS_PASSWORD) {
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
    log(`Connecting to Redis at ${REDIS_HOST}:${REDIS_PORT}...`, 'info');

    // Create Redis client
    const redisClient = createClient({
        socket: {
            host: REDIS_HOST,
            port: REDIS_PORT,
        },
        password: REDIS_PASSWORD,
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
            for (const [muscle, count] of Object.entries(muscleCounts)) {
                console.log(`    - ${muscle}: ${count} exercise(s)`);
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

// ==========================================
// RUN THE CHECKER
// ==========================================
checkRedisSession(WORKOUT_ID);
