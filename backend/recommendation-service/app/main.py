from fastapi import FastAPI
from pydantic import BaseModel
import joblib
from pathlib import Path
from app.helpers import test_db, load_model, get_inference_features, MUSCLE_GROUPS, MACHINE_GROUPS, TYPE_GROUPS

app = FastAPI() 

@app.get("/health")
def root(): 
  return {"status": "ok"}

@app.get("/db_health")
def root(): 
  users = test_db()
  return users

class RecommendationParams(BaseModel):
  exercise_id: int
  workout_name: str 
  user_id: int

@app.get("/")
def get_recommendation(RecommendationParams):
  user_id = RecommendationParams.user_id
  workout_name = RecommendationParams.workout_name 
  exercise_id = RecommendationParams.exercise_id
  MODEL_DIR = Path(__file__).parents[2] / "models"
  
  machine_path = MODEL_DIR / f"user_{user_id}_machine.joblib"
  muscle_path = MODEL_DIR / f"user_{user_id}_muscle.joblib"
  type_path = MODEL_DIR / f"user_{user_id}_type.joblib"

  machine_model = load_model(machine_path)
  muscle_model = load_model(muscle_path)
  type_model = load_model(type_path)

  X  = get_inference_features(exercise_id, workout_name)

  muscle_pred = muscle_model.predict(X).argmax(axis=1)[0]
  machine_pred = machine_model.predict(X).argmax(axis=1)[0]
  type_pred = type_model.predict(X).argmax(axis=1)[0]

  muscle_label = MUSCLE_GROUPS[muscle_pred]
  machine_label = MACHINE_GROUPS[machine_pred]
  type_label = TYPE_GROUPS[type_pred]

  return {""
  ""
  ""}




