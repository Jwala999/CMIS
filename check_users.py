import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('SELECT user_id, email, password_hash FROM users')
users = c.fetchall()
print("Users in database:")
for user in users:
    print(f"ID: {user[0]}, Email: {user[1]}, Password Hash: {user[2]}")
conn.close()