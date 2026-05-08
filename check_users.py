import sqlite3

db = sqlite3.connect('database.db')
cur = db.cursor()
cur.execute('SELECT id, username, email, role FROM users')
users = cur.fetchall()
db.close()

print('Usuários no banco:')
for user in users:
    print(f'ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}')