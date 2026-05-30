import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users)")
print("Columns in users table:")
for row in cursor.fetchall():
    print(row)

# Also check what's in the table
cursor.execute("SELECT * FROM users LIMIT 1")
print("\nFirst user row:")
print(cursor.fetchone())
