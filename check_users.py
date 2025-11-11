#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('globetrotter.db')
cursor = conn.cursor()

print("=== Database Users ===")
cursor.execute('SELECT id, email, first_name, last_name FROM user')
users = cursor.fetchall()

if users:
    for user in users:
        print(f"ID: {user[0]}, Email: {user[1]}, Name: {user[2]} {user[3]}")
else:
    print("No users found in database")

print(f"\nTotal users: {len(users)}")
conn.close()
