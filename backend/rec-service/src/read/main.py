import logging
import json

from core import recommendation_core, get_cached_recommendation

logging.getLogger().setLevel(logging.INFO)  
logger = logging.getLogger(__name__)

def handler(event, context):
    request_id = getattr(context, "aws_request_id", None)
    logger.info("request start request_id=%s", request_id)
    
    try: 
        request_context = event.get("requestContext")
        authorizer = request_context.get("authorizer")
        user_id = authorizer.get("lambda", {}).get("user_id")
    except Exception as e: 
        logger.warning("Error retrieving userId %s", str(e))
        return {"statusCode": 401, "body": json.dumps({"error": "Unauthorized"})}

    if not user_id:
        logger.warning("user_id missing from authorizer context")
        return {"statusCode": 401, "body": json.dumps({"error": "Unauthorized"})}

    logger.info("request_context=%s authorizer=%s user_id=%s", request_context, authorizer, user_id)

    try:
        body = event.get("body", event)
        if isinstance(body, str):
            body = json.loads(body)
        workout_id = int(body["workout_id"])
        workout_name = body["workout_name"]
        exercise_id = int(body["exercise_id"])
        workout_position = int(body["workout_position"])
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.warning("Invalid request body: %s", str(e))
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid request body"})}

    logger.info(
        "request params request_id=%s user_id=%s workout_id=%s exercise_id=%s, position=%s",
        request_id, user_id, workout_id, exercise_id, workout_position
    )

    cache_key = f"session:{workout_id}:recommendation:{exercise_id}:{workout_position}"
    try:
        cached = get_cached_recommendation(workout_id, workout_position, exercise_id)
        if cached:
            logger.info("cache hit key=%s", cache_key)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(cached),
            }
        logger.warning("cache miss key=%s, computing live", cache_key)
    except Exception as e:
        logger.warning("Redis cache check failed, falling back to live: %s", str(e))


    try:
        result = recommendation_core(workout_id, workout_name, exercise_id, user_id)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result),
        }
    except Exception as e:
        logger.exception("recommendation failed request_id=%s: %s", request_id, str(e))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error", "detail": str(e)}),
        }