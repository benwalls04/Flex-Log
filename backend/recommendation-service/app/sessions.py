"""
Redis session management for workout tracking.
Manages exercise tracking, muscle group counts, and workout position within Redis cache.
"""

import os
import psycopg2

def get_redis_client():
    """Get the shared Redis client from application state"""
    from app.dependencies import get_redis_client as get_client
    return get_client()

def get_db_connection():
    """Get a database connection from the pool"""
    from app.dependencies import get_db_connection as get_pool_connection
    return get_pool_connection()

def release_db_connection(conn):
    """Return a database connection to the pool"""
    from app.dependencies import release_db_connection as release_conn
    release_conn(conn)

def add_exercise_to_session(workout_id: int, exercise_id: int):
    """
    Add an exercise to the Redis session cache for a workout.
    Tracks: exercise IDs, total count, and muscle group distribution.
    """
    redis_client = get_redis_client()
    
    # Add exercise ID to set
    exercises_key = f"session:{workout_id}:exercises"
    redis_client.sadd(exercises_key, exercise_id)
    redis_client.expire(exercises_key, 18000)  # 5 hour TTL

    # Increment total count
    count_key = f"session:{workout_id}:count"
    redis_client.incr(count_key)
    redis_client.expire(count_key, 18000)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT muscle_group FROM exercises WHERE id = %s",
                (exercise_id,)
            )
            row = cursor.fetchone()
            muscle_group = row[0] if row else None
            
            if muscle_group:
                muscle_counts_key = f"session:{workout_id}:muscle_counts"
                redis_client.hincrby(muscle_counts_key, muscle_group, 1)
                redis_client.expire(muscle_counts_key, 18000)
    finally:
        release_db_connection(conn)

def get_session_exercises(workout_id: int) -> set:
    """Get all exercise IDs from the session cache"""
    redis_client = get_redis_client()
    key = f"session:{workout_id}:exercises"
    exercises = redis_client.smembers(key)
    return {int(ex_id) for ex_id in exercises} if exercises else set()

def get_muscle_group_counts(workout_id: int):
    """Get muscle group distribution from the session cache"""
    redis_client = get_redis_client()
    key = f"session:{workout_id}:muscle_counts"
    raw_hash = redis_client.hgetall(key)
    return {k: int(v) for k, v in raw_hash.items()}

def get_session_position(workout_id: int):
    """Get the current exercise position/count in the workout"""
    redis_client = get_redis_client()
    key = f"session:{workout_id}:count"
    count = redis_client.get(key)
    return int(count) if count else 0
