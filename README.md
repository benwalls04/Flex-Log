# FlexLog

A **personalized workout tracking and recommendation system** that helps users log workouts, track progress, and get exercise recommendations based on their history and session context.

---

## Motivation

Users often repeat the same exercises or struggle to choose what to do next. FlexLog uses per-user machine learning to predict preferred exercise attributes (muscle group, equipment, movement type) from context—current workout, session position, and prior counts—then recommends exercises that match those preferences while accounting for how often the user does each exercise. The goal is to make recommendations feel relevant and varied without requiring manual configuration.

---

## Capabilities

- **Recommendation API** — Given a workout session and current exercise, returns top exercise recommendations. Uses per-user Ridge models (trained on historical logs), session state from Redis (exercises done, muscle-group counts, position), and a weighted score combining prediction similarity and user frequency.
- **Batch training** — A separate Lambda runs training per user: reads workout logs from Postgres, builds context features (day flags, previous counts, position), trains Ridge regression models for muscle, machine, and exercise-type targets, and uploads models to S3 for the recommendation service.
- **Authentication** — API Gateway HTTP API with a Lambda authorizer that validates Supabase JWTs (HS256) and passes the user id into the recommendation Lambda so requests are scoped to the authenticated user.
- **Session state** — Redis holds per-workout session data (exercise ids done, muscle-group counts, position) so recommendations can avoid already-done exercises and reflect in-session progress.

---

## Technologies

| Layer | Technology |
|-------|------------|
| **Recommendation API** | Python, AWS Lambda (container), API Gateway HTTP API |
| **Training** | Python, scikit-learn (Ridge), AWS Lambda (container) |
| **Auth** | Lambda authorizer, Supabase JWT (HS256) |
| **Database** | PostgreSQL (Supabase) |
| **Session cache** | Redis |
| **Model storage** | S3 |
| **Secrets** | AWS Secrets Manager |
| **Infrastructure** | AWS CDK (Python) |

---

## Deployment architecture

- **Rec-service** — Single Lambda (Docker image) behind API Gateway. One route (e.g. `POST /recommendation`) with the Lambda authorizer. Request body: `workout_id`, `workout_name`, `exercise_id`; `user_id` comes from the authorizer context. Lambda loads DB and Redis config from Secrets Manager, reads models from S3, uses one DB connection per invocation (released in `finally`), and caches the Redis client per container.
- **Training-service** — Lambda (Docker image) triggered on demand or on a schedule. Fetches logs from Postgres via Secrets Manager credentials, trains per-user models, writes `user_{id}/muscle.joblib`, `machine.joblib`, and `type.joblib` to the `flexlog-models` S3 bucket.
- **Authorizer** — Lambda that receives the token from API Gateway’s identity source (e.g. `Authorization` header), validates it with the Supabase JWT secret, and returns `isAuthorized` plus `context.user_id` for HTTP API (payload 2.0).

All three Lambdas are deployed with CDK from their respective stacks; the recommendation and training images are built from Dockerfiles at deploy time (`cdk deploy`).

---

## System design and scalability

- **Serverless** — Recommendation and training run on Lambda, so capacity scales with request volume without managing servers. Cold starts are mitigated by container reuse and by keeping dependencies and connection setup minimal.
- **Per-user models** — Each user has their own Ridge models in S3. Training runs per user and only updates that user’s objects; the recommendation Lambda loads only the three objects for the requesting user, which keeps payloads small and avoids cross-user coupling.
- **Connection handling** — The recommendation Lambda opens one Postgres connection per invocation and closes it in a `finally` block so it is always released on success or failure. Redis client is reused per container to avoid repeated connections.
- **Secrets and config** — DB and Redis connection details live in Secrets Manager; Lambdas receive only secret names via environment variables and fetch at runtime, keeping images and config separate and rotation-friendly.
- **Stateless API** — The recommendation endpoint is stateless aside from session data in Redis; any Lambda instance can serve any user, which fits horizontal scaling and multiple API Gateway stages or regions if needed later.

---

## Repository structure

- `backend/rec-service/` — Recommendation Lambda (CDK stack + `image/` with Dockerfile and Python handler).
- `backend/training-service/` — Training Lambda (CDK stack + `image/` with Dockerfile and training script).
- `backend/authorizer/` — Lambda authorizer (JWT validation for API Gateway).

Deploy from the root of each service (where `cdk.json` and `app.py` live), e.g. `cd backend/rec-service && cdk deploy`.
