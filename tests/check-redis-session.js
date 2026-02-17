/**
 * FlexLog Redis Session State Checker
 * Standalone script to inspect Redis cache for a specific workout ID
 * 
 * Usage: npm run check:redis <workout_id>
 * Example: npm run check:redis 26
 */

import { checkRedisSessionDetailed } from './test-utils.js';

// Get workout ID from command line args
const WORKOUT_ID = process.argv[2] || null;

// ==========================================
// RUN THE CHECKER
// ==========================================
checkRedisSessionDetailed(WORKOUT_ID);
