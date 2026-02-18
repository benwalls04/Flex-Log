"""
Recommendation Lambda: single-file handler.
Connections: DB and Redis from Secrets Manager; S3 via Lambda IAM role.

Env: DB_SECRET_NAME (or SECRET_NAME) = secret with DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.
     Optional REDIS_SECRET_NAME = secret with REDIS_HOST, REDIS_PORT, REDIS_PASSWORD.
     If unset, Redis config is read from the DB secret (one secret can hold both).
"""
import os
import json
import tempfile
from pathlib import Path

import boto3
import joblib
import numpy as np
import pandas as pd
import psycopg2
import redis

# --- Connection state (filled from Secrets Manager on first use) ---
_db_secret = None
_redis_secret = None
_redis_client = None


def _get_db_secret():
    """Load DB config from Secrets Manager. Cached per Lambda container."""
    global _db_secret
    if _db_secret is not None:
        return _db_secret
    name = os.environ.get("DB_SECRET_NAME") or os.environ.get("DB_SECRET_NAME", "dev/supabase")
    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("secretsmanager", region_name=region)
    _db_secret = json.loads(client.get_secret_value(SecretId=name)["SecretString"])
    return _db_secret


def _get_redis_secret():
    """Load Redis config from Secrets Manager. Uses REDIS_SECRET_NAME if set, else DB secret."""
    global _redis_secret
    if _redis_secret is not None:
        return _redis_secret
    name =  os.environ.get("REDIS_SECRET_NAME") or os.environ.get("REDIS_SECRET_NAME", "dev/Redis")

    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("secretsmanager", region_name=region)
    _redis_secret = json.loads(client.get_secret_value(SecretId=name)["SecretString"])
    
    return _redis_secret


def get_db_connection():
    """Return a new DB connection. Caller must call release_db_connection(conn) when done."""
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


def release_db_connection(conn):
    """Release a DB connection (close it)."""
    if conn:
        try:
            conn.close()
        except Exception:
            pass


def get_redis_client():
    """Return a Redis client. Cached per Lambda container."""
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

def get_inference_features(exercise_id: int, workout_id : int, workout_name: str):
    """Get features for inference/prediction"""
    conn = get_db_connection()
    try:
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
    finally:
        release_db_connection(conn)
   
def get_top_N(user_id, pred_vector: np.array, workout_name : str, workout_id : int, top_n: int):
    """Get top N exercise recommendations based on model predictions"""
    done_exercises = get_session_exercises(workout_id)

    conn = get_db_connection()
    try:
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
    finally:
        release_db_connection(conn)
    
    df_encoded = encode_features(df, workout_name=workout_name)

    X = df_encoded[EXERCISE_LABELS].astype(float).values
    pred_vector = np.array(pred_vector).reshape(1, -1)

    X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-8)
    pred_norm = pred_vector / (np.linalg.norm(pred_vector) + 1e-8) 
    similarity = (X_norm @ pred_norm.T).ravel() 

    # Get exercise frequencies - vectorized
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT exercise_id, COUNT(*) as count FROM logs WHERE user_id = %s GROUP BY exercise_id
            """, (user_id, ))
            rows = cursor.fetchall()
            
            cursor.execute("""
                SELECT COUNT(*) FROM logs WHERE user_id = %s
            """, (user_id,))
            total_logs = cursor.fetchone()[0]
    finally:
        release_db_connection(conn)
    
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

    top_exercise_id = int(df_encoded.iloc[top_idx[0]]["id"])

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
    """Core recommendation logic. Called by handler after parsing event."""
    machine_model = load_model_from_s3("flexlog-models", f"user_{user_id}/machine.joblib")
    muscle_model = load_model_from_s3("flexlog-models", f"user_{user_id}/muscle.joblib")
    type_model = load_model_from_s3("flexlog-models", f"user_{user_id}/type.joblib")

    df = get_inference_features(exercise_id, workout_id, workout_name)
    X = df[FEATURE_LABELS].values

    muscle_probs = muscle_model.predict(X)
    machine_probs = machine_model.predict(X)
    type_probs = type_model.predict(X)

    try:
        muscle_label = MUSCLE_GROUPS[muscle_probs.argmax(axis=1)[0]]
        machine_label = MACHINE_LABELS[machine_probs.argmax(axis=1)[0]]
        type_label = TYPE_LABELS[type_probs.argmax(axis=1)[0]]
    except Exception as e:
        return {"error": f"Models not found for user {user_id}. Train models first.", "detail": str(e)}

    pred_vector = np.concatenate([muscle_probs, machine_probs, type_probs], axis=1)

    top_recommendations = get_top_N(
        user_id=user_id,
        workout_id=workout_id,
        workout_name=workout_name,
        pred_vector=pred_vector,
        top_n=5,
    )

    return {
        "top_muscle": muscle_label,
        "top_machine": machine_label,
        "top_type": type_label,
        "recommendations": top_recommendations.to_dict(orient="records"),
    }


def handler(event, context):
    # Lambda authorizer (HTTP API v2) passes context as requestContext.authorizer.<key>
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    user_id = authorizer.get("user_id")

    if not user_id:
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Unauthorized"}),
        }

    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)
    workout_id = int(body["workout_id"])
    workout_name = body["workout_name"]
    exercise_id = int(body["exercise_id"])
    result = recommendation_core(workout_id, workout_name, exercise_id, user_id)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result),
    }