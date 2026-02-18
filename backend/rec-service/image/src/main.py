import os
import json
import tempfile
import boto3
import joblib
import numpy as np
import pandas as pd
import psycopg2
import redis
import logging

_db_secret = None
_redis_secret = None
_redis_client = None

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _get_db_secret():
    global _db_secret
    if _db_secret is not None:
        return _db_secret
    name = os.environ.get("DB_SECRET_NAME", "dev/supabase")
    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("secretsmanager", region_name=region)
    _db_secret = json.loads(client.get_secret_value(SecretId=name)["SecretString"])
    return _db_secret


def _get_redis_secret():
    global _redis_secret
    if _redis_secret is not None:
        return _redis_secret
    name = os.environ.get("REDIS_SECRET_NAME", "dev/Redis")

    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("secretsmanager", region_name=region)
    _redis_secret = json.loads(client.get_secret_value(SecretId=name)["SecretString"])
    
    return _redis_secret


def get_db_connection():
    s = _get_db_secret()
    return psycopg2.connect(
        host=s["DB_HOST"],
        port=int(s.get("DB_PORT", 6543)),
        dbname=s.get("DB_NAME", "postgres"),
        user=s["DB_USER"],
        password=s["DB_PASSWORD"],
        sslmode="require",
        connect_timeout=15,
    )

def get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    s = _get_redis_secret()
    _redis_client = redis.Redis(
        host=s["REDIS_HOST"],
        port=int(s.get("REDIS_PORT", 6379)),
        password=s.get("REDIS_PASSWORD", ""),
        decode_responses=True,
        socket_connect_timeout=5,
    )
    return _redis_client


def get_s3_client():
    return boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))


# --- Labels and feature config ---
MUSCLE_GROUPS = ["chest", "back", "legs", "shoulders", "biceps", "triceps"]
MACHINE_LABELS = ["barbell", "dumbbell", "machine", "cable", "smith", "misc"]
TYPE_LABELS = ["isolation", "compound"]
DAY_LABELS = [f"{group}_day" for group in MUSCLE_GROUPS]
PREV_LABELS = [f"num_prev_{group}" for group in MUSCLE_GROUPS]
OTHER_LABELS = ["position"]

EXERCISE_LABELS = MUSCLE_GROUPS + MACHINE_LABELS + TYPE_LABELS
FEATURE_LABELS = EXERCISE_LABELS + DAY_LABELS + PREV_LABELS + OTHER_LABELS


def get_session_exercises(workout_id: int) -> set:
    redis_client = get_redis_client()
    key = f"session:{workout_id}:exercises"
    exercises = redis_client.smembers(key)
    return {int(ex_id) for ex_id in exercises} if exercises else set()

def get_muscle_group_counts(workout_id: int):
    redis_client = get_redis_client()
    key = f"session:{workout_id}:muscle_counts"
    raw_hash = redis_client.hgetall(key) or {}
    return {k: int(v) for k, v in raw_hash.items()}

def get_session_position(workout_id: int):
    redis_client = get_redis_client()
    key = f"session:{workout_id}:count"
    count = redis_client.get(key)
    return int(count) if count else 0
  
def encode_features(df, workout_name=None, column_mapping=None):
    for group in MUSCLE_GROUPS: 
        if "workout_name" in df.columns: 
            df[f"{group}_day"] = df["workout_name"].str.contains(group, case=False).astype(int)
        else: 
            df[f"{group}_day"] = int(group.lower() in workout_name.lower() if workout_name else False)
    
    if column_mapping is None:
        column_mapping = {
            "muscle_group": MUSCLE_GROUPS,
            "machine_type": MACHINE_LABELS,
            "exercise_type": TYPE_LABELS
        }

    for col, categories in column_mapping.items():
        if col not in df.columns:
            continue
        df[col] = df[col].str.lower()
        categories_lower = [c.lower() for c in categories]
        for cat in categories_lower:
            df[cat] = (df[col] == cat).astype(int)
        df.drop(columns=[col], inplace=True)
    
    return df

def decode_features(df):
    decoded_df = df.copy()
    
    # Decode muscle groups
    muscle_group_cols = [col for col in df.columns if col in [g.lower() for g in MUSCLE_GROUPS]]
    if muscle_group_cols:
        decoded_df['muscle_group'] = df[muscle_group_cols].idxmax(axis=1)
        decoded_df.drop(columns=muscle_group_cols, inplace=True)
    
    # Decode machine types
    machine_cols = [col for col in df.columns if col in [m.lower() for m in MACHINE_LABELS]]
    if machine_cols:
        decoded_df['machine_type'] = df[machine_cols].idxmax(axis=1)
        decoded_df.drop(columns=machine_cols, inplace=True)
        
    # Decode exercise types
    type_cols = [col for col in df.columns if col in [t.lower() for t in TYPE_LABELS]]
    if type_cols:
        decoded_df['exercise_type'] = df[type_cols].idxmax(axis=1)
        decoded_df.drop(columns=type_cols, inplace=True)
    
    # Remove workout day columns (e.g., chest_day, back_day, etc.)
    day_cols = [col for col in df.columns if col.endswith('_day')]
    if day_cols:
        decoded_df.drop(columns=day_cols, inplace=True)        

    return decoded_df

def get_inference_features(exercise_id: int, workout_id : int, workout_name: str, conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT   
            muscle_group, machine_type, exercise_type
            FROM exercises 
            WHERE id = %s
        """, (exercise_id, ))

        rows = cursor.fetchall()

        if not rows:
            raise ValueError(f"Exercise {exercise_id} not found in database")

        df = pd.DataFrame(rows, columns=["muscle_group", "machine_type", "exercise_type"])

        df = encode_features(df, workout_name=workout_name)

        group_counts = get_muscle_group_counts(workout_id)
        for group in MUSCLE_GROUPS:
            if group in group_counts: 
                df[f"num_prev_{group}"] = group_counts[group]
            else: 
                df[f"num_prev_{group}"] = 0 

        df["position"] = get_session_position(workout_id)

        missing_cols = [col for col in FEATURE_LABELS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing features in inference dataframe: {missing_cols}")

        return df 

def get_top_N(user_id, pred_vector: np.array, workout_name : str, workout_id : int, top_n: int, conn):
    done_exercises = get_session_exercises(workout_id)

    groups = workout_name.split()
    conditions = " OR ".join(f"muscle_group = %s" for g in groups)
    
    if done_exercises:
        exclude_placeholders = ','.join(['%s'] * len(done_exercises))
        query = f"SELECT * FROM exercises WHERE ({conditions}) AND id NOT IN ({exclude_placeholders})"
        params = groups + list(done_exercises)
    else:
        query = f"SELECT * FROM exercises WHERE ({conditions})"
        params = groups

    df = pd.read_sql(query, conn, params=params)

    df_encoded = encode_features(df, workout_name=workout_name)

    X = df_encoded[EXERCISE_LABELS].astype(float).values
    pred_vector = np.array(pred_vector).reshape(1, -1)

    X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-8)
    pred_norm = pred_vector / (np.linalg.norm(pred_vector) + 1e-8) 
    similarity = (X_norm @ pred_norm.T).ravel() 

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT exercise_id, COUNT(*) as count FROM logs WHERE user_id = %s GROUP BY exercise_id
        """, (user_id, ))
        rows = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) FROM logs WHERE user_id = %s
        """, (user_id,))
        total_logs = cursor.fetchone()[0]
    
    # Build frequency vector aligned with df_encoded
    freq_vector = np.zeros(len(df_encoded))
    if total_logs > 0:
        freq_dict = {exercise_id: count / total_logs for exercise_id, count in rows}
        exercise_ids = df_encoded['id'].values  
        for i, ex_id in enumerate(exercise_ids):
            freq_vector[i] = freq_dict.get(ex_id, 0)
    
    a = .5
    weighted_scores = a * similarity + (1 - a) * freq_vector
    
    top_idx = np.argsort(weighted_scores)[::-1][:top_n]
    
    topN_results = df_encoded.iloc[top_idx]
    decoded_results = decode_features(topN_results)

    return decoded_results


def load_model_from_s3(bucket, key):
    s3 = get_s3_client()
    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        s3.download_file(bucket, key, tmp_path)
        return joblib.load(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
def recommendation_core(workout_id: int, workout_name: str, exercise_id: int, user_id: str) -> dict:
    logger.info(
        "recommendation_core start user_id=%s workout_id=%s exercise_id=%s",
        user_id, workout_id, exercise_id,
    )
    conn = get_db_connection()
    try:
        machine_model = load_model_from_s3("flexlog-models", f"user_{user_id}/machine.joblib")
        muscle_model = load_model_from_s3("flexlog-models", f"user_{user_id}/muscle.joblib")
        type_model = load_model_from_s3("flexlog-models", f"user_{user_id}/type.joblib")
        
        df = get_inference_features(exercise_id, workout_id, workout_name, conn)

        logger.info("Inference features shape: %s", df.shape if df is not None else None)
        X = df[FEATURE_LABELS].values

        muscle_probs = muscle_model.predict(X)
        machine_probs = machine_model.predict(X)
        type_probs = type_model.predict(X)

        muscle_label = MUSCLE_GROUPS[muscle_probs.argmax(axis=1)[0]]
        machine_label = MACHINE_LABELS[machine_probs.argmax(axis=1)[0]]
        type_label = TYPE_LABELS[type_probs.argmax(axis=1)[0]]

        pred_vector = np.concatenate([muscle_probs, machine_probs, type_probs], axis=1)

        top_recommendations = get_top_N(
            user_id=user_id,
            workout_id=workout_id,
            workout_name=workout_name,
            pred_vector=pred_vector,
            top_n=5,
            conn=conn,
        )

        logger.info("Top N count: %s", len(top_recommendations) if top_recommendations is not None else 0)

        return {
            "top_muscle": muscle_label,
            "top_machine": machine_label,
            "top_type": type_label,
            "recommendations": top_recommendations.to_dict(orient="records"),
        }
    finally:
        if conn: 
            conn.close()
        logger.info("recommendation_core done user_id=%s", user_id)


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
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.warning("Invalid request body: %s", str(e))
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid request body"})}

    logger.info(
        "request params request_id=%s user_id=%s workout_id=%s exercise_id=%s",
        request_id, user_id, workout_id, exercise_id,
    )

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