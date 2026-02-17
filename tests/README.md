# FlexLog Frontend Testing

This directory contains test scripts for validating the FlexLog backend services (tracking-service and recommendation-service).

## Test Structure

### Test Utilities (`test-utils.js`)
Shared module containing reusable functions for all tests:

**Authentication**
- `signInUser()` - Sign in with Supabase and get JWT token

**Tracking Service (Spring Boot)**
- `getAllExercises(token)` - Fetch all exercises from database
- `buildExerciseLookup(exercises)` - Create exercise name → ID lookup map
- `resolveExercises(lookup, names)` - Resolve exercise IDs from names
- `createWorkout(token, name)` - Create a new workout session
- `createLog(token, workoutId, exerciseId, weight, reps, isFirst)` - Log a single set
- `logExerciseSets(token, workoutId, exercise, numSets, isFirst, options)` - Log multiple sets

**Recommendation Service (FastAPI)**
- `getRecommendation(token, workoutId, workoutName, lastExerciseId)` - Get exercise recommendations

**Redis Session Management**
- `checkRedisSession(workoutId)` - Retrieve session state from Redis (compact)
- `checkRedisSessionDetailed(workoutId)` - Detailed Redis check with verbose logging (for standalone script)
- `verifyRedisSession(redisData, expectedCount)` - Verify Redis data matches expectations

**Utilities**
- `log(message, type)` - Colored console logging
- `section(title)` - Print formatted section headers
- `sleep(ms)` - Async sleep helper
- `validateConfig()` - Validate environment variables
- `displayRecommendation(rec, afterExercise)` - Pretty-print recommendations
- `formatExerciseName(exercise)` - Format exercise name with variant

### Test Scripts

#### `test-auth.js`
Basic authentication test that validates:
- Supabase authentication
- Creating a workout via tracking-service
- Getting recommendations via recommendation-service

**Run with:**
```bash
npm test
```

#### `test-session.js`
Comprehensive session test that validates:
- Complete workout flow with multiple exercises
- Redis session cache tracking
- Exercise logging (3 sets per exercise)
- Recommendation generation after each exercise
- Redis state verification

**Run with:**
```bash
npm run test:session
```

#### `test-model-workout.js`
Model-driven workout builder that creates a complete workout based on recommendation engine:
- Takes parameters: workout name, number of exercises, sets per exercise
- Gets recommendations from the model for each exercise
- Logs all sets for the recommended exercise
- Displays final workout plan with muscle distribution

**Run with:**
```bash
# Default: "full body" workout, 5 exercises, 3 sets each
npm run test:model

# Custom workout
node test-model-workout.js "chest back arms" 6 4

# Parameters: <workout_name> <num_exercises> <sets_per_exercise>
```

**Note:** Requires trained models in S3 for the test user.

#### `check-redis-session.js`
Standalone script to inspect Redis session state for a specific workout ID.

**Run with:**
```bash
npm run check:redis <workout_id>
```

## Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Create a `.env.test` file based on `.env.test.example`:

```bash
cp .env.test.example .env.test
```

Fill in your configuration:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Test User Credentials
TEST_EMAIL=your-test@email.com
TEST_PASSWORD=your-password

# API Endpoints
TRACKING_API_URL=http://localhost:8080/api
RECOMMENDATION_API_URL=http://localhost:8000

# Redis Configuration (optional, for session checks)
REDIS_HOST=your-redis-host.com
REDIS_PORT=17726
REDIS_PASSWORD=your-redis-password
```

### 3. Start Backend Services
Make sure both services are running:

**Tracking Service (Spring Boot)**
```bash
cd backend/tracking-service
./run-dev.ps1  # Windows PowerShell
```

**Recommendation Service (FastAPI)**
```bash
cd backend/recommendation-service
docker build -t recommendation-service .
docker run -p 8000:8000 --env-file .env recommendation-service
```

### 4. Run Tests
```bash
# Basic authentication test
npm test

# Full session test with Redis validation
npm run test:session

# Model-driven workout builder (requires trained models)
npm run test:model
# Or with custom parameters:
node test-model-workout.js "chest day" 5 3

# Check Redis session state
npm run check:redis <workout_id>
```

## Example Output

### Model-Driven Workout (`npm run test:model`)

```
🤖 FlexLog Model-Driven Workout Builder
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Model-Built Workout Plan:
   Workout: chest back arms
   Workout ID: 127
   Total Exercises: 5
   Total Sets: 15

1. barbell bench press
   Muscle Group: chest
   Sets: 3 x 135lbs x 12 reps
   Recommendation Context: chest / barbell / compound

2. cable row
   Muscle Group: back
   Sets: 3 x 135lbs x 12 reps
   Recommendation Context: back / cable / compound

3. dumbbell fly
   Muscle Group: chest
   Sets: 3 x 135lbs x 12 reps
   Recommendation Context: chest / dumbbell / isolation

4. lat pulldown
   Muscle Group: back
   Sets: 3 x 135lbs x 12 reps
   Recommendation Context: back / machine / compound

5. barbell curl
   Muscle Group: biceps
   Sets: 3 x 135lbs x 12 reps
   Recommendation Context: arms / barbell / isolation

💪 Muscle Group Distribution:
   chest: 2 exercises (40.0%)
   back: 2 exercises (40.0%)
   biceps: 1 exercise (20.0%)
```

## Writing New Tests

To create a new test, import the utilities module:

```javascript
import {
    signInUser,
    createWorkout,
    logExerciseSets,
    getRecommendation,
    log,
    section
} from './test-utils.js';

async function myTest() {
    section('MY TEST');
    
    // Authenticate
    const { user, token } = await signInUser();
    log('Signed in!', 'success');
    
    // Create workout
    const workout = await createWorkout(token, 'chest day');
    log(`Workout ${workout.id} created`, 'success');
    
    // Log sets
    await logExerciseSets(token, workout.id, exercise, 3, true);
    
    // Get recommendations
    const rec = await getRecommendation(token, workout.id, 'chest day', exercise.id);
    log('Received recommendations', 'success');
}

myTest();
```

## Troubleshooting

### "Missing SUPABASE_ANON_KEY"
- Ensure `.env.test` exists and contains all required variables
- Check that you're running tests from the `frontend` directory

### "Get exercises failed: 403"
- Verify your JWT_SECRET in tracking-service matches Supabase's HS256 secret
- Check that both services are running
- Confirm your test user exists in Supabase Auth

### "Redis check failed"
- Verify Redis credentials in `.env.test`
- Check that Redis connection allows external connections
- Ensure tracking-service is successfully connecting to Redis

### "Exercise not found"
- Check that exercises exist in your database
- Verify exercise names in `TEST_EXERCISE_NAMES` match database format: `"variant name"` (e.g., `"barbell bench press"`)
- Use lowercase names

### "Recommendation failed: 500" or "No exercise recommendations returned"
- Check if user models have been trained (`pipeline.py`)
- Verify S3 bucket contains model files for the test user (`user_<uuid>/machine.joblib`, `user_<uuid>/type.joblib`, `user_<uuid>/muscle.joblib`)
- Check recommendation-service logs for detailed errors
- The `test:model` script requires trained models to work properly
