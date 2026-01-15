import sqlite3
from fastapi import Depends, FastAPI

DB_PATH = "/app/db/flexlog"

def get_exercise_features(exercise_name : str):
  with sqlite3.connect(DB_PATH) as conn: 
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM EXERCISES WHERE title = {exercise_name}")
    results = cursor.fetchall()
