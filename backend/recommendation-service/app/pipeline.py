
import argparse
import pandas as pd
import joblib
from pathlib import Path
from sklearn.linear_model import Ridge
from app.helpers import get_train_features, FEATURE_LABELS, MUSCLE_GROUPS, MACHINE_LABELS, TYPE_LABELS, EXERCISE_LABELS

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="")
  parser.add_argument("--user_id", type=int, required=True, help="user id to run the pipeline for")
  args = parser.parse_args()

  df = get_train_features(args.user_id)

  df["workout_name"] = df["workout_name"].fillna("")

  for group in MUSCLE_GROUPS: 
    df[f"{group}_day"] = df["workout_name"].str.contains(group, case=False).astype(int) 

  for col in EXERCISE_LABELS:
      df[f"prev_{col}"] = (
          df[col]
          .shift(1)
          .fillna(0)
          .astype(int)
      )

      df.loc[df["first"] == 1, f"prev_{col}"] = 0

  X = df[FEATURE_LABELS].values

  y_muscle = df[MUSCLE_GROUPS]
  y_machine = df[MACHINE_GROUPS]
  y_type = df[TYPE_GROUPS] 

  ridge_muscle  = Ridge(alpha=1.0).fit(X, y_muscle)
  ridge_machine = Ridge(alpha=1.0).fit(X, y_machine)
  ridge_type    = Ridge(alpha=1.0).fit(X, y_type)

  MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

  MODEL_DIR.mkdir(parents=True, exist_ok=True)

  joblib.dump(ridge_muscle,  MODEL_DIR / f"user_{args.user_id}_muscle.joblib")
  joblib.dump(ridge_machine, MODEL_DIR / f"user_{args.user_id}_machine.joblib")
  joblib.dump(ridge_type,    MODEL_DIR / f"user_{args.user_id}_type.joblib")
  