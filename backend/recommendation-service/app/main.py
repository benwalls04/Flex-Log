from fastapi import FastAPI 
from pydantic import BaseModel

app = FastAPI() 

@app.get("/health")
def root(): 
  return {"status": "ok"}

class RecommendationParams(BaseModel):
  exercise_name: str
  num_reps: int
  workout_name: str 

@app.get("/")
def get_recommendation(RecommendationParams):
  num_reps = RecommendationParams.num_reps 
  workout_name = RecommendationParams.workout_name 
  exercise_name = RecommendationParams.exercise_name



