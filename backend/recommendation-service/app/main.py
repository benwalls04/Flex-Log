from fastapi import FastAPI, Depends
from pydantic import BaseModel
import subprocess
from pathlib import Path
import os
import numpy as np
from app.helpers import test_db, load_model_from_s3, get_inference_features, get_top_N
from app.label_manager import *
from app.auth import get_current_user
from app.dependencies import lifespan

app = FastAPI(lifespan=lifespan) 

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

@app.get("/recommendation/debug")
async def get_recommendation_debug(
  workout_id: int,
  workout_name: str,
  exercise_id: int,
  user_id: str = Depends(get_current_user)
):
  """
  Debug endpoint that returns the complete data transformation pipeline.
  Shows how raw parameters are transformed into one-hot encoded features.
  """
  
  # 1. Capture original input parameters
  original_params = {
    "workout_id": workout_id,
    "workout_name": workout_name,
    "exercise_id": exercise_id,
    "user_id": user_id
  }
  
  # 2. Get the exercise details before encoding
  from app.helpers import get_db_connection
  with get_db_connection() as conn:
    with conn.cursor() as cursor:
      cursor.execute("""
        SELECT id, name, variant, muscle_group, machine_type, exercise_type
        FROM exercises 
        WHERE id = %s
      """, (exercise_id,))
      row = cursor.fetchone()
      
      if not row:
        return {"error": f"Exercise {exercise_id} not found"}
      
      exercise_details = {
        "id": row[0],
        "name": row[1],
        "variant": row[2],
        "muscle_group": row[3],
        "machine_type": row[4],
        "exercise_type": row[5]
      }
  
  # 3. Get encoded features (this is what goes to the model)
  df = get_inference_features(exercise_id, workout_id, workout_name)
  encoded_features = df.to_dict(orient='records')[0]
  
  # 4. Extract just the feature vector in the correct order
  X = df[FEATURE_LABELS].values
  feature_vector = X[0].tolist()
  
  # 5. Create a mapping showing which features are "hot" (1) vs "cold" (0)
  feature_mapping = {}
  for i, label in enumerate(FEATURE_LABELS):
    feature_mapping[label] = {
      "value": feature_vector[i],
      "type": "binary" if feature_vector[i] in [0, 1] else "numeric"
    }
  
  # 6. Load models and get predictions
  try:
    machine_model = load_model_from_s3("flexlog-models", f"user_{user_id}/machine.joblib")
    muscle_model = load_model_from_s3("flexlog-models", f"user_{user_id}/muscle.joblib")
    type_model = load_model_from_s3("flexlog-models", f"user_{user_id}/type.joblib")
    
    muscle_probs = muscle_model.predict(X)
    machine_probs = machine_model.predict(X)
    type_probs = type_model.predict(X)
    
    # 7. Format predictions with labels
    predictions = {
      "muscle": {
        "probabilities": {MUSCLE_GROUPS[i]: float(muscle_probs[0][i]) for i in range(len(MUSCLE_GROUPS))},
        "top_prediction": MUSCLE_GROUPS[muscle_probs.argmax()],
        "top_probability": float(muscle_probs.max())
      },
      "machine": {
        "probabilities": {MACHINE_LABELS[i]: float(machine_probs[0][i]) for i in range(len(MACHINE_LABELS))},
        "top_prediction": MACHINE_LABELS[machine_probs.argmax()],
        "top_probability": float(machine_probs.max())
      },
      "type": {
        "probabilities": {TYPE_LABELS[i]: float(type_probs[0][i]) for i in range(len(TYPE_LABELS))},
        "top_prediction": TYPE_LABELS[type_probs.argmax()],
        "top_probability": float(type_probs.max())
      }
    }
  except Exception as e:
    predictions = {"error": f"Models not found for user {user_id}. Train models first.", "detail": str(e)}
  
  return {
    "step_1_input": original_params,
    "step_2_exercise_details": exercise_details,
    "step_3_encoded_features": encoded_features,
    "step_4_feature_vector": feature_vector,
    "step_5_feature_labels": FEATURE_LABELS,
    "step_6_feature_mapping": feature_mapping,
    "step_7_predictions": predictions
  }
