from fastapi import FastAPI, Depends
from pydantic import BaseModel
import subprocess
from pathlib import Path
import os
import numpy as np
from app.helpers import test_db, load_model_from_s3, get_inference_features, get_top_N
from app.label_manager import *
from app.auth import get_current_user

app = FastAPI() 

@app.get("/health")
def root(): 
  return {"status": "ok"}

@app.get("/db_health")
def root(): 
  users = test_db()
  return users

@app.get("/recommendation")
async def get_recommendation(
  workout_id: int,
  workout_name: str,
  exercise_id: int,
  user_id: str = Depends(get_current_user)
):
  """
  Get exercise recommendations for the authenticated user.
  User ID is automatically extracted from the JWT token.
  """

  return {"test" : "success"}
  # Load user-specific models from S3
  machine_model = load_model_from_s3("flexlog-models", f"user_{user_id}/machine.joblib")
  muscle_model = load_model_from_s3("flexlog-models", f"user_{user_id}/muscle.joblib")
  type_model = load_model_from_s3("flexlog-models", f"user_{user_id}/type.joblib")

  df = get_inference_features(exercise_id, workout_id, workout_name)
  X = df[FEATURE_LABELS].values

  muscle_probs = muscle_model.predict(X)
  machine_probs = machine_model.predict(X)
  type_probs = type_model.predict(X)
  
  try:
    muscle_label = MUSCLE_GROUPS[muscle_probs.argmax(axis=1)[0]]
    machine_label = MACHINE_LABELS[machine_probs.argmax(axis=1)[0]]
    type_label = TYPE_LABELS[type_probs.argmax(axis=1)[0]]
  except Exception as e: 
    return {"error": f"Models not found for user {user_id}. Train models first.", "detail": str(e)}

  pred_vector = np.concatenate([muscle_probs, machine_probs, type_probs], axis=1)

  top_recommendations = get_top_N(
    user_id=user_id,
    workout_id=workout_id, 
    workout_name=workout_name, 
    pred_vector=pred_vector,
    top_n=5
  )
  
  return {
    "top_muscle": muscle_label, 
    "top_machine": machine_label, 
    "top_type": type_label, 
    "recommendations": top_recommendations.to_dict(orient="records")
  }

@app.post("/train_model")
async def train(all_users: bool = True, user_id: int = None):
    pipeline_path = Path(__file__).parent / "pipeline.py"
    cmd = ["python3", str(pipeline_path)]

    if all_users:
        cmd.append("--all-users")
    elif user_id is not None:
        cmd.extend(["--user-id", str(user_id)])
    else:
        return {"error": "Specify either all_users=True or user_id"}

    # Run the pipeline as a subprocess
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Return stdout/stderr for debugging
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }

