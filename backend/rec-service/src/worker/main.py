import logging
import json

from core import recommendation_core, set_cached_recommendation, get_cached_recommendation

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

def handler(event, context):
    for record in event["Records"]:
        message_id = record.get("messageId")
        
        try:
            body = json.loads(record["body"])
            user_id = body["user_id"]
            workout_id = int(body["workout_id"])
            workout_name = body["workout_name"]
            exercise_id = int(body["exercise_id"])
            workout_position = int(body["workout_position"])
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.warning("Invalid message body message_id=%s: %s", message_id, str(e))
            continue

        logger.info("processing message_id=%s user_id=%s workout_id=%s exercise_id=%s workout_position=%s",
            message_id, user_id, workout_id, exercise_id, workout_position)

        if get_cached_recommendation(workout_id, workout_position, exercise_id): 
            logger.info("recommendation already in cache")
            continue 

        cache_key = f"session:{workout_id}:recommendation:{exercise_id}:{workout_position}"
        try:
            result = recommendation_core(workout_id, workout_name, exercise_id, user_id)
            set_cached_recommendation(workout_id, workout_position, exercise_id, result)
            logger.info("cached result key=%s", cache_key)
        except Exception as e:
            logger.exception("recommendation failed message_id=%s: %s", message_id, str(e))
            raise