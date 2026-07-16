import sqlite3

from app import app, DB_PATH


def test_customer_delete_removes_customer_and_related_rows():
    app.testing = True
    with app.test_client() as client:
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['username'] = 'admin'
            session['role'] = 'admin'

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payments WHERE customer_id IN (SELECT id FROM customers WHERE name = 'Cliente Teste Exclusao')")
        cursor.execute("DELETE FROM reservations WHERE customer_id IN (SELECT id FROM customers WHERE name = 'Cliente Teste Exclusao')")
        cursor.execute("DELETE FROM fines WHERE customer_id IN (SELECT id FROM customers WHERE name = 'Cliente Teste Exclusao')")
        cursor.execute("DELETE FROM sales WHERE customer_id IN (SELECT id FROM customers WHERE name = 'Cliente Teste Exclusao')")
        cursor.execute("DELETE FROM customers WHERE name = 'Cliente Teste Exclusao'")
        conn.commit()

        cursor.execute(
            "INSERT INTO customers (name, document_type, document, email, phone, phone2, score, internal_notes, cep, street, number, neighborhood, city, state, complement) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ('Cliente Teste Exclusao', 'CPF', '12345678900', 'teste@example.com', '85999999999', '', 650, '', '', '', '', '', '', '', '')
        )
        customer_id = cursor.lastrowid
        cursor.execute("INSERT INTO payments (customer_id, vehicle_id, amount, due_date, status, payment_method) VALUES (?, ?, ?, ?, ?, ?)", (customer_id, 1, 100.00, '2030-01-01', 'pendente', 'PIX'))
        cursor.execute("INSERT INTO reservations (customer_id, vehicle_id, start_date, end_date, status, created_at, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", (customer_id, 1, '2030-01-01', '2030-01-03', 'confirmada', '2030-01-01', 'teste'))
        conn.commit()
        conn.close()

        response = client.post('/customers', data={'action': 'delete', 'customer_id': customer_id}, follow_redirects=True)
        assert response.status_code == 200

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        customer = conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
        payments = conn.execute("SELECT id FROM payments WHERE customer_id = ?", (customer_id,)).fetchall()
        reservations = conn.execute("SELECT id FROM reservations WHERE customer_id = ?", (customer_id,)).fetchall()
        conn.close()

        assert customer is None
        assert payments == []
        assert reservations == []
