# FlexLog Frontend Test Scripts

## Authentication Test

### Setup

1. Install dependencies:
```bash
npm install
```

2. Update configuration in `test-auth.js`:
   - Get Supabase anon key:
     - Go to [Supabase Dashboard](https://supabase.com/dashboard)
     - Select your project
     - Go to Settings > API
     - Copy the `anon` `public` key
     - Replace `YOUR_SUPABASE_ANON_KEY_HERE` in `test-auth.js`
   - Update your credentials:
     - Replace `YOUR_EMAIL_HERE` with your email
     - Replace `YOUR_PASSWORD_HERE` with your password

### Run the test

```bash
npm test
```

Or directly:
```bash
node test-auth.js
```

### What it does

1. Signs in to your existing Supabase account
2. Gets a JWT access token
3. Calls `POST /api/workouts/` (Spring Boot) with the token to create a workout
4. Calls `GET /recommendation` (FastAPI) with the token to get exercise recommendations
5. Tests authentication on both services

### Prerequisites

- Spring Boot tracking-service running on `http://localhost:8080`
- FastAPI recommendation-service running on `http://localhost:8000`
- Supabase project configured
- Both services have the same JWT_SECRET configured
- Email confirmation disabled in Supabase (or handle confirmation flow)
