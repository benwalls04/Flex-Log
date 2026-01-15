import sqlite3
from fastapi import Depends, FastAPI
import os

DB_PATH = os.getenv("DATABASE_PATH", "/data/test_database.db")

def test_db():
  with sqlite3.connect(DB_PATH) as conn: 
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor() 
      cursor.execute("SELECT * FROM USERS")
      rows = cursor.fetchall()
      return [dict(row) for row in rows]
  
def get_exercise_features(exercise_name : str):
  with sqlite3.connect(DB_PATH) as conn: 
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM EXERCISES WHERE title = {exercise_name}")
    results = cursor.fetchall()
