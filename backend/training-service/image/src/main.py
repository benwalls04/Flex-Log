import json
import boto3
import joblib
import tempfile 
import os
from io import BytesIO
from sklearn.linear_model import Ridge 
import numpy as np
import psycopg2
import pandas as pd

MUSCLE_GROUPS = ["chest", "back", "legs", "shoulders", "biceps", "triceps"]
MACHINE_LABELS = ["barbell", "dumbbell", "machine", "cable", "smith", "misc"]
TYPE_LABELS = ["isolation", "compound"]
DAY_LABELS = [f"{group}_day" for group in MUSCLE_GROUPS]
PREV_LABELS = [f"num_prev_{group}" for group in MUSCLE_GROUPS]
OTHER_LABELS = ["position"]

EXERCISE_LABELS = MUSCLE_GROUPS + MACHINE_LABELS + TYPE_LABELS
FEATURE_LABELS = EXERCISE_LABELS + DAY_LABELS + PREV_LABELS + OTHER_LABELS

secrets_client = None
s3_client = None
supabase_secret = None
DB_CONFIG = None

def get_clients():
    global secrets_client, s3_client, supabase_secret, DB_CONFIG
    
    if secrets_client is None:
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
        secret_name = os.environ.get('SECRET_NAME', 'dev/supabase')
 
        session = boto3.session.Session(region_name=region_name)
        secrets_client = session.client(service_name='secretsmanager')
        s3_client = session.client(service_name='s3')
        
        secret_response = secrets_client.get_secret_value(SecretId=secret_name)
        supabase_secret = json.loads(secret_response['SecretString'])
    
    if DB_CONFIG is None:
        DB_CONFIG = {
            "host": supabase_secret["DB_HOST"], 
            "port": int(supabase_secret.get("DB_PORT", 6543)), 
            "database": supabase_secret.get("DB_NAME", "postgres"), 
            "user": supabase_secret["DB_USER"],
            "password": supabase_secret["DB_PASSWORD"],
            "sslmode": "require",
            "connect_timeout": 15
        }
    
    return secrets_client, s3_client, DB_CONFIG

def dump_model_to_s3(model, bucket, key):
    buffer = BytesIO()
    joblib.dump(model, buffer)
    buffer.seek(0)  
    
    s3_client.upload_fileobj(
        Fileobj=buffer,
        Bucket=bucket,
        Key=key
    )
    print(f"Model uploaded to s3://{bucket}/{key}")


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_all_users() -> list:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM auth.users")
            return [row[0] for row in cursor.fetchall()]

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

def get_train_features(user_id): 
    with get_db_connection() as conn:
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

def train(user_id):
    try:
        print(f"Training models for user {user_id}")
        df = get_train_features(user_id)

        if df.empty:
            print(f"No training data for user {user_id}, skipping...")
            return {"user_id": user_id, "status": "skipped", "reason": "no_data"}
        
        X = df[FEATURE_LABELS].values

        y_muscle = df[[f"target_{mg}" for mg in MUSCLE_GROUPS]]
        y_machine = df[[f"target_{mt}" for mt in MACHINE_LABELS]]
        y_type = df[[f"target_{t}" for t in TYPE_LABELS]]

        ridge_muscle  = Ridge(alpha=1.0).fit(X, y_muscle)
        ridge_machine = Ridge(alpha=1.0).fit(X, y_machine)
        ridge_type    = Ridge(alpha=1.0).fit(X, y_type)

        dump_model_to_s3(ridge_muscle, "flexlog-models", f"user_{user_id}/muscle.joblib")
        dump_model_to_s3(ridge_machine, "flexlog-models", f"user_{user_id}/machine.joblib")
        dump_model_to_s3(ridge_type, "flexlog-models", f"user_{user_id}/type.joblib")
        
        print(f"Successfully trained models for user {user_id}")
        return {"user_id": user_id, "status": "success"}
    except Exception as e:
        print(f"Error training user {user_id}: {str(e)}")
        return {"user_id": user_id, "status": "error", "error": str(e)}


def handler(event, context):
    get_clients()
    if event.get('user_id') is not None:
        train(event['user_id'])
    else: 
        for uId in get_all_users():
            train(uId)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
