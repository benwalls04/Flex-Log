from fastapi import FastAPI 
from pydantic import BaseModel
from app.helpers import test_db

app = FastAPI() 

@app.get("/health")
def root(): 
  return {"status": "ok"}

@app.get("/db_health")
def root(): 
  users = test_db()
  return users

class RecommendationParams(BaseModel):
  exercise_name: str
  num_reps: int
  workout_name: str 

@app.get("/")
def get_recommendation(RecommendationParams):
  num_reps = RecommendationParams.num_reps 
  workout_name = RecommendationParams.workout_name 
  exercise_name = RecommendationParams.exercise_name



