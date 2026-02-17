import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException
from pathlib import Path
from app.label_manager import *
from app.sessions import get_session_exercises, add_exercise_to_session, get_muscle_group_counts, get_session_position
import pandas as pd
import numpy as np
import joblib
import os
import tempfile

def get_db_connection():
    """
    Get a database connection from the pool.
    IMPORTANT: Must call release_db_connection() when done!
    """
    from app.dependencies import get_db_connection as get_pool_connection
    return get_pool_connection()

def release_db_connection(conn):
    """Return a database connection to the pool"""
    from app.dependencies import release_db_connection as release_conn
    release_conn(conn)

def test_db():
    """Test database connectivity"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        release_db_connection(conn)
  
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

def get_train_features(user_id):
    """Get training features for a user (Note: This is not used in recommendation-service)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    l.first, l.timestamp, 
                    w.name as workout_name,
                    e.muscle_group,
                    e.machine_type, 
                    e.exercise_type
                FROM logs l
                JOIN exercises e ON l.exercise_id = e.id
                JOIN workouts w ON l.workout_id = w.id
                WHERE l.user_id = %s
                GROUP BY l.exercise_id, l.workout_id, l.first, l.timestamp, w.name, e.muscle_group, e.machine_type, e.exercise_type
                ORDER BY l.timestamp ASC
            """, (user_id,))
            rows = cursor.fetchall()

            column_names = [
                "first", "timestamp", "workout_name", "muscle_group", "machine_type", "exercise_type"
            ]

            df = pd.DataFrame(rows, columns=column_names)

            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["day"] = df['timestamp'].dt.day
            df["workout_name"] = df["workout_name"].fillna("")

            group_counts = {key : 0 for key in MUSCLE_GROUPS}
            for group in MUSCLE_GROUPS:
                df[f"num_prev_{group}"] = 0

            df['position'] = 0
            position = 0
            for idx, row in df.iterrows(): 
                if row["first"] == 1: 
                    for k in group_counts.keys():
                        group_counts[k] = 0
                    position = 0

                df.loc[idx, "position"] = position
                for group, v in group_counts.items(): 
                    df.loc[idx, f"num_prev_{group}"] = v
                
                position += 1
                group_counts[row["muscle_group"]] += 1

            df = encode_features(df)

            for col in EXERCISE_LABELS:
                df[f"target_{col}"] = df[col].copy()
                df[col] = df[col].shift(1).fillna(0).astype(int)
                df.loc[df["first"] == 1, col] = 0
            
            return df
    finally:
        release_db_connection(conn)
  
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

def get_all_users() -> list:
    """Get all user IDs from the database"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users")
            return [row[0] for row in cursor.fetchall()]
    finally:
        release_db_connection(conn)
    
def load_model(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Model file does not exist: {path}")
    return joblib.load(path)


def dump_model_to_s3(model, bucket, key):
    """Upload a model to S3 using the shared S3 client"""
    from app.dependencies import get_s3_client
    s3 = get_s3_client()
    
    # Use delete=False to prevent auto-deletion on Windows
    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Now we can write to the file after closing it
        joblib.dump(model, tmp_path)
        s3.upload_file(tmp_path, bucket, key)
    finally:
        # Clean up manually
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def load_model_from_s3(bucket, key):
    """Download and load a model from S3 using the shared S3 client"""
    from app.dependencies import get_s3_client
    s3 = get_s3_client()
    
    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        s3.download_file(bucket, key, tmp_path)
        return joblib.load(tmp_path)
    finally:
        # Clean up manually
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    