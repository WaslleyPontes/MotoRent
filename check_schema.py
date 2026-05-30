import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Verificar estrutura das tabelas importantes
tables = ['vehicle_inspection', 'payments', 'users', 'vehicles', 'customers']

for table in tables:
    print(f"\n{'='*50}")
    print(f"Tabela: {table}")
    print('='*50)
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
    
    # Mostrar um exemplo de registro
    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
    sample = cursor.fetchone()
    if sample:
        print(f"\nExemplo de registro:")
        for key in sample.keys():
            print(f"  {key}: {sample[key]}")
