import sqlite3
from fastapi import HTTPException
from pathlib import Path
from app.label_manager import LabelManager
import pandas as pd
import numpy as np
import joblib
import os

if "DATABASE_PATH" in os.environ:
    DB_PATH = Path(os.environ["DATABASE_PATH"])
else:
    DB_PATH = (
        Path(__file__).resolve()
        .parents[3]   
        / "data"
        / "test_database.db"
    )

def test_db():
  with sqlite3.connect(DB_PATH) as conn: 
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor() 
      cursor.execute("SELECT * FROM USERS")
      rows = cursor.fetchall()
      return [dict(row) for row in rows]
  
def encode_features(df, workout_name=None, column_mapping=None):
    for group in LabelManager.MUSCLE_GROUPS: 
        if "workout_name" in df.columns: 
            df[f"{group}_day"] = df["workout_name"].str.contains(group, case=False).astype(int)
        else: 
            df[f"{group}_day"] = int(group.lower() in workout_name.lower() if workout_name else False)
    
    if column_mapping is None:
        column_mapping = {
            "muscle_group": LabelManager.MUSCLE_GROUPS,
            "machine_type": LabelManager.MACHINE_LABELS,
            "exercise_type": LabelManager.TYPE_LABELS
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
    muscle_group_cols = [col for col in df.columns if col in [g.lower() for g in LabelManager.MUSCLE_GROUPS]]
    if muscle_group_cols:
        decoded_df['muscle_group'] = df[muscle_group_cols].idxmax(axis=1)
        decoded_df.drop(columns=muscle_group_cols, inplace=True)
    
    # Decode machine types
    machine_cols = [col for col in df.columns if col in [m.lower() for m in LabelManager.MACHINE_LABELS]]
    if machine_cols:
        decoded_df['machine_type'] = df[machine_cols].idxmax(axis=1)
        decoded_df.drop(columns=machine_cols, inplace=True)
    
    # Decode exercise types
    type_cols = [col for col in df.columns if col in [t.lower() for t in LabelManager.TYPE_LABELS]]
    if type_cols:
        decoded_df['exercise_type'] = df[type_cols].idxmax(axis=1)
        decoded_df.drop(columns=type_cols, inplace=True)
    
    # Remove workout day columns (e.g., chest_day, back_day, etc.)
    day_cols = [col for col in df.columns if col.endswith('_day')]
    if day_cols:
        decoded_df.drop(columns=day_cols, inplace=True)
    
    return decoded_df

def get_train_features(user_id: int): 
  print(DB_PATH)     
  with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            l.first,
            w.name as workout_name,
            e.muscle_group,
            e.machine_type, 
            e.exercise_type
        FROM logs l
        JOIN exercises e ON l.exercise_id = e.id
        JOIN workouts w ON l.workout_id = w.id
        WHERE l.user_id = ?
        GROUP BY l.exercise_id, l.workout_id
        ORDER BY l.timestamp ASC
    """, (user_id,))
    rows = cursor.fetchall()

    column_names = [
      "first", "workout_name", "muscle_group", "machine_type", "exercise_type"
    ]

    df = pd.DataFrame(rows, columns=column_names)

    df["workout_name"] = df["workout_name"].fillna("")
    df = encode_features(df)

    for col in LabelManager.EXERCISE_LABELS:
        df[f"target_{col}"] = df[col].copy()
        df[col] = df[col].shift(1).fillna(0).astype(int)
        df.loc[df["first"] == 1, col] = 0
    
    return df
  
def get_inference_features(exercise_id: int, workout_name: str):
   with sqlite3.connect(DB_PATH) as conn: 
      cursor = conn.cursor()
      cursor.execute("""
        SELECT   
          muscle_group, machine_type, exercise_type
        FROM exercises 
        WHERE id = ?
      """, (exercise_id, ))

      rows = cursor.fetchall()

      df = pd.DataFrame(rows, columns=["muscle_group", "machine_type", "exercise_type"])

      df = encode_features(df, workout_name=workout_name)

      missing_cols = [col for col in LabelManager.FEATURE_LABELS if col not in df.columns]
      if missing_cols:
          raise ValueError(f"Missing features in inference dataframe: {missing_cols}")

      return df
   
def get_top_N(user_id: int, pred_vector: np.array, workout_name : str, top_n: int):
    with sqlite3.connect(DB_PATH) as conn:
        groups = workout_name.split()
        conditions = " OR ".join(f"muscle_group = '{g}'" for g in groups)
        df = pd.read_sql(f"SELECT * FROM exercises WHERE {conditions};", conn)
    
    df_encoded = encode_features(df, workout_name=workout_name)

    X = df_encoded[LabelManager.EXERCISE_LABELS].astype(float).values
    pred_vector = np.array(pred_vector).reshape(1, -1)

    X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
    pred_norm = pred_vector / np.linalg.norm(pred_vector)
    similarity = (X_norm @ pred_norm.T).ravel()  # Shape: (n_exercises,)

    # Get exercise frequencies - vectorized
    with sqlite3.connect(DB_PATH) as conn: 
        cursor = conn.cursor()
        cursor.execute("""
            SELECT exercise_id, COUNT(*) as count FROM logs WHERE user_id = ? GROUP BY exercise_id
        """, (user_id, ))
        rows = cursor.fetchall()
        
        cursor.execute("""
            SELECT COUNT(*) FROM logs WHERE user_id = ?
        """, (user_id,))
        total_logs = cursor.fetchone()[0]
    
    # Build frequency vector aligned with df_encoded
    freq_vector = np.zeros(len(df_encoded))
    if total_logs > 0:
        freq_dict = {exercise_id: count / total_logs for exercise_id, count in rows}
        exercise_ids = df_encoded['id'].values  
        for i, ex_id in enumerate(exercise_ids):
            freq_vector[i] = freq_dict.get(ex_id, 0)
    
    # Vectorized weighted score calculation
    a = .5
    weighted_scores = a * similarity + (1 - a) * freq_vector
    
    top_idx = np.argsort(weighted_scores)[::-1][:top_n]
    
    topN_results = df_encoded.iloc[top_idx]
    decoded_results = decode_features(topN_results)
    return decoded_results

def load_model(path: Path):
  if not path.exists():
      raise HTTPException(status_code=404, detail=f"Model file does not exist: {path}")
  return joblib.load(path)

