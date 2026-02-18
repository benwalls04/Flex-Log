# FlexLog

A **personalized workout tracking and recommendation system** that helps users log workouts, track progress, and get exercise recommendations based on their history and session context. The system is built as **scalable, containerized microservices** so each component can be deployed, scaled, and updated independently.

---

## Motivation

Users often repeat the same exercises or struggle to choose what to do next. FlexLog uses per-user machine learning to predict preferred exercise attributes (muscle group, equipment, movement type) from context—current workout, session position, and prior counts—then recommends exercises that match those preferences while accounting for how often the user does each exercise. The goal is to make recommendations feel relevant and varied without requiring manual configuration.

---

## Capabilities

- **Recommendation API** — Given a workout session and current exercise, returns top exercise recommendations. Uses per-user Ridge models (trained on historical logs), session state from Redis (exercises done, muscle-group counts, position), and a weighted score combining prediction similarity and user frequency.
- **Async pre-computation with caching** — To avoid latency when the user finishes an exercise, recommendations are triggered when a new workout is selected. The request is sent to SQS; a worker computes recommendations asynchronously and caches the result (e.g. Redis). By the time the user needs the recommendation (5+ minutes later), the result is served from cache for a fast read.
- **Batch training** — A Lambda runs training per user: reads workout logs from Postgres, builds context features (day flags, previous counts, position), trains Ridge regression models for muscle, machine, and exercise-type targets, and uploads models to S3. Invoked weekly via EventBridge; users whose logs have not been updated since the last run are filtered out to save compute.
- **Tracking service (Spring Boot)** — A Spring Boot application for workout logging, exercise catalog, and progress tracking, deployed on AWS Elastic Beanstalk (containerized). Its endpoints are integrated with the same API Gateway as the recommendation service.
- **Authentication** — A single API Gateway HTTP API fronts all microservices (auth, tracking, recommendations). A Lambda authorizer validates Supabase JWTs (HS256) and passes the user id into downstream services.
- **Session state** — Redis holds per-workout session data (exercise ids done, muscle-group counts, position) so recommendations can avoid already-done exercises and reflect in-session progress.

---

## Technologies

| Layer | Technology |
|-------|------------|
| **Recommendation API** | Python, AWS Lambda (container), API Gateway HTTP API |
| **Tracking** | Spring Boot, AWS Elastic Beanstalk (container) |
| **Training** | Python, scikit-learn (Ridge), AWS Lambda (container) |
| **Auth** | Lambda authorizer, Supabase JWT (HS256) |
| **Database** | PostgreSQL (Supabase) |
| **Session / recommendation cache** | Redis |
| **Async recommendation queue** | SQS |
| **Training schedule** | EventBridge (cron) |
| **Model storage** | S3 |
| **Secrets** | AWS Secrets Manager |
| **Infrastructure** | AWS CDK (Python) |

---

## Deployment architecture

- **Shared API Gateway** — One HTTP API fronts auth, tracking, and recommendations. The Lambda authorizer validates the Supabase JWT and injects `user_id` into the request context for all protected routes.
- **Rec-service** — Lambda (Docker image) behind API Gateway. Recommendation requests can be synchronous or, for pre-computation, enqueued to SQS; a worker Lambda (or same service) processes the queue and caches results in Redis so clients read from cache when the user needs recommendations. Lambda loads DB and Redis config from Secrets Manager, reads models from S3, uses one DB connection per invocation (released in `finally`), and caches the Redis client per container.
- **Tracking service** — Spring Boot application running in Docker on **Elastic Beanstalk**. Handles workout logging, exercise catalog, and progress; its REST endpoints are registered on the same API Gateway so clients use one base URL and one auth flow.
- **Training-service** — Lambda (Docker image) invoked weekly by **EventBridge** (cron). Fetches logs from Postgres via Secrets Manager, filters to users whose logs have been updated since the last run, trains per-user models, and writes `user_{id}/muscle.joblib`, `machine.joblib`, and `type.joblib` to the `flexlog-models` S3 bucket.
- **Authorizer** — Lambda that receives the token from API Gateway’s identity source (e.g. `Authorization` header), validates it with the Supabase JWT secret, and returns `isAuthorized` plus `context.user_id` for HTTP API (payload 2.0).

Recommendation and training Lambdas are deployed with CDK; images are built from Dockerfiles at deploy time (`cdk deploy`). All services are containerized (Lambda container images or Elastic Beanstalk) so the stack is consistently deployable and scalable as microservices.

---

## System design and scalability

- **Serverless** — Recommendation and training run on Lambda, so capacity scales with request volume without managing servers. Cold starts are mitigated by container reuse and by keeping dependencies and connection setup minimal.
- **Per-user models** — Each user has their own Ridge models in S3. Training runs per user and only updates that user’s objects; the recommendation Lambda loads only the three objects for the requesting user, which keeps payloads small and avoids cross-user coupling.
- **Connection handling** — The recommendation Lambda opens one Postgres connection per invocation and closes it in a `finally` block so it is always released on success or failure. Redis client is reused per container to avoid repeated connections.
- **Secrets and config** — DB and Redis connection details live in Secrets Manager; Lambdas receive only secret names via environment variables and fetch at runtime, keeping images and config separate and rotation-friendly.
- **Stateless API** — The recommendation endpoint is stateless aside from session data in Redis; any Lambda instance can serve any user, which fits horizontal scaling and multiple API Gateway stages or regions if needed later.
- **Containerized microservices** — Recommendation and training are Docker images on Lambda; the tracking service is containerized on Elastic Beanstalk. A single API Gateway fronts all microservices (auth, tracking, recommendations) so clients use one gateway and one auth model.

---

## Repository structure

- `backend/rec-service/` — Recommendation Lambda (CDK stack + `image/` with Dockerfile and Python handler).
- `backend/training-service/` — Training Lambda (CDK stack + `image/` with Dockerfile and training script).
- `backend/authorizer/` — Lambda authorizer (JWT validation for API Gateway).

Deploy from the root of each service (where `cdk.json` and `app.py` live), e.g. `cd backend/rec-service && cdk deploy`.
