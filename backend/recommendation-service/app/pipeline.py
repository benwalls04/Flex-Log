
import argparse
import pandas as pd
from datetime import datetime
import joblib
from pathlib import Path
from sklearn.linear_model import Ridge
from app.helpers import get_train_features
from app.label_manager import *

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="")
  parser.add_argument("--user_id", type=int, required=True, help="user id to run the pipeline for")
  args = parser.parse_args()

  df = get_train_features(args.user_id)

  X = df[FEATURE_LABELS].values

  y_muscle = df[MUSCLE_GROUPS]
  y_machine = df[MACHINE_LABELS]
  y_type = df[TYPE_LABELS] 

  ridge_muscle  = Ridge(alpha=1.0).fit(X, y_muscle)
  ridge_machine = Ridge(alpha=1.0).fit(X, y_machine)
  ridge_type    = Ridge(alpha=1.0).fit(X, y_type)

  MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

  MODEL_DIR.mkdir(parents=True, exist_ok=True)

  joblib.dump(ridge_muscle,  MODEL_DIR / f"user_{args.user_id}_muscle.joblib")
  joblib.dump(ridge_machine, MODEL_DIR / f"user_{args.user_id}_machine.joblib")
  joblib.dump(ridge_type,    MODEL_DIR / f"user_{args.user_id}_type.joblib")
  