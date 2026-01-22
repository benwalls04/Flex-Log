import sqlite3

conn = sqlite3.connect("./data/test_database.db")
cursor = conn.cursor()

# Enable foreign key support
cursor.execute("PRAGMA foreign_keys = ON;")

cursor.execute("DROP TABLE favorites;")
cursor.execute("DROP TABLE logs;")
cursor.execute("DROP TABLE workouts;")
cursor.execute("DROP TABLE exercises;")
cursor.execute("DROP TABLE users;")


# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT
)
""")

# Exercises table
cursor.execute("""
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY,
    variant TEXT,
    machine_type TEXT,
    name TEXT,
    chest INTEGER,
    back INTEGER,
    legs INTEGER,
    shoulders INTEGER,
    biceps INTEGER,
    triceps INTEGER,
    misc_group INTEGER,
    barbell INTEGER,
    dumbbell INTEGER,
    machine INTEGER,
    cable INTEGER,
    smith INTEGER,
    misc_machine INTEGER,
    isolation INTEGER, 
    compound INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY, 
    user_id INTEGER,
    name TEXT, 
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# Logs table with composite key and foreign keys
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    user_id INTEGER,
    timestamp TEXT,
    exercise_id INTEGER,
    weight FLOAT,
    reps INTEGER,
    workout_id INTEGER, 
    first INTEGER, 
    PRIMARY KEY (user_id, timestamp),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (workout_id) references workouts(id)
)
""")

# Favorites table
cursor.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    user_id INTEGER,
    exercise_id INTEGER,
    PRIMARY KEY (user_id, exercise_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
)
""")

import pandas as pd 
excel_path = "data/test_database.xlsx"

integer_columns = {
    "users": ["id"],
    "exercises": ["id","chest","back","legs","shoulders","biceps","triceps",
                  "misc_group","barbell","dumbbell","machine","cable","smith","misc_machine", "isolation", "compound"],
    "logs": ["user_id","exercise_id","workout_id", "reps", "first"],
    "workouts": ["id","user_id"],
    "favorites": ["user_id","exercise_id"]
}

tables = ["users", "exercises", "workouts", "logs", "favorites"]

for table_name in tables:
    # Read sheet
    df = pd.read_excel(excel_path, sheet_name=table_name)

    cursor.execute(f"SELECT * FROM {table_name}")
    if len(cursor.fetchall()) > 0:
        continue
    
    # Fill integer NaNs with 0
    int_cols = [col for col in integer_columns.get(table_name, []) if col in df.columns]
    df[int_cols] = df[int_cols].fillna(0).astype(int)
    
    # Fill other columns' NaNs with empty string
    non_int_cols = [col for col in df.columns if col not in int_cols]
    df[non_int_cols] = df[non_int_cols].fillna("")
    
    # Insert into database
    df.to_sql(table_name, conn, if_exists="append", index=False)

conn.commit()
conn.close()
