import os
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import app, get_db


def setup_module(module):
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False


def test_login_with_default_admin_credentials():
    client = app.test_client()
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET password_hash = ? WHERE username = ?", (generate_password_hash('admin123'), 'admin'))
        db.commit()

    response = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data
