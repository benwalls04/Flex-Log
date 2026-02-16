# FlexLog Frontend Test Scripts

This folder contains Node.js test scripts for the FlexLog API services.

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment variables:**
   ```bash
   # Copy the example file
   cp .env.test.example .env.test
   ```
   
   Then edit `.env.test` and fill in your values:
   - `SUPABASE_ANON_KEY` - Your Supabase Anon Key from the dashboard
   - `TEST_EMAIL` - Your test user's email
   - `TEST_PASSWORD` - Your test user's password

## Running Tests

### Basic Authentication Test

Tests authentication and creates a simple workout:

```bash
npm test
```

This script:
- Signs in to Supabase
- Gets a JWT token
- Creates a workout via tracking-service (Spring Boot)
- Gets a recommendation via recommendation-service (FastAPI)

### Session & Recommendation Test

Tests the full workout session pipeline with Redis session tracking:

```bash
npm run test:session
```

This script:
1. Signs in a test user
2. Fetches all exercises from the database and builds a lookup map
3. Resolves test exercise IDs by variant + name (e.g., "barbell bench press")
4. Creates a workout session
5. Logs 3 different exercises (3 sets each = 9 total logs)
6. Gets recommendations after each exercise
7. Displays Redis session state information

**What it tests:**
- User authentication with Supabase
- Workout creation
- Exercise logging with proper set tracking
- Recommendation engine responses
- Redis session state tracking (exercises, counts, muscle group distribution)

**Expected Redis State:**
- `session:{workout_id}:exercises` - Set containing unique exercise IDs
- `session:{workout_id}:count` - Total unique exercise count (should be 3)
- `session:{workout_id}:muscle_counts` - Hash with muscle group counts

## Prerequisites

### Exercise Names
The `test-session.js` script dynamically fetches all exercises from the database and looks them up by variant + name. Update the `TEST_EXERCISE_NAMES` array in the script if you want to test different exercises:

```javascript
const TEST_EXERCISE_NAMES = [
    'barbell bench press',    // Looks up exercise with variant="barbell" and name="bench press"
    'barbell row',            // Looks up exercise with variant="barbell" and name="row"
    'barbell curl'            // Looks up exercise with variant="barbell" and name="curl"
];
```

The script will automatically resolve these to the correct IDs from your database.

### Services Running
Both test scripts require these services to be running:
- **Tracking Service** (Spring Boot): `http://localhost:8080`
- **Recommendation Service** (FastAPI): `http://localhost:8000`

### Trained Models (for recommendations)
The recommendation endpoint will fail gracefully if models haven't been trained yet. To get actual recommendations:
1. Ensure you have workout history in the database
2. Train models using the `/train_model` endpoint

## Checking Redis Session State

After running `test:session`, you can manually verify the Redis cache state:

### Option 1: Redis CLI
```bash
redis-cli -h YOUR_REDIS_HOST -p YOUR_REDIS_PORT -a YOUR_REDIS_PASSWORD

# Check exercises in session
SMEMBERS session:{workout_id}:exercises

# Check total count
GET session:{workout_id}:count

# Check muscle group distribution
HGETALL session:{workout_id}:muscle_counts
```

### Option 2: Add an Endpoint (Recommended)
Add a debug endpoint to your tracking-service or recommendation-service:

**Spring Boot (tracking-service):**
```java
@GetMapping("/debug/session/{workoutId}")
public Map<String, Object> getSessionState(@PathVariable Integer workoutId) {
    // Return exercises, count, and muscle counts from Redis
}
```

**FastAPI (recommendation-service):**
```python
@app.get("/debug/session/{workout_id}")
def get_session_state(workout_id: int):
    return {
        "exercises": list(get_session_exercises(workout_id)),
        "count": get_session_position(workout_id),
        "muscle_counts": get_muscle_group_counts(workout_id)
    }
```

## Troubleshooting

### "Invalid token: Invalid audience" (FastAPI)
Update `app/auth.py` in recommendation-service to skip audience validation:
```python
payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_aud": False})
```

### 403 Forbidden (Spring Boot)
Ensure your `JWT_SECRET` in `.env` matches the **Legacy HS256 shared secret key** from Supabase:
- Supabase Dashboard → Project Settings → API → JWT keys → Legacy HS256 shared secret key

### Recommendation Returns "test: success"
The recommendation endpoint has a test return statement. Remove the `return {"test": "success"}` line from `main.py` to get actual recommendations.

## Environment Variables

Configuration is managed through `.env.test`, which is gitignored to keep your credentials safe. The test scripts will read from this file automatically.

**Available variables:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous/public key
- `TEST_EMAIL` - Test user email for authentication
- `TEST_PASSWORD` - Test user password
- `TRACKING_API_URL` - Spring Boot API endpoint (default: http://localhost:8080/api)
- `RECOMMENDATION_API_URL` - FastAPI endpoint (default: http://localhost:8000)

## Notes

- `.env.test` is gitignored to protect credentials
- `.env.test.example` is checked into version control as a template
- The scripts use colored console output for better readability
- Small delays (100ms) are added between log entries to ensure proper timestamp ordering
- If you need to share config with the team, update `.env.test.example` (without real credentials)
