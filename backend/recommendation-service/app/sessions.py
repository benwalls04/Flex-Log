import redis
import os

redis_client = redis.Redis(
    host='redis-14082.c263.us-east-1-2.ec2.cloud.redislabs.com',
    port=14082,
    decode_responses=True,
    username="default",
    password=os.getenv("REDIS_PASSWORD"),
)


def add_exercise_to_session(workout_id: int, exercise_id: int):
    key = f"session:{workout_id}:exercises"
    redis_client.sadd(key, exercise_id)
    redis_client.expire(key, 18000)  

# Get all exercises from session
def get_session_exercises(workout_id: int) -> set:
    print(os.getenv("REDIS_PASSWORD"))

    key = f"session:{workout_id}:exercises"
    exercises = redis_client.smembers(key)
    return {int(ex_id) for ex_id in exercises} if exercises else set()