#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('globetrotter.db')
cursor = conn.cursor()

# Make admin@globetrotter.com an admin user
cursor.execute('UPDATE user SET is_admin = 1 WHERE email = ?', ('admin@globetrotter.com',))
print('Made admin@globetrotter.com an admin user')

# Check current admin users
cursor.execute('SELECT id, email, first_name, last_name, is_admin FROM user WHERE is_admin = 1')
admins = cursor.fetchall()

print('\nCurrent admin users:')
for admin in admins:
    print(f'ID: {admin[0]}, Email: {admin[1]}, Name: {admin[2]} {admin[3]}, Admin: {admin[4]}')

conn.commit()
conn.close()
print('\nAdmin setup complete!')
