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

// ==========================================
// LOGGING UTILITIES
// ==========================================
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    blue: '\x1b[34m',
    yellow: '\x1b[33m',
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
    }

    console.log(`${color}[${timestamp}] ${prefix} ${message}${colors.reset}`);
}

// ==========================================
// SUPABASE AUTH FUNCTIONS
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

    if (!data.user) {
        throw new Error('No user returned from Supabase sign-in');
    }

    if (!data.session || !data.session.access_token) {
        throw new Error('No session/token returned from sign-in.');
    }

    log(`Signed in successfully! User ID: ${data.user.id}`, 'success');
    log(`Access token received (${data.session.access_token.length} chars)`, 'success');

    return {
        user: data.user,
        token: data.session.access_token
    };
}

// ==========================================
// TRACKING SERVICE API FUNCTIONS (Spring Boot)
// ==========================================
async function createWorkout(accessToken) {
    const workoutData = {
        name: 'chest back biceps',
        date: new Date().toISOString(),
    };

    log(`Sending workout data: ${JSON.stringify(workoutData)}`, 'info');
    log(`Using Authorization header: Bearer ${accessToken.substring(0, 20)}...`, 'info');

    const response = await fetch(`${TRACKING_API_URL}/workouts/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(workoutData)
    });

    log(`Response status: ${response.status} ${response.statusText}`, response.ok ? 'success' : 'error');

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Tracking API failed: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    return result;
}

// ==========================================
// RECOMMENDATION SERVICE API FUNCTIONS (FastAPI)
// ==========================================
async function getRecommendation(accessToken, workoutId) {
    const params = new URLSearchParams({
        workout_id: workoutId,
        workout_name: 'chest back biceps',
        exercise_id: 1  // Using exercise ID 1 as test
    });

    const url = `${RECOMMENDATION_API_URL}/recommendation?${params}`;
    
    log(`Calling recommendation endpoint: ${url}`, 'info');
    log(`Using Authorization header: Bearer ${accessToken.substring(0, 20)}...`, 'info');

    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });

    log(`Response status: ${response.status} ${response.statusText}`, response.ok ? 'success' : 'error');

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Recommendation API failed: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    return result;
}

// ==========================================
// MAIN TEST FLOW
// ==========================================
async function runTest() {
    console.log('\n' + '='.repeat(60));
    log('🏋️  FlexLog Authentication Test', 'info');
    console.log('='.repeat(60) + '\n');

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

    // Initialize Supabase client
    const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

    try {
        // Step 1: Sign in with existing account
        log('Step 1: Signing in to your account...', 'info');
        const { user, token } = await signInUser(supabase);

        // Step 2: Create a workout
        log('\nStep 2: Creating workout via Tracking API (Spring Boot)...', 'info');
        const workout = await createWorkout(token);
        log('Workout created successfully!', 'success');
        console.log('\nWorkout details:');
        console.log(JSON.stringify(workout, null, 2));

        // Step 3: Get recommendations
        log('\nStep 3: Getting recommendations via Recommendation API (FastAPI)...', 'info');
        const recommendations = await getRecommendation(token, workout.id);
        log('Recommendations retrieved successfully!', 'success');
        console.log('\nRecommendation results:');
        console.log(JSON.stringify(recommendations, null, 2));

        console.log('\n' + '='.repeat(60));
        log('🎉 All tests passed! Both services authenticated successfully.', 'success');
        console.log('='.repeat(60) + '\n');

    } catch (error) {
        console.log('\n' + '='.repeat(60));
        log(`Test failed: ${error.message}`, 'error');
        console.log('='.repeat(60) + '\n');
        console.error('Full error:', error);
        process.exit(1);
    }
}

// ==========================================
// RUN THE TEST
// ==========================================
runTest();
