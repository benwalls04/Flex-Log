import sqlite3
from fastapi import HTTPException
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import os

if "DATABASE_PATH" in os.environ:
    DB_PATH = Path(os.environ["DATABASE_PATH"])
else:
    DB_PATH = (
        Path(__file__).resolve()
        .parent.parent   # app/
        / "data"
        / "test_database.db"
    )


MUSCLE_GROUPS = ["chest", "back", "legs", "shoulders", "biceps", "triceps", "misc_group"]
DAY_LABELS = ["chest_day", "back_day", "legs_day", "shoulders_day", "biceps_day", "triceps_day"]
MACHINE_LABELS = ["barbell", "dumbbell", "machine", "cable", "smith", "misc_machine"]
TYPE_LABELS = ["isolation", "compound"]

EXERCISE_LABELS = MUSCLE_GROUPS + MACHINE_LABELS + TYPE_LABELS
FEATURE_LABELS = [f"prev_{col}" for col in EXERCISE_LABELS] + DAY_LABELS

def test_db():
  with sqlite3.connect(DB_PATH) as conn: 
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor() 
      cursor.execute("SELECT * FROM USERS")
      rows = cursor.fetchall()
      return [dict(row) for row in rows]

def get_train_features(user_id: int):
  with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            l.timestamp, l.first,
            w.name as workout_name,
            e.variant,
            e.machine_type,
            e.name as exercise_name,
            e.chest, e.back, e.legs, e.shoulders, e.biceps, e.triceps, e.misc_group,
            e.barbell, e.dumbbell, e.machine, e.cable, e.smith, e.misc_machine,
            e.isolation, e.compound
        FROM logs l
        JOIN exercises e ON l.exercise_id = e.id
        JOIN workouts w ON l.workout_id = w.id
        WHERE l.user_id = ?
        GROUP BY l.exercise_id, l.workout_id
        ORDER BY l.timestamp ASC
    """, (user_id,))
    rows = cursor.fetchall()

    column_names = [
        "timestamp", "first", "workout_name", 
        "variant", "machine_type", "exercise_name",
        "chest","back","legs","shoulders","biceps","triceps","misc_group",
        "barbell","dumbbell","machine","cable","smith","misc_machine",
        "isolation","compound"
      ]

    df = pd.DataFrame(rows, columns=column_names)

    df["workout_name"] = df["workout_name"].fillna("")

    for group in MUSCLE_GROUPS: 
      if group == "misc_group":
        continue
      df[f"{group}_day"] = df["workout_name"].str.contains(group, case=False).astype(int) 

    for col in EXERCISE_LABELS:
        df[f"prev_{col}"] = (
            df[col]
            .shift(1)
            .fillna(0)
            .astype(int)
        )

        df.loc[df["first"] == 1, f"prev_{col}"] = 0
    
    return df
  
def get_inference_features(exercise_id: int, workout_name: str):
   with sqlite3.connect(DB_PATH) as conn: 
      cursor = conn.cursor()
      cursor.execute("""
        SELECT   
          e.chest, e.back, e.legs, e.shoulders, e.biceps, e.triceps, e.misc_group,
          e.barbell, e.dumbbell, e.machine, e.cable, e.smith, e.misc_machine,
          e.isolation, e.compound
        FROM exercises e
        WHERE e.id = ?
      """, (exercise_id, ))

      rows = cursor.fetchall()

      df = pd.DataFrame(rows, columns=EXERCISE_LABELS)
      df = df.add_prefix("prev_")

      for group in MUSCLE_GROUPS: 
          if group == "misc_group":
            continue
          df[f"{group}_day"] = int(group.lower() in workout_name.lower() if workout_name else False)

      missing_cols = [col for col in FEATURE_LABELS if col not in df.columns]
      if missing_cols:
          raise ValueError(f"Missing features in inference dataframe: {missing_cols}")

      return df
   
def recommend_exercises(pred_vector: np.array, workout_name : str, top_n: int):
  print(pred_vector.shape)

  with sqlite3.connect(DB_PATH) as conn: 
    fields = workout_name.split() + ["misc_group"]
    conditions = " OR ".join(f"{f} = 1" for f in fields)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM exercises WHERE {conditions};")
    rows = np.array(cursor.fetchall())
    ids = rows[:,0]
    features = rows [:,4:].astype(float)

    pred_vector = np.array(pred_vector).reshape(1, -1)

    pred_norm = pred_vector / np.linalg.norm(pred_vector)
    features_norm = features / np.linalg.norm(features, axis=1, keepdims=True)
    similarity = features_norm @ pred_norm.T

    top_idx = np.argsort(similarity.ravel())[::-1][:top_n]
    top_rows = rows[top_idx,0:4]
    return [tuple(row) for row in top_rows]

  return t5_ids

def load_model(path: Path):
  if not path.exists():
      raise HTTPException(status_code=404, detail=f"Model file does not exist: {path}")
  return joblib.load(path)

