MUSCLE_GROUPS = ["chest", "back", "legs", "shoulders", "biceps", "triceps"]
MACHINE_LABELS = ["barbell", "dumbbell", "machine", "cable", "smith", "misc"]
TYPE_LABELS = ["isolation", "compound"]
DAY_LABELS = [f"{group}_day" for group in MUSCLE_GROUPS]
PREV_LABELS = [f"num_prev_{group}" for group in MUSCLE_GROUPS]
OTHER_LABELS = ["position"]

EXERCISE_LABELS = MUSCLE_GROUPS + MACHINE_LABELS + TYPE_LABELS
FEATURE_LABELS = EXERCISE_LABELS + DAY_LABELS + PREV_LABELS + OTHER_LABELS