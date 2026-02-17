/**
 * FlexLog Basic Authentication Test
 * Tests authentication flow and basic API calls to both services
 */

import {
    config,
    validateConfig,
    signInUser,
    createWorkout,
    getRecommendation,
    log,
    colors
} from './test-utils.js';

// ==========================================
// MAIN TEST FLOW
// ==========================================
async function runTest() {
    console.log('\n' + '='.repeat(60));
    log('🏋️  FlexLog Authentication Test', 'info');
    console.log('='.repeat(60) + '\n');

    // Validate configuration
    validateConfig();

    try {
        // Step 1: Sign in with existing account
        log('Step 1: Signing in to your account...', 'info');
        const { user, token } = await signInUser();

        // Step 2: Create a workout
        log('\nStep 2: Creating workout via Tracking API (Spring Boot)...', 'info');
        const workout = await createWorkout(token, 'chest back biceps');
        log('Workout created successfully!', 'success');
        console.log('\nWorkout details:');
        console.log(JSON.stringify(workout, null, 2));

        // Step 3: Get recommendations
        log('\nStep 3: Getting recommendations via Recommendation API (FastAPI)...', 'info');
        const recommendations = await getRecommendation(token, workout.id, 'chest back biceps', 1);
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
