import sqlite3

conn = sqlite3.connect("./data/database.db")
cursor = conn.cursor()

# Enable foreign key support
cursor.execute("PRAGMA foreign_keys = ON;")

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
    title TEXT,
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
    misc_machine INTEGER
)
""")

# Logs table with composite key and foreign keys
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    user_id INTEGER,b
    timestamp TEXT,
    exercise_id INTEGER,
    weight FLOAT,
    reps INTEGER,
    PRIMARY KEY (user_id, timestamp),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
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

conn.commit()

conn.close()
