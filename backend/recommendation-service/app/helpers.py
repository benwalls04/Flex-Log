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
   
def get_top_N(pred_vector: np.array, workout_name : str, top_n: int):

  with sqlite3.connect(DB_PATH) as conn:
      groups = workout_name.split()
      conditions = " OR ".join(f"muscle_group = '{g}'" for g in groups)
      df = pd.read_sql(f"SELECT * FROM exercises WHERE {conditions};", conn)
  
  df_encoded = encode_features(df, workout_name=workout_name)

  X = df_encoded[LabelManager.EXERCISE_LABELS].astype(float).values
  pred_vector = np.array(pred_vector).reshape(1, -1)

  X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
  pred_norm = pred_vector / np.linalg.norm(pred_vector)
  similarity = X_norm @ pred_norm.T

  # Get top indices
  top_idx = np.argsort(similarity.ravel())[::-1][:top_n]
  return [(
            int(df.iloc[i]["id"]),
            df.iloc[i]["variant"],
            df.iloc[i]["name"],
          ) for i in top_idx]

def load_model(path: Path):
  if not path.exists():
      raise HTTPException(status_code=404, detail=f"Model file does not exist: {path}")
  return joblib.load(path)

