class LabelManager:
    MUSCLE_GROUPS = ["chest", "back", "legs", "shoulders", "biceps", "triceps"]
    MACHINE_LABELS = ["barbell", "dumbbell", "machine", "cable", "smith", "misc"]
    TYPE_LABELS = ["isolation", "compound"]

    DAY_LABELS = ["chest_day", "back_day", "legs_day", "shoulders_day", "biceps_day", "triceps_day"]
    EXERCISE_LABELS = MUSCLE_GROUPS + MACHINE_LABELS + TYPE_LABELS
    FEATURE_LABELS = EXERCISE_LABELS + DAY_LABELS

    @classmethod
    def get_muscle_label(cls, idx):
        return cls.MUSCLE_GROUPS[idx]

    @classmethod
    def get_machine_label(cls, idx):
        return cls.MACHINE_LABELS[idx]

    @classmethod
    def get_type_label(cls, idx):
        return cls.TYPE_LABELS[idx]

    @classmethod
    def get_feature_label(cls, idx):
        return cls.FEATURE_LABELS[idx]

    @classmethod
    def get_exercise_label(cls, idx):
        return cls.EXERCISE_LABELS[idx]
