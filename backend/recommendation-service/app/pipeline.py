
import argparse
import pandas as pd
import joblib
from pathlib import Path
from sklearn.linear_model import Ridge
from app.helpers import get_input_features   


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="")
  parser.add_argument("--user_id", type=int, required=True, help="user id to run the pipeline for")
  args = parser.parse_args()

  rows = get_input_features(args.user_id)

  column_names = [
      "timestamp", "first", "workout_name", 
      "variant", "machine_type", "exercise_name",
      "chest","back","legs","shoulders","biceps","triceps","misc_group",
      "barbell","dumbbell","machine","cable","smith","misc_machine",
      "isolation","compound"
  ]

  df = pd.DataFrame(rows, columns=column_names)

  df["exercise_name"] = df["variant"] + " " +  df["machine_type"] + " " + df["exercise_name"]

  muscle_groups = ["chest", "back", "legs", "shoulders", "biceps", "triceps"]

  for group in muscle_groups: 
    df[f"{group}_day"] = df["workout_name"].str.contains(group, case=False).astype(int) 

  lagged_cols = ["barbell", "dumbbell", "machine", "cable", "smith", "misc_machine", "misc_group", "isolation", "compound", "chest", "back", "legs", "shoulders", "biceps", "triceps"]

  for col in lagged_cols:
      df[f"prev_{col}"] = (
          df[col]
          .shift(1)
          .fillna(0)
          .astype(int)
  )

  df.loc[df["first"] == 1, f"prev_{col}"] = 0

  feature_cols = [col for col in df.columns if col.startswith("prev_") or "day" in col]

  X = df[feature_cols].values
  y_muscle = df[["chest", "back", "legs", "shoulders", "biceps", "triceps", "misc_group"]]
  y_machine = df[["barbell", "dumbbell", "machine", "cable", "smith", "misc_machine"]]
  y_type = df[["isolation", "compound"]] 

  ridge_muscle  = Ridge(alpha=1.0).fit(X, y_muscle)
  ridge_machine = Ridge(alpha=1.0).fit(X, y_machine)
  ridge_type    = Ridge(alpha=1.0).fit(X, y_type)

  MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

  MODEL_DIR.mkdir(parents=True, exist_ok=True)

  joblib.dump(ridge_muscle,  MODEL_DIR / f"user_{args.user_id}_muscle.joblib")
  joblib.dump(ridge_machine, MODEL_DIR / f"user_{args.user_id}_machine.joblib")
  joblib.dump(ridge_type,    MODEL_DIR / f"user_{args.user_id}_type.joblib")