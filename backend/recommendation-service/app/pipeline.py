
import argparse
import joblib
from pathlib import Path
from sklearn.linear_model import Ridge
from app.helpers import get_train_features, get_all_users, dump_model_to_s3, test_s3
from app.label_manager import *

def train(user_id):
  df = get_train_features(user_id)

  X = df[FEATURE_LABELS].values

  y_muscle = df[MUSCLE_GROUPS]
  y_machine = df[MACHINE_LABELS]
  y_type = df[TYPE_LABELS] 

  ridge_muscle  = Ridge(alpha=1.0).fit(X, y_muscle)
  ridge_machine = Ridge(alpha=1.0).fit(X, y_machine)
  ridge_type    = Ridge(alpha=1.0).fit(X, y_type)
  

if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  group = parser.add_mutually_exclusive_group(required=True)

  group.add_argument(
      "--all-users",
      action="store_true",
      help="Run pipeline for all users"
  )

  group.add_argument(
      "--user-id",
      type=int,
      help="Run pipeline for a single user"
  )

  args = parser.parse_args()
  test_s3

  # if args.all_users:
  #   user_ids = get_all_users()
  #   for u_id in user_ids: 
  #     train(user_id=u_id)

  # else:  
  #   train(user_id=args.user_id)