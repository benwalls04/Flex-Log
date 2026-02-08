import redis
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
redis_client = redis.Redis(
    host=os.getenv("REDIS_ENDPOINT"),
    port=14082,
    decode_responses=True,
    username="default",
    password=os.getenv("REDIS_PASSWORD"),
)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db.kauffaiclsbufnwyiuau.supabase.co"),
    "port": os.environ.get("DB_PORT", "5432"),
    "database": os.environ.get("DB_NAME", "postgres"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD"),
    "sslmode": "require",
}

def get_db_connection():
    """Create and return a PostgreSQL (Supabase) connection."""
    return psycopg2.connect(**DB_CONFIG)

def add_exercise_to_session(workout_id: int, exercise_id: int):
    exercises_key = f"session:{workout_id}:exercises"
    redis_client.sadd(exercises_key, exercise_id)
    redis_client.expire(exercises_key, 18000)

    count_key = f"session:{workout_id}:count"
    redis_client.incr(count_key)
    redis_client.expire(count_key, 18000)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT muscle_group FROM exercises WHERE id = %s",
                (exercise_id,),
            )
            row = cursor.fetchone()
            muscle_group = row[0] if row else None

    if muscle_group is None:
        return

    redis_client.hincrby(
        f"session:{workout_id}:muscle_counts",
        muscle_group,
        1
    )
    redis_client.expire(f"session:{workout_id}:muscle_counts", 18000)

# Get all exercises from session
def get_session_exercises(workout_id: int) -> set:
    key = f"session:{workout_id}:exercises"
    exercises = redis_client.smembers(key)
    return {int(ex_id) for ex_id in exercises} if exercises else set()

def get_muscle_group_counts(workout_id: int):
    key = f"session:{workout_id}:muscle_counts"
    raw_hash = redis_client.hgetall(key)
    return {k: int(v) for k, v in raw_hash.items()}

def get_session_position(workout_id : int):
    key = f"session:{workout_id}:count"
    count = redis_client.get(key)
    return int(count) if count else 0
