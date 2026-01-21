import sqlite3
from fastapi import Depends, FastAPI
from pathlib import Path
import os

LOCAL_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "test_database.db"
DB_PATH = os.getenv("DATABASE_PATH", LOCAL_DB_PATH)
print(f"using path {DB_PATH}")

def test_db():
  with sqlite3.connect(DB_PATH) as conn: 
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor() 
      cursor.execute("SELECT * FROM USERS")
      rows = cursor.fetchall()
      return [dict(row) for row in rows]

def get_input_features(user_id: int):
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
    return rows

 