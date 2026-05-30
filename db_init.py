import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).with_name('database.db')

schema = [
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, password_hash TEXT, role TEXT)",
    "CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, document_type TEXT, document TEXT, email TEXT, phone TEXT, score INTEGER, internal_notes TEXT DEFAULT '', cep TEXT, street TEXT, number TEXT, neighborhood TEXT, city TEXT, state TEXT, complement TEXT, UNIQUE(document_type, document))",
    "CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY, brand TEXT, model TEXT, plate TEXT UNIQUE, color TEXT DEFAULT 'Azul', status TEXT, insurance TEXT, latitude REAL, longitude REAL, owner_id INTEGER, FOREIGN KEY(owner_id) REFERENCES customers(id))",
    "CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, customer_id INTEGER, vehicle_id INTEGER, amount REAL, due_date TEXT, status TEXT, payment_method TEXT, FOREIGN KEY(customer_id) REFERENCES customers(id), FOREIGN KEY(vehicle_id) REFERENCES vehicles(id))",
    "CREATE TABLE IF NOT EXISTS payment_audit (id INTEGER PRIMARY KEY, payment_id INTEGER, changed_by INTEGER, changed_at TEXT, old_status TEXT, new_status TEXT, old_amount REAL, new_amount REAL, note TEXT, FOREIGN KEY(payment_id) REFERENCES payments(id), FOREIGN KEY(changed_by) REFERENCES users(id))",
    "CREATE TABLE IF NOT EXISTS vehicle_inspection (id INTEGER PRIMARY KEY, vehicle_id INTEGER, inspector_id INTEGER, inspection_date TEXT, inspection_type TEXT, condition TEXT, fuel_level TEXT, mileage INTEGER, notes TEXT, photos TEXT, created_at TEXT, FOREIGN KEY(vehicle_id) REFERENCES vehicles(id), FOREIGN KEY(inspector_id) REFERENCES users(id))",
    "CREATE TABLE IF NOT EXISTS fines (id INTEGER PRIMARY KEY, customer_id INTEGER, vehicle_id INTEGER, amount REAL, description TEXT, date TEXT, status TEXT, points INTEGER, FOREIGN KEY(customer_id) REFERENCES customers(id), FOREIGN KEY(vehicle_id) REFERENCES vehicles(id))",
    "CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY, vehicle_id INTEGER, last_service_date TEXT, next_service_date TEXT, status TEXT, predicted_cost REAL, note TEXT, FOREIGN KEY(vehicle_id) REFERENCES vehicles(id))",
    "CREATE TABLE IF NOT EXISTS telemetry (id INTEGER PRIMARY KEY, vehicle_id INTEGER, latitude REAL, longitude REAL, speed REAL, timestamp TEXT, status TEXT, FOREIGN KEY(vehicle_id) REFERENCES vehicles(id))",
    "CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, owner_type TEXT, owner_id INTEGER, doc_type TEXT, filename TEXT, note TEXT, background_check TEXT, uploaded_at TEXT)",
    "CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, customer_id INTEGER, vehicle_id INTEGER, sale_price REAL, installments INTEGER, installment_value REAL, sale_date TEXT, status TEXT, payment_method TEXT, FOREIGN KEY(customer_id) REFERENCES customers(id), FOREIGN KEY(vehicle_id) REFERENCES vehicles(id))",
]

sample_users = [
    ('admin', 'admin@exemplo.com', generate_password_hash('admin123'), 'admin'),
    ('operador', 'operador@exemplo.com', generate_password_hash('operador123'), 'operator'),
]

sample_customers = [
    ('João Silva', 'CPF', '12345678900', 'joao@exemplo.com', '+55 11 99999-0001', 720),
    ('Mariana Costa', 'CPF', '98765432100', 'mariana@exemplo.com', '+55 11 99999-0002', 680),
    ('Carlos Andrade', 'CPF', '45612378900', 'carlos@exemplo.com', '+55 11 99999-0003', 590),
]

sample_vehicles = [
    ('Honda', 'Honda CG 160', 'Azul', 'ABC-1234', 'alugado', 'Seguro Ativo', -23.55052, -46.63331, 1),
    ('Yamaha', 'Yamaha Fazer 250', 'Preta', 'DEF-5678', 'disponível', 'Seguro Ativo', -23.5587, -46.6253, 2),
    ('NK', 'NK 250', 'Vermelha', 'GHI-9012', 'manutenção', 'Seguro Vencido', -23.5610, -46.6500, 3),
]

sample_payments = [
    (1, 1, 350.0, '2026-04-10', 'pago', 'Boleto'),
    (2, 2, 420.0, '2026-04-18', 'atrasado', 'Pix'),
    (3, 3, 500.0, '2026-04-15', 'pago', 'Cartão'),
]

sample_fines = [
    (1, 1, 200.0, 'Excesso de velocidade', '2026-03-05', 'pendente', 4),
    (2, 2, 150.0, 'Estacionamento irregular', '2026-03-28', 'pago', 3),
]

sample_maintenance = [
    (1, '2026-02-15', '2026-08-15', 'programada', 450.0, 'Troca de óleo e revisão de freios'),
    (2, '2026-01-10', '2026-07-10', 'em breve', 780.0, 'Revisão preventiva e calibração de suspensão'),
]

sample_telemetry = [
    (1, -23.55052, -46.63331, 48.0, '2026-04-10 09:20', 'em rota'),
    (2, -23.55870, -46.62530, 0.0, '2026-04-10 09:42', 'parado'),
    (3, -23.56100, -46.65000, 35.0, '2026-04-10 10:05', 'em rota'),
]

sample_documents = [
    ('customer', 1, 'CNH', 'cnh_joao.pdf', 'Carteira de motorista válida', 'Não', '2026-04-10'),
    ('vehicle', 1, 'CRLV', 'crlv_cg160.pdf', 'Documentação do veículo', 'Não', '2026-04-10'),
]

if __name__ == '__main__':
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for stmt in schema:
        cur.execute(stmt)

    cur.execute('DELETE FROM users')
    cur.execute('DELETE FROM customers')
    cur.execute('DELETE FROM vehicles')
    cur.execute('DELETE FROM payments')
    cur.execute('DELETE FROM fines')
    cur.execute('DELETE FROM maintenance')
    cur.execute('DELETE FROM telemetry')
    cur.execute('DELETE FROM documents')

    cur.executemany('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)', sample_users)
    cur.executemany('INSERT INTO customers (name, document_type, document, email, phone, score) VALUES (?, ?, ?, ?, ?, ?)', sample_customers)
    cur.executemany('INSERT INTO vehicles (brand, model, color, plate, status, insurance, latitude, longitude, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', sample_vehicles)
    cur.executemany('INSERT INTO payments (customer_id, vehicle_id, amount, due_date, status, payment_method) VALUES (?, ?, ?, ?, ?, ?)', sample_payments)
    cur.executemany('INSERT INTO fines (customer_id, vehicle_id, amount, description, date, status, points) VALUES (?, ?, ?, ?, ?, ?, ?)', sample_fines)
    cur.executemany('INSERT INTO maintenance (vehicle_id, last_service_date, next_service_date, status, predicted_cost, note) VALUES (?, ?, ?, ?, ?, ?)', sample_maintenance)
    cur.executemany('INSERT INTO telemetry (vehicle_id, latitude, longitude, speed, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)', sample_telemetry)
    cur.executemany('INSERT INTO documents (owner_type, owner_id, doc_type, filename, note, background_check, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?)', sample_documents)

    conn.commit()
    conn.close()
    print(f'Banco de dados criado em {DB_PATH}')
