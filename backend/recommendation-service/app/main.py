from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import os
import numpy as np
from app.helpers import test_db, load_model, get_inference_features, get_top_N
from app.label_manager import LabelManager

app = FastAPI() 

@app.get("/health")
def root(): 
  return {"status": "ok"}

@app.get("/db_health")
def root(): 
  users = test_db()
  return users

@app.get("/")
def get_recommendation(exercise_id: int, workout_name: str, user_id: int):

  if "MODEL_PATH" in os.environ:
    MODEL_DIR = Path(os.environ["MODEL_PATH"])
  else:
    MODEL_DIR = Path(__file__).parents[2] / "models"

  machine_path = MODEL_DIR / f"user_{user_id}_machine.joblib"
  muscle_path = MODEL_DIR / f"user_{user_id}_muscle.joblib"
  type_path = MODEL_DIR / f"user_{user_id}_type.joblib"

  machine_model = load_model(machine_path)
  muscle_model = load_model(muscle_path)
  type_model = load_model(type_path)

  df = get_inference_features(exercise_id, workout_name)
  X = df[LabelManager.FEATURE_LABELS].values

  muscle_probs = muscle_model.predict(X)
  machine_probs = machine_model.predict(X)
  type_probs = type_model.predict(X)
  
  muscle_label = LabelManager.MUSCLE_GROUPS[muscle_probs.argmax(axis=1)[0]]
  machine_label = LabelManager.MACHINE_LABELS[machine_probs.argmax(axis=1)[0]]
  type_label = LabelManager.TYPE_LABELS[type_probs.argmax(axis=1)[0]]

  pred_vector = np.concatenate([muscle_probs, machine_probs, type_probs], axis=1)

  top_recommendations = get_top_N(pred_vector, workout_name, 5)
  
  return {
    "top_muslce": muscle_label, 
    "top_machine": machine_label, 
    "top_type": type_label, 
    "recommendations": top_recommendations
  }



