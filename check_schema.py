#!/usr/bin/env python3

import sqlite3
import os

# Connect to the database
db_path = 'instance/globetrotter.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check trip_destinations table schema
print("=== trip_destinations table schema ===")
cursor.execute("PRAGMA table_info(trip_destinations)")
columns = cursor.fetchall()
for col in columns:
    print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}, PK: {col[5]}")

print("\n=== Sample data from trip_destinations ===")
cursor.execute("SELECT * FROM trip_destinations LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
