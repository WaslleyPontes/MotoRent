import sqlite3
from werkzeug.security import generate_password_hash

# Conectar ao banco de dados
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Nova senha (em hash)
new_password_admin = generate_password_hash('123456')
new_password_operator = generate_password_hash('123456')

# Atualizar senha do admin
cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_password_admin, 'admin'))

# Atualizar senha do operador
cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_password_operator, 'operador'))

conn.commit()
conn.close()

print("Senhas resetadas com sucesso!")
print("Admin: admin / 123456")
print("Operador: operador / 123456")
