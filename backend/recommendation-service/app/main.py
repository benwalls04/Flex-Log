from fastapi import FastAPI 
from pydantic import BaseModel

app = FastAPI() 

@app.get("/health")
def root(): 
  return {"status": "ok"}

class RecommendationParams(BaseModel):
  exercise_title: str
  num_reps: int
  day_title: str 

@app.get("/")
def get_recommendation(RecommendationParams):
  num_reps = RecommendationParams.num_reps 
  day_title = RecommendationParams.day_title 
  exercise_title = RecommendationParams.exercise_title



