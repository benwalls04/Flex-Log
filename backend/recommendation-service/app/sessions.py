import redis
import os
import sqlite3
from pathlib import Path

redis_client = redis.Redis(
    host='redis-14082.c263.us-east-1-2.ec2.cloud.redislabs.com',
    port=14082,
    decode_responses=True,
    username="default",
    password=os.getenv("REDIS_PASSWORD"),
)

if "DATABASE_PATH" in os.environ:
    DB_PATH = Path(os.environ["DATABASE_PATH"])
else:
    DB_PATH = (
        Path(__file__).resolve()
        .parents[3]   
        / "data"
        / "test_database.db"
    )

def add_exercise_to_session(workout_id: int, exercise_id: int):
    exercises_key  = f"session:{workout_id}:exercises"
    redis_client.sadd(exercises_key , exercise_id)
    redis_client.expire(exercises_key , 18000)    

    count_key = f"session:{workout_id}:count"
    redis_client.incr(count_key)
    redis_client.expire(count_key, 18000)

    with sqlite3.connect(DB_PATH) as conn: 
        cursor = conn.cursor()
        cursor.execute("SELECT muscle_group from exercises WHERE id = ?)", 
        (exercise_id, ))
        muscle_group = cursor.fetchone()[0]

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
