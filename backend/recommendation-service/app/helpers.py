import sqlite3
from fastapi import HTTPException
from pathlib import Path
import pandas as pd
import joblib
import os

LOCAL_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "test_database.db"
DB_PATH = os.getenv("DATABASE_PATH", LOCAL_DB_PATH)
print(f"using path {DB_PATH}")

MUSCLE_GROUPS = ["chest", "back", "legs", "shoulders", "biceps", "triceps"]
MACHINE_LABELS = ["barbell", "dumbbell", "machine", "cable", "smith", "misc_machine"]
TYPE_LABELS = ["isolation", "compound"]
EXERCISE_LABELS = MUSCLE_GROUPS + MACHINE_LABELS + TYPE_LABELS
FEATURE_LABELS = [f"prev_{col}" for col in EXERCISE_LABELS] + [f"{col}_day" for col in MUSCLE_GROUPS]

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
    
    return df
  
def get_inference_features(exercise_id: int, workout_name: str):
   with sqlite3.connect(DB_PATH) as conn: 
      cursor = conn.cursor()
      cursor.execute("""
        SELECT   
          e.chest, e.back, e.legs, e.sFhoulders, e.biceps, e.triceps, e.misc_group,
          e.barbell, e.dumbbell, e.machine, e.cable, e.smith, e.misc_machine,
          e.isolation, e.compound
        FROM exercises e
        WHERE e.id = ?
      """, (exercise_id, ))

      rows = cursor.fetchall()

      df = pd.DataFrame(rows, columns=EXERCISE_LABELS)
      df = df.add_prefix("prev_")

      for group in MUSCLE_GROUPS: 
        df[f"{group}_day"] = workout_name.str.contains(group, case=False).astype(int) 

      missing_cols = [col for col in FEATURE_LABELS if col not in df.columns]
      if missing_cols:
          raise ValueError(f"Missing features in inference dataframe: {missing_cols}")

      return df[FEATURE_LABELS].values

def load_model(path: Path):
  if not path.exists():
      raise HTTPException(status_code=404, detail=f"Model file does not exist: {path}")
  return joblib.load(path)

