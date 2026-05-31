from flask import Flask, jsonify, render_template, g, request, redirect, url_for, session, flash, send_from_directory, send_file, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from dotenv import load_dotenv
import sqlite3
import os
import smtplib
import ssl
from email.message import EmailMessage
import time
from pathlib import Path
import secrets
import json
import io
from fpdf import FPDF
import urllib.request
import urllib.error
import datetime

load_dotenv()

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    import warnings
    warnings.warn("PIL/pytesseract não instalados. OCR será desabilitado.")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'database.db'
UPLOAD_FOLDER = BASE_DIR / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_urlsafe(16))

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', '')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@example.com')

app.config['PREFERRED_URL_SCHEME'] = os.environ.get('FLASK_ENV', 'development') == 'production' and 'https' or 'http'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV', 'development') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict' if os.environ.get('FLASK_ENV', 'development') == 'production' else 'Lax'
app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('FLASK_ENV', 'development') == 'production'
app.config['SESSION_REFRESH_EACH_REQUEST'] = True


def ensure_column_exists(db, table, column, definition):
    cur = db.execute(f"PRAGMA table_info({table})")
    columns = [row['name'] for row in cur.fetchall()]
    cur.close()
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


ALLOWED_UPLOAD_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


def allowed_file(filename):
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_UPLOAD_EXTENSIONS


def send_reset_email(to_email, reset_url):
    server = app.config['MAIL_SERVER']
    if not server:
        return False

    message = EmailMessage()
    message['Subject'] = 'Recuperação de senha MotoRent'
    message['From'] = app.config['MAIL_DEFAULT_SENDER']
    message['To'] = to_email
    message.set_content(f"Olá,\n\nRecebemos uma solicitação para redefinir sua senha.\n\nUse este link para continuar:\n{reset_url}\n\nCaso não tenha solicitado, ignore esta mensagem.\n\nAtenciosamente,\nEquipe MotoRent")

    try:
        if app.config['MAIL_USE_SSL']:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(server, app.config['MAIL_PORT'], context=context) as smtp:
                if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
                    smtp.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
                smtp.send_message(message)
        else:
            with smtplib.SMTP(server, app.config['MAIL_PORT']) as smtp:
                if app.config['MAIL_USE_TLS']:
                    smtp.starttls(context=ssl.create_default_context())
                if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
                    smtp.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
                smtp.send_message(message)
        return True
    except smtplib.SMTPException as e:
        import warnings
        warnings.warn(f"Erro ao enviar email: {str(e)}")
        return False
    except Exception as e:
        import warnings
        warnings.warn(f"Erro inesperado ao enviar email: {str(e)}")
        return False


def ensure_schema_migrations(db):
    ensure_column_exists(db, 'customers', 'document_type', "TEXT DEFAULT 'CPF'")
    ensure_column_exists(db, 'customers', 'internal_notes', "TEXT DEFAULT ''")
    ensure_column_exists(db, 'customers', 'cep', 'TEXT')
    ensure_column_exists(db, 'customers', 'phone2', 'TEXT')
    ensure_column_exists(db, 'customers', 'street', 'TEXT')
    ensure_column_exists(db, 'customers', 'number', 'TEXT')
    ensure_column_exists(db, 'customers', 'neighborhood', 'TEXT')
    ensure_column_exists(db, 'customers', 'city', 'TEXT')
    ensure_column_exists(db, 'customers', 'state', 'TEXT')
    ensure_column_exists(db, 'customers', 'complement', 'TEXT')
    ensure_column_exists(db, 'vehicles', 'brand', "TEXT DEFAULT 'Honda'")
    ensure_column_exists(db, 'vehicles', 'color', "TEXT DEFAULT 'Azul'")
    ensure_column_exists(db, 'payments', 'payment_method', "TEXT DEFAULT 'Boleto'")
    ensure_column_exists(db, 'documents', 'background_check', "TEXT DEFAULT 'Não'")
    ensure_column_exists(db, 'users', 'reset_token', 'TEXT')
    ensure_column_exists(db, 'users', 'reset_token_expires', 'INTEGER')
    try:
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_document_unique ON customers(document_type, document)')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_vehicles_plate_unique ON vehicles(plate)')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_email_unique ON customers(email) WHERE email IS NOT NULL AND email != ""')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_phone_unique ON customers(phone) WHERE phone IS NOT NULL AND phone != ""')
    except sqlite3.Error:
        pass
    db.execute('CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY, customer_id INTEGER, vehicle_id INTEGER, start_date TEXT, end_date TEXT, status TEXT, created_at TEXT, notes TEXT, FOREIGN KEY(customer_id) REFERENCES customers(id), FOREIGN KEY(vehicle_id) REFERENCES vehicles(id))')
    db.execute('CREATE TABLE IF NOT EXISTS payment_audit (id INTEGER PRIMARY KEY, payment_id INTEGER, changed_by INTEGER, changed_at TEXT, old_status TEXT, new_status TEXT, old_amount REAL, new_amount REAL, note TEXT, FOREIGN KEY(payment_id) REFERENCES payments(id), FOREIGN KEY(changed_by) REFERENCES users(id))')
    db.execute('CREATE TABLE IF NOT EXISTS vehicle_inspection (id INTEGER PRIMARY KEY, vehicle_id INTEGER, inspector_id INTEGER, inspection_date TEXT, inspection_type TEXT, condition TEXT, fuel_level TEXT, mileage INTEGER, notes TEXT, photos TEXT, created_at TEXT, FOREIGN KEY(vehicle_id) REFERENCES vehicles(id), FOREIGN KEY(inspector_id) REFERENCES users(id))')
    db.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, customer_id INTEGER, vehicle_id INTEGER, sale_price REAL, installments INTEGER, installment_value REAL, sale_date TEXT, status TEXT, payment_method TEXT, FOREIGN KEY(customer_id) REFERENCES customers(id), FOREIGN KEY(vehicle_id) REFERENCES vehicles(id))')
    db.commit()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        ensure_schema_migrations(db)
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view


def generate_csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


def validate_csrf_token(token):
    return token and token == session.get('_csrf_token')


def sync_overdue_payments():
    db = get_db()
    db.execute("UPDATE payments SET status = 'atrasado' WHERE status != 'pago' AND date(due_date) < date('now')")
    db.commit()


@app.context_processor
def inject_csrf_token():
    return {'csrf_token': generate_csrf_token()}


@app.before_request
def enforce_https_and_csrf():
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        # Accept CSRF token from common locations: form, headers, JSON body or query param
        token = None
        # form data
        try:
            token = request.form.get('csrf_token')
        except Exception:
            token = None
        # headers (several common header names)
        if not token:
            token = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF')
        # json body
        if not token and request.is_json:
            try:
                token = (request.get_json(silent=True) or {}).get('csrf_token')
            except Exception:
                token = None
        # query params (fallback for API calls)
        if not token:
            token = request.args.get('csrf_token')

        if not validate_csrf_token(token):
            abort(400, 'CSRF token inválido ou ausente.')

    sync_overdue_payments()

    if os.environ.get('FLASK_ENV', '').lower() == 'production':
        proto = request.headers.get('X-Forwarded-Proto', 'http')
        if proto != 'https' and not request.is_secure:
            secure_url = request.url.replace('http://', 'https://', 1)
            return redirect(secure_url, code=301)


@app.after_request
def set_security_headers(response):
    response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
    response.headers.setdefault('X-XSS-Protection', '1; mode=block')
    response.headers.setdefault('Content-Security-Policy', "default-src 'self' https://cdn.jsdelivr.net https://unpkg.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://unpkg.com; img-src 'self' data: https:; connect-src 'self' https://tile.openstreetmap.org https://a.tile.openstreetmap.org https://b.tile.openstreetmap.org https://c.tile.openstreetmap.org; font-src 'self' data:; frame-ancestors 'none'; object-src 'none'; base-uri 'self';")
    return response


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if session.get('role') != 'admin':
            flash('Acesso restrito a administradores.')
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if session.get('role') not in allowed_roles:
                flash('Você não tem permissão para acessar esta área.')
                return redirect(url_for('index'))
            return view(**kwargs)
        return wrapped_view
    return decorator


def calculate_driver_score(customer_id):
    customer = query_db('SELECT * FROM customers WHERE id = ?', (customer_id,), one=True)
    if not customer:
        return None

    late_count = query_db('SELECT COUNT(*) AS count FROM payments WHERE customer_id = ? AND status = ?', (customer_id, 'atrasado'), one=True)['count']
    unpaid_fines = query_db('SELECT COUNT(*) AS count, SUM(amount) AS total FROM fines WHERE customer_id = ? AND status = ?', (customer_id, 'pendente'), one=True)
    fine_count = unpaid_fines['count'] or 0
    fine_amount = unpaid_fines['total'] or 0
    base_score = int(customer['score'] or 0)
    penalty = late_count * 30 + fine_count * 20 + int(fine_amount // 100)
    risk_score = max(0, min(100, base_score // 10 - penalty // 5))

    status = 'Aprovado' if risk_score >= 65 else 'Atenção' if risk_score >= 45 else 'Negado'
    notes = []
    if late_count > 0:
        notes.append(f'Histórico de {late_count} pagamento(s) atrasado(s).')
    if fine_count > 0:
        notes.append(f'{fine_count} multa(s) pendente(s) com valor total de R$ {fine_amount:.2f}.')
    if risk_score < 50:
        notes.append('Risco maior; recomenda-se análise adicional de documentos e comprovantes.')

    if not notes:
        notes.append('Nenhuma irregularidade encontrada nos registros atuais.')

    return {
        'risk_score': risk_score,
        'status': status,
        'recommendation': 'Liberar com acompanhamento' if risk_score >= 65 else 'Reforçar análise de crédito',
        'notes': notes
    }


def check_criminal_records(search_term):
    """
    Simulação de consulta aos antecedentes criminais no TJCE
    Em produção, isso seria integrado com a API real do Tribunal de Justiça do Ceará
    """
    # Simulação baseada no termo de busca
    # Em produção, isso faria uma chamada real para a API do TJCE
    
    # Para demonstração, vamos simular alguns cenários baseados no termo
    if not search_term:
        return None
    
    # Simulação: alguns CPFs têm registros (apenas para demo)
    mock_criminal_data = {
        '12345678900': {
            'count': 2,
            'details': [
                {'type': 'Trânsito', 'description': 'Dirigir sob efeito de álcool', 'date': '2023-08-15'},
                {'type': 'Furto', 'description': 'Furto qualificado', 'date': '2022-11-20'}
            ]
        },
        '98765432100': {
            'count': 1,
            'details': [
                {'type': 'Trânsito', 'description': 'Excesso de velocidade habitual', 'date': '2024-01-10'}
            ]
        },
        'joão silva': {
            'count': 2,
            'details': [
                {'type': 'Trânsito', 'description': 'Dirigir sob efeito de álcool', 'date': '2023-08-15'},
                {'type': 'Furto', 'description': 'Furto qualificado', 'date': '2022-11-20'}
            ]
        }
        # Outros termos retornam None (sem registros)
    }
    
    # Limpar o termo de busca (remover pontos, traços, etc.)
    clean_term = ''.join(c for c in search_term if c.isdigit())
    normalized_term = search_term.strip().lower()
    
    if clean_term in mock_criminal_data:
        return mock_criminal_data[clean_term]
    if normalized_term in mock_criminal_data:
        return mock_criminal_data[normalized_term]
    
    # Se não encontrou registros específicos, retorna None (sem antecedentes)
    return None


def extract_text_from_file(path):
    if OCR_AVAILABLE:
        try:
            image = Image.open(path)
            return pytesseract.image_to_string(image, lang='por')
        except FileNotFoundError:
            return 'OCR falhou: arquivo não encontrado. Verifique a instalação do Tesseract ou envie outro arquivo.'
        except Exception as e:
            return f'OCR falhou ao processar o arquivo: {str(e)}'

    return 'OCR não disponível neste ambiente. Arquivo salvo com sucesso.'


@app.route('/')
@login_required
def index():
    total_clients = query_db('SELECT COUNT(*) AS count FROM customers', one=True)['count']
    total_vehicles = query_db('SELECT COUNT(*) AS count FROM vehicles', one=True)['count']
    active_rentals = query_db("SELECT COUNT(*) AS count FROM vehicles WHERE status = 'alugado'", one=True)['count']
    available_vehicles = query_db("SELECT COUNT(*) AS count FROM vehicles WHERE status = 'disponível'", one=True)['count']
    maintenance_vehicles = query_db("SELECT COUNT(*) AS count FROM vehicles WHERE status = 'manutenção'", one=True)['count']
    overdue_payments = query_db("SELECT COUNT(*) AS count FROM payments WHERE status = 'atrasado'", one=True)['count']
    overdue_amount = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'atrasado'", one=True)['total'] or 0
    total_income = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'pago'", one=True)['total'] or 0
    predicted_revenue = query_db("SELECT SUM(amount) AS total FROM payments WHERE status != 'pago' AND due_date >= date('now')", one=True)['total'] or 0
    operational_vehicles = query_db("SELECT COUNT(*) AS count FROM vehicles WHERE status = 'disponível' OR status = 'alugado'", one=True)['count']
    occupancy_rate = round((active_rentals / total_vehicles * 100) if total_vehicles else 0, 1)

    revenue_by_month = [dict(row) for row in query_db("SELECT strftime('%Y-%m', due_date) AS month, SUM(amount) AS total FROM payments WHERE status = 'pago' GROUP BY month ORDER BY month DESC LIMIT 6")]

    vehicle_revenues = query_db("SELECT v.id, v.model, v.brand, v.status, COALESCE(SUM(p.amount),0) AS revenue FROM vehicles v LEFT JOIN payments p ON p.vehicle_id = v.id AND p.status = 'pago' GROUP BY v.id ORDER BY revenue DESC")
    profit_by_vehicle = []
    for row in vehicle_revenues:
        row = dict(row)
        estimated_cost = 9000
        profit = row['revenue'] - estimated_cost
        profit_by_vehicle.append({
            'vehicle': f"{row['brand']} {row['model']}",
            'revenue': row['revenue'],
            'profit': profit
        })

    customer_rows = query_db('SELECT id, name FROM customers')
    customer_risks = []
    for customer in customer_rows:
        risk = calculate_driver_score(customer['id'])
        if risk:
            customer_risks.append({'name': customer['name'], 'risk': risk['risk_score'], 'status': risk['status'], 'recommendation': risk['recommendation']})
    customer_risks.sort(key=lambda item: item['risk'])
    top_risky_customers = customer_risks[:3]

    locations = [dict(row) for row in query_db('SELECT model, latitude, longitude, status FROM vehicles WHERE latitude IS NOT NULL AND longitude IS NOT NULL')]

    vehicle_status_counts = [dict(row) for row in query_db("SELECT status, COUNT(*) AS count FROM vehicles GROUP BY status")]

    return render_template(
        'index.html',
        title='Dashboard',
        subtitle='Rede de locações e controle operacional',
        total_clients=total_clients,
        total_vehicles=total_vehicles,
        active_rentals=active_rentals,
        available_vehicles=available_vehicles,
        maintenance_vehicles=maintenance_vehicles,
        overdue_payments=overdue_payments,
        overdue_amount=overdue_amount,
        total_income=total_income,
        predicted_revenue=predicted_revenue,
        occupancy_rate=occupancy_rate,
        revenue_by_month=revenue_by_month,
        profit_by_vehicle=profit_by_vehicle,
        top_risky_customers=top_risky_customers,
        locations=locations,
        vehicle_status_counts=vehicle_status_counts
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Preencha usuário e senha.')
            return render_template('login.html', title='Login', subtitle='Acesse o painel de controle')

        user = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        flash('Usuário ou senha incorretos.')

    return render_template('login.html', title='Login', subtitle='Acesse o painel de controle')


def validate_password_strength(password):
    if len(password) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres."
    if not any(c.isdigit() for c in password):
        return False, "Senha deve conter pelo menos 1 número."
    if not any(c.isupper() for c in password):
        return False, "Senha deve conter pelo menos 1 letra maiúscula."
    return True, ""


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('Preencha todos os campos.')
            return render_template('register.html', title='Registrar', subtitle='Crie sua conta')
        
        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            flash(msg)
            return render_template('register.html', title='Registrar', subtitle='Crie sua conta')

        if query_db('SELECT id FROM users WHERE username = ?', (username,), one=True):
            flash('Nome de usuário já existe.')
            return render_template('register.html', title='Registrar', subtitle='Crie sua conta')

        password_hash = generate_password_hash(password)
        db = get_db()
        db.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)', (username, email, password_hash, 'operator'))
        db.commit()
        flash('Conta criada com sucesso. Faça login agora.')
        return redirect(url_for('login'))

    return render_template('register.html', title='Registrar', subtitle='Crie sua conta')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    reset_link = None
    email_sent = False
    if request.method == 'POST':
        email = request.form.get('email')
        user = query_db('SELECT * FROM users WHERE email = ?', (email,), one=True)
        if user:
            reset_token = secrets.token_urlsafe(24)
            expires = int(time.time() + 3600)
            db = get_db()
            db.execute('UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?',
                       (reset_token, expires, user['id']))
            db.commit()
            reset_link = url_for('reset_password', token=reset_token, _external=True)
            if send_reset_email(email, reset_link):
                email_sent = True
                flash('Enviamos o link de recuperação para o seu e-mail.')
            else:
                flash('Não foi possível enviar e-mail. Use o link abaixo para redefinir sua senha.')
        else:
            flash('E-mail não encontrado. Verifique e tente novamente.')
    return render_template('forgot_password.html', title='Recuperar senha', subtitle='Redefina sua senha', reset_link=reset_link, email_sent=email_sent)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = query_db('SELECT * FROM users WHERE reset_token = ?', (token,), one=True)
    if not user or not user['reset_token_expires'] or user['reset_token_expires'] < int(time.time()):
        flash('Token de recuperação inválido ou expirado. Solicite um novo link.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('As senhas não coincidem. Tente novamente.')
            return render_template('reset_password.html', title='Redefinir senha', subtitle='Digite a nova senha')
        
        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            flash(msg)
            return render_template('reset_password.html', title='Redefinir senha', subtitle='Digite a nova senha')

        password_hash = generate_password_hash(password)
        db = get_db()
        db.execute('UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?',
                   (password_hash, user['id']))
        db.commit()
        flash('Senha redefinida com sucesso. Faça login novamente.')
        return redirect(url_for('login'))

    return render_template('reset_password.html', title='Redefinir senha', subtitle='Digite a nova senha')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada.')
    return redirect(url_for('login'))


@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    if request.method == 'POST':
        action = request.form.get('action', 'create')
        db = get_db()
        if action == 'create':
            name = request.form.get('name', '').strip()
            document_type = request.form.get('document_type', 'CPF')
            document = request.form.get('document', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            phone2 = request.form.get('phone2', '').strip()
            try:
                score = int(request.form.get('score', 0) or 0)
            except (TypeError, ValueError):
                score = 0
            internal_notes = request.form.get('internal_notes', '')
            cep = request.form.get('cep', '').strip()
            street = request.form.get('street', '').strip()
            number = request.form.get('number', '').strip()
            neighborhood = request.form.get('neighborhood', '').strip()
            city = request.form.get('city', '').strip()
            state = request.form.get('state', '').strip()
            complement = request.form.get('complement', '').strip()

            if not name or not document:
                flash('Nome e documento são obrigatórios.', 'error')
                return redirect(url_for('customers'))
            
            # Validar documento duplicado
            existing = query_db('SELECT id FROM customers WHERE document_type = ? AND document = ?', (document_type, document), one=True)
            if existing:
                flash(f'Já existe um cliente cadastrado com este {document_type}!', 'error')
                return redirect(url_for('customers'))
            
            # Validar email duplicado
            if email:
                existing = query_db('SELECT id FROM customers WHERE email = ?', (email,), one=True)
                if existing:
                    flash('Este email já foi cadastrado para outro cliente!', 'error')
                    return redirect(url_for('customers'))
            
            # Validar telefone duplicado (telefone 1)
            if phone:
                existing = query_db('SELECT id FROM customers WHERE phone = ?', (phone,), one=True)
                if existing:
                    flash('Este telefone já foi cadastrado para outro cliente!', 'error')
                    return redirect(url_for('customers'))
            # Validar telefone duplicado (telefone 2)
            if phone2:
                existing = query_db('SELECT id FROM customers WHERE phone2 = ?', (phone2,), one=True)
                if existing:
                    flash('Este telefone 2 já foi cadastrado para outro cliente!', 'error')
                    return redirect(url_for('customers'))
            
            db.execute('INSERT INTO customers (name, document_type, document, email, phone, phone2, score, internal_notes, cep, street, number, neighborhood, city, state, complement) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (name, document_type, document, email, phone, phone2, score, internal_notes, cep, street, number, neighborhood, city, state, complement))
            db.commit()
            flash('Cliente cadastrado com sucesso.')
        elif action == 'update':
            try:
                customer_id = int(request.form.get('customer_id', 0))
            except (TypeError, ValueError):
                customer_id = 0
            name = request.form.get('name', '').strip()
            document_type = request.form.get('document_type', 'CPF')
            document = request.form.get('document', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            phone2 = request.form.get('phone2', '').strip()
            try:
                score = int(request.form.get('score', 0) or 0)
            except (TypeError, ValueError):
                score = 0
            internal_notes = request.form.get('internal_notes', '')
            cep = request.form.get('cep', '').strip()
            street = request.form.get('street', '').strip()
            number = request.form.get('number', '').strip()
            neighborhood = request.form.get('neighborhood', '').strip()
            city = request.form.get('city', '').strip()
            state = request.form.get('state', '').strip()
            complement = request.form.get('complement', '').strip()

            if not customer_id or not name or not document:
                flash('ID, nome e documento são obrigatórios.', 'error')
                return redirect(url_for('customers'))
            
            # Validar documento duplicado (exceto o próprio cliente)
            existing = query_db('SELECT id FROM customers WHERE document_type = ? AND document = ? AND id != ?', (document_type, document, customer_id), one=True)
            if existing:
                flash(f'Já existe outro cliente com este {document_type}!', 'error')
                return redirect(url_for('customers'))
            
            # Validar email duplicado (exceto o próprio cliente)
            if email:
                existing = query_db('SELECT id FROM customers WHERE email = ? AND id != ?', (email, customer_id), one=True)
                if existing:
                    flash('Este email já foi cadastrado para outro cliente!', 'error')
                    return redirect(url_for('customers'))
            
            # Validar telefone duplicado (exceto o próprio cliente) - telefone 1
            if phone:
                existing = query_db('SELECT id FROM customers WHERE phone = ? AND id != ?', (phone, customer_id), one=True)
                if existing:
                    flash('Este telefone já foi cadastrado para outro cliente!', 'error')
                    return redirect(url_for('customers'))
            # Validar telefone duplicado (exceto o próprio cliente) - telefone 2
            if phone2:
                existing = query_db('SELECT id FROM customers WHERE phone2 = ? AND id != ?', (phone2, customer_id), one=True)
                if existing:
                    flash('Este telefone 2 já foi cadastrado para outro cliente!', 'error')
                    return redirect(url_for('customers'))
            
            db.execute('UPDATE customers SET name = ?, document_type = ?, document = ?, email = ?, phone = ?, phone2 = ?, score = ?, internal_notes = ?, cep = ?, street = ?, number = ?, neighborhood = ?, city = ?, state = ?, complement = ? WHERE id = ?',
                       (name, document_type, document, email, phone, phone2, score, internal_notes, cep, street, number, neighborhood, city, state, complement, customer_id))
            db.commit()
            flash('Cliente atualizado com sucesso.')
        elif action == 'delete':
            try:
                customer_id = int(request.form.get('customer_id', 0))
            except (TypeError, ValueError):
                customer_id = 0
            if customer_id:
                db.execute('UPDATE vehicles SET owner_id = NULL WHERE owner_id = ?', (customer_id,))
                db.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
                db.commit()
                flash('Cliente excluído com sucesso.')
            else:
                flash('Cliente inválido para exclusão.', 'error')
        return redirect(url_for('customers'))

    customers = query_db('SELECT * FROM customers ORDER BY name')
    return render_template('customers.html', title='Clientes', subtitle='Cadastro e análise de condutores', customers=customers)


@app.route('/customer/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def customer_profile(customer_id):
    db = get_db()
    customer = query_db('SELECT * FROM customers WHERE id = ?', (customer_id,), one=True)
    if not customer:
        flash('Cliente não encontrado.')
        return redirect(url_for('customers'))

    if request.method == 'POST':
        internal_notes = request.form.get('internal_notes', '')
        db.execute('UPDATE customers SET internal_notes = ? WHERE id = ?', (internal_notes, customer_id))
        db.commit()
        flash('Notas internas atualizadas com sucesso.')
        return redirect(url_for('customer_profile', customer_id=customer_id))

    payments = [dict(row) for row in query_db('SELECT p.*, v.model AS vehicle, v.plate AS plate FROM payments p JOIN vehicles v ON p.vehicle_id = v.id WHERE p.customer_id = ? ORDER BY p.due_date DESC', (customer_id,))]
    fines = [dict(row) for row in query_db('SELECT f.*, v.model AS vehicle, v.plate AS plate FROM fines f JOIN vehicles v ON f.vehicle_id = v.id WHERE f.customer_id = ? ORDER BY f.date DESC', (customer_id,))]
    vehicles = [dict(row) for row in query_db('SELECT * FROM vehicles WHERE owner_id = ? ORDER BY model', (customer_id,))]
    risk_info = calculate_driver_score(customer_id)
    total_revenue = sum(p['amount'] for p in payments if p['status'] == 'pago')
    overdue_balance = sum(p['amount'] for p in payments if p['status'] == 'atrasado')

    return render_template(
        'customer_profile.html',
        title='Perfil do cliente',
        subtitle=f'Perfil e histórico de {customer["name"]}',
        customer=customer,
        payments=payments,
        fines=fines,
        vehicles=vehicles,
        risk_info=risk_info,
        total_revenue=total_revenue,
        overdue_balance=overdue_balance
    )


@app.route('/vehicles', methods=['GET', 'POST'])
@login_required
def vehicles():
    if request.method == 'POST':
        action = request.form.get('action', 'create')
        db = get_db()
        if action == 'create':
            model = request.form.get('model', '').strip()
            brand = request.form.get('brand', '').strip()
            plate = request.form.get('plate', '').strip().upper()
            color = request.form.get('color', '').strip()
            status = request.form.get('status', '').strip()
            insurance = request.form.get('insurance', '').strip()
            try:
                owner_id = int(request.form.get('owner_id', 0) or 0)
            except (TypeError, ValueError):
                owner_id = 0
            
            if not model or not brand or not plate:
                flash('Marca, modelo e placa são obrigatórios.', 'error')
                return redirect(url_for('vehicles'))

            # Validar placa duplicada
            existing = query_db('SELECT id FROM vehicles WHERE plate = ?', (plate,), one=True)
            if existing:
                flash('Já existe um veículo cadastrado com esta placa!', 'error')
                return redirect(url_for('vehicles'))
            
            db.execute('INSERT INTO vehicles (brand, model, plate, color, status, insurance, latitude, longitude, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (brand, model, plate, color, status, insurance, -23.55, -46.63, owner_id if owner_id > 0 else None))
            db.commit()
            flash('Veículo registrado com sucesso.')
        elif action == 'update':
            try:
                vehicle_id = int(request.form.get('vehicle_id', 0))
            except (TypeError, ValueError):
                vehicle_id = 0
            model = request.form.get('model', '').strip()
            brand = request.form.get('brand', '').strip()
            plate = request.form.get('plate', '').strip().upper()
            color = request.form.get('color', '').strip()
            status = request.form.get('status', '').strip()
            insurance = request.form.get('insurance', '').strip()
            try:
                owner_id = int(request.form.get('owner_id', 0) or 0)
            except (TypeError, ValueError):
                owner_id = 0
            
            if not vehicle_id or not model or not brand or not plate:
                flash('ID, marca, modelo e placa são obrigatórios.', 'error')
                return redirect(url_for('vehicles'))

            # Validar placa duplicada (exceto o próprio veículo)
            existing = query_db('SELECT id FROM vehicles WHERE plate = ? AND id != ?', (plate, vehicle_id), one=True)
            if existing:
                flash('Já existe outro veículo com esta placa!', 'error')
                return redirect(url_for('vehicles'))
            
            db.execute('UPDATE vehicles SET brand = ?, model = ?, plate = ?, color = ?, status = ?, insurance = ?, owner_id = ? WHERE id = ?',
                       (brand, model, plate, color, status, insurance, owner_id if owner_id > 0 else None, vehicle_id))
            db.commit()
            flash('Veículo atualizado com sucesso.')
        elif action == 'delete':
            try:
                vehicle_id = int(request.form.get('vehicle_id', 0))
            except (TypeError, ValueError):
                vehicle_id = 0
            if vehicle_id:
                db.execute('DELETE FROM vehicles WHERE id = ?', (vehicle_id,))
                db.commit()
                flash('Veículo excluído com sucesso.')
            else:
                flash('Veículo inválido para exclusão.', 'error')
        return redirect(url_for('vehicles'))

    customers = query_db('SELECT * FROM customers ORDER BY name')
    raw_vehicles = query_db('SELECT v.*, c.name AS owner_name FROM vehicles v LEFT JOIN customers c ON v.owner_id = c.id ORDER BY v.model')
    vehicles = [dict(row) for row in raw_vehicles]
    return render_template('vehicles.html', title='Veículos', subtitle='Cadastro e controle de frota', customers=customers, vehicles=vehicles)


@app.route('/pos', methods=['GET', 'POST'])
@login_required
def pos():
    db = get_db()
    message = None
    if request.method == 'POST':
        customer_id = int(request.form['customer_id'])
        vehicle_id = int(request.form['vehicle_id'])
        sale_price = float(request.form['sale_price'] or 0)
        installments = int(request.form['installments'] or 1)
        installment_value = float(request.form['installment_value'] or 0)
        payment_method = request.form.get('payment_method', 'À vista')
        sale_date = request.form.get('sale_date') or time.strftime('%Y-%m-%d')

        db.execute('INSERT INTO sales (customer_id, vehicle_id, sale_price, installments, installment_value, sale_date, status, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (customer_id, vehicle_id, sale_price, installments, installment_value, sale_date, 'concluída', payment_method))
        db.execute('UPDATE vehicles SET status = ?, owner_id = ? WHERE id = ?', ('vendido', customer_id, vehicle_id))
        db.commit()
        flash('Venda registrada com sucesso e estoque atualizado.')
        return redirect(url_for('pos'))

    customers = query_db('SELECT * FROM customers ORDER BY name')
    available_vehicles = query_db("SELECT * FROM vehicles WHERE status = 'disponível' ORDER BY model")
    sales = [dict(row) for row in query_db('SELECT s.*, c.name AS customer, v.model AS vehicle, v.plate AS plate FROM sales s JOIN customers c ON s.customer_id = c.id JOIN vehicles v ON s.vehicle_id = v.id ORDER BY s.sale_date DESC LIMIT 20')]
    return render_template('pos.html', title='PDV', subtitle='Ponto de venda de motos', customers=customers, available_vehicles=available_vehicles, sales=sales)


@app.route('/reservations', methods=['GET', 'POST'])
@login_required
def reservations():
    db = get_db()
    if request.method == 'POST':
        try:
            customer_id = int(request.form.get('customer_id', 0))
            vehicle_id = int(request.form.get('vehicle_id', 0))
        except (TypeError, ValueError):
            customer_id = 0
            vehicle_id = 0

        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        notes = request.form.get('notes', '').strip()

        if not customer_id or not vehicle_id or not start_date or not end_date:
            flash('Preencha todos os campos obrigatórios.', 'error')
            return redirect(url_for('reservations'))

        if start_date > end_date:
            flash('Data de início deve ser anterior ou igual à data de fim.', 'error')
            return redirect(url_for('reservations'))

        overlap = query_db(
            "SELECT COUNT(*) AS count FROM reservations WHERE vehicle_id = ? AND status IN ('confirmada','reservado') AND NOT (end_date < ? OR start_date > ?)",
            (vehicle_id, start_date, end_date), one=True)['count']

        if overlap:
            flash('O veículo já está reservado no período selecionado.', 'error')
            return redirect(url_for('reservations'))

        db.execute('INSERT INTO reservations (customer_id, vehicle_id, start_date, end_date, status, created_at, notes) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (customer_id, vehicle_id, start_date, end_date, 'confirmada', datetime.date.today().isoformat(), notes))
        current_status = query_db('SELECT status FROM vehicles WHERE id = ?', (vehicle_id,), one=True)
        if current_status and current_status['status'] == 'disponível':
            db.execute('UPDATE vehicles SET status = ? WHERE id = ?', ('reservado', vehicle_id))
        db.commit()
        flash('Reserva confirmada com sucesso.')
        return redirect(url_for('reservations'))

    customers = query_db('SELECT * FROM customers ORDER BY name')
    available_vehicles = query_db("SELECT * FROM vehicles WHERE status = 'disponível' ORDER BY model")
    reservations_data = [dict(row) for row in query_db("SELECT r.*, c.name AS customer_name, v.model AS vehicle_model, v.plate AS vehicle_plate FROM reservations r JOIN customers c ON r.customer_id = c.id JOIN vehicles v ON r.vehicle_id = v.id ORDER BY r.start_date DESC")]
    upcoming_reservations = [r for r in reservations_data if r['end_date'] >= datetime.date.today().isoformat()]
    return render_template('reservations.html', title='Reservas', subtitle='Reserva online e disponibilidade de frota', customers=customers, available_vehicles=available_vehicles, reservations=reservations_data, upcoming_reservations=upcoming_reservations)


@app.route('/receipt/<int:sale_id>')
@login_required
def sale_receipt(sale_id):
    sale = query_db(
        'SELECT s.*, c.name AS customer, c.email AS customer_email, c.phone AS customer_phone, v.brand AS vehicle_brand, v.model AS vehicle_model, v.plate AS vehicle_plate '
        'FROM sales s JOIN customers c ON s.customer_id = c.id JOIN vehicles v ON s.vehicle_id = v.id WHERE s.id = ?',
        (sale_id,), one=True)
    if not sale:
        abort(404)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Recibo de Venda MotoRent', ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.ln(4)
    pdf.cell(0, 8, f'Venda ID: {sale_id}', ln=True)
    pdf.cell(0, 8, f'Data: {sale["sale_date"]}', ln=True)
    pdf.cell(0, 8, f'Cliente: {sale["customer"]}', ln=True)
    pdf.cell(0, 8, f'E-mail: {sale["customer_email"] or "-"}', ln=True)
    pdf.cell(0, 8, f'Telefone: {sale["customer_phone"] or "-"}', ln=True)
    pdf.ln(4)
    pdf.cell(0, 8, 'Veículo:', ln=True)
    pdf.cell(0, 8, f'  {sale["vehicle_brand"]} {sale["vehicle_model"]} - {sale["vehicle_plate"]}', ln=True)
    pdf.ln(4)
    pdf.cell(0, 8, f'Valor total: R$ {sale["sale_price"]:.2f}', ln=True)
    pdf.cell(0, 8, f'Parcelas: {sale["installments"]}', ln=True)
    pdf.cell(0, 8, f'Valor por parcela: R$ {sale["installment_value"]:.2f}', ln=True)
    pdf.cell(0, 8, f'Forma de pagamento: {sale["payment_method"]}', ln=True)
    pdf.cell(0, 8, f'Status: {sale["status"]}', ln=True)
    pdf.ln(8)
    pdf.multi_cell(0, 8, 'Obrigado por escolher a MotoRent. Este comprovante confirma a venda e poderá ser usado como recibo fiscal sempre que necessário.')

    pdf_buffer = io.BytesIO(pdf.output(dest='S').encode('latin-1'))
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=f'receipt_{sale_id}.pdf')


@app.route('/faq')
@login_required
def faq():
    faqs = [
        {'question': 'Como faço uma reserva online?', 'answer': 'Vá até a página de Reservas, escolha o cliente, o veículo e o período desejado, e confirme a reserva.'},
        {'question': 'Como altero o status de um veículo?', 'answer': 'Acesse a página de Veículos e edite o registro do veículo para atualizar o status.'},
        {'question': 'Como recebo um recibo em PDF?', 'answer': 'No PDV, clique em PDF ao lado da venda para baixar o recibo.'},
        {'question': 'Como posso consultar o histórico do cliente?', 'answer': 'Abra o perfil do cliente na página de Clientes para ver pagamentos, multas e veículos associados.'},
        {'question': 'Como ativar o modo escuro?', 'answer': 'Use o botão de modo no canto superior para alternar entre tema claro e escuro. A escolha é lembrada automaticamente.'}
    ]
    return render_template('faq.html', title='FAQ', subtitle='Perguntas frequentes e suporte', faqs=faqs)


@app.route('/fines', methods=['GET', 'POST'])
@login_required
def fines():
    if request.method == 'POST':
        customer_id = int(request.form['customer_id'])
        vehicle_id = int(request.form['vehicle_id'])
        amount = float(request.form['amount'])
        description = request.form['description']
        date = request.form['date']
        points = int(request.form['points'])
        db = get_db()
        db.execute('INSERT INTO fines (customer_id, vehicle_id, amount, description, date, status, points) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (customer_id, vehicle_id, amount, description, date, 'pendente', points))
        db.commit()
        flash('Multa registrada com sucesso.')
        return redirect(url_for('fines'))

    customers = query_db('SELECT * FROM customers ORDER BY name')
    vehicles = query_db('SELECT * FROM vehicles ORDER BY model')
    raw_fines = query_db('SELECT f.*, c.name AS customer, v.model AS vehicle FROM fines f JOIN customers c ON f.customer_id = c.id JOIN vehicles v ON f.vehicle_id = v.id ORDER BY f.date DESC')
    fines_list = [dict(row) for row in raw_fines]
    return render_template('fines.html', title='Multas', subtitle='Gestão de infrações e pontos', customers=customers, vehicles=vehicles, fines=fines_list)


@app.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintenance():
    if request.method == 'POST':
        vehicle_id = int(request.form['vehicle_id'])
        last_service_date = request.form['last_service_date']
        next_service_date = request.form['next_service_date']
        predicted_cost = float(request.form['predicted_cost'])
        note = request.form['note']
        db = get_db()
        db.execute('INSERT INTO maintenance (vehicle_id, last_service_date, next_service_date, status, predicted_cost, note) VALUES (?, ?, ?, ?, ?, ?)',
                   (vehicle_id, last_service_date, next_service_date, 'programada', predicted_cost, note))
        db.commit()
        flash('Manutenção registrada com sucesso.')
        return redirect(url_for('maintenance'))

    vehicles = query_db('SELECT * FROM vehicles ORDER BY model')
    raw_maintenance = query_db('SELECT m.*, v.model AS vehicle, v.plate AS plate FROM maintenance m JOIN vehicles v ON m.vehicle_id = v.id ORDER BY m.next_service_date ASC')
    maintenance_list = [dict(row) for row in raw_maintenance]
    return render_template('maintenance.html', title='Manutenção', subtitle='Manutenção preventiva e preditiva', vehicles=vehicles, maintenance_list=maintenance_list)


@app.route('/telemetry')
@login_required
def telemetry():
    raw_telemetry = query_db('SELECT t.*, v.model AS vehicle FROM telemetry t JOIN vehicles v ON t.vehicle_id = v.id ORDER BY t.timestamp DESC')
    telemetry = [dict(row) for row in raw_telemetry]
    return render_template('telemetry.html', title='Telemetria', subtitle='Dados de localização e velocidade', telemetry=telemetry)


@app.route('/vehicle-inspection', methods=['GET', 'POST'])
@login_required
def vehicle_inspection():
    db = get_db()
    if request.method == 'POST':
        vehicle_id = int(request.form.get('vehicle_id', 0))
        inspection_type = request.form.get('inspection_type', 'entrada')
        condition = request.form.get('condition', 'bom')
        fuel_level = request.form.get('fuel_level', 'E')
        mileage = int(request.form.get('mileage', 0) or 0)
        notes = request.form.get('notes', '').strip()
        
        if not vehicle_id or mileage < 0:
            flash('Preencha os dados da vistoria corretamente.', 'error')
            return redirect(url_for('vehicle_inspection'))
        
        inspection_date = datetime.date.today().isoformat()
        created_at = datetime.datetime.now().isoformat()
        
        db.execute('INSERT INTO vehicle_inspection (vehicle_id, inspector_id, inspection_date, inspection_type, condition, fuel_level, mileage, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (vehicle_id, session.get('user_id'), inspection_date, inspection_type, condition, fuel_level, mileage, notes, created_at))
        db.commit()
        flash('Vistoria registrada com sucesso.')
        return redirect(url_for('vehicle_inspection'))
    
    vehicles = query_db('SELECT * FROM vehicles ORDER BY model')
    inspections = [dict(row) for row in query_db(
        'SELECT i.*, v.model AS vehicle, v.plate AS plate, u.username AS inspector_name FROM vehicle_inspection i '
        'JOIN vehicles v ON i.vehicle_id = v.id '
        'JOIN users u ON i.inspector_id = u.id '
        'ORDER BY i.inspection_date DESC LIMIT 50'
    )]
    
    return render_template('vehicle_inspection.html', title='Vistoria de Veículos', 
                         subtitle='Inspeção de entrada, saída e manutenção', 
                         vehicles=vehicles, inspections=inspections)


@app.route('/upload-document', methods=['GET', 'POST'])
@login_required
def upload_document():
    ocr_result = None
    if request.method == 'POST':
        owner_type = request.form.get('owner_type', '').strip()
        raw_owner = request.form.get('owner_id', '')
        doc_type = request.form.get('doc_type', '').strip()
        background_check = request.form.get('background_check', 'Não')
        file = request.files.get('file')

        try:
            owner_id = int(raw_owner.split(':')[-1]) if ':' in str(raw_owner) else int(raw_owner)
        except (ValueError, IndexError, TypeError, AttributeError):
            owner_id = None

        if owner_type not in ('customer', 'vehicle'):
            flash('Tipo de proprietário inválido.', 'error')
        elif owner_id is None or owner_id <= 0:
            flash('Selecione um proprietário válido.', 'error')
        elif not file or not file.filename:
            flash('Selecione um arquivo válido para upload.', 'error')
        else:
            filename = secure_filename(file.filename)
            if not allowed_file(filename):
                flash('Tipo de arquivo não permitido. Envie imagens ou PDF.', 'error')
            else:
                unique_name = f"{int(time.time())}_{filename}"
                destination = UPLOAD_FOLDER / unique_name
                file.save(destination)
                text = extract_text_from_file(destination)
                uploaded_at = datetime.datetime.utcnow().isoformat()
                db = get_db()
                db.execute('INSERT INTO documents (owner_type, owner_id, doc_type, filename, note, background_check, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (owner_type, owner_id, doc_type, unique_name, f'OCR: {text[:120]}', background_check, uploaded_at))
                db.commit()
                ocr_result = {'text': text}
                flash('Documento enviado com sucesso.')

    customers = query_db('SELECT * FROM customers ORDER BY name')
    vehicles = query_db('SELECT * FROM vehicles ORDER BY model')
    return render_template('upload.html', title='Documentos', subtitle='Upload com OCR inteligente', customers=customers, vehicles=vehicles, ocr_result=ocr_result)


@app.route('/background-check', methods=['GET', 'POST'])
@login_required
def background_check():
    background_result = None
    if request.method == 'POST':
        customer_id_raw = request.form.get('customer_id', '').strip()
        criminal_check = request.form.get('criminal_check', '').strip()
        customer_id = int(customer_id_raw) if customer_id_raw.isdigit() else 0

        if customer_id > 0:
            customer = query_db('SELECT * FROM customers WHERE id = ?', (customer_id,), one=True)
            if not customer:
                flash('Cliente não encontrado.', 'error')
            else:
                background_result = calculate_driver_score(customer_id)
                background_result['customer_name'] = customer['name']
                background_result['document'] = customer['document']
                background_result['search_term'] = criminal_check or customer['document']
                background_result['criminal_records'] = check_criminal_records(background_result['search_term'])
        elif criminal_check:
            criminal_records = check_criminal_records(criminal_check)
            background_result = {
                'customer_name': None,
                'document': None,
                'search_term': criminal_check,
                'risk_score': None,
                'status': 'Consulta sem cadastro',
                'recommendation': 'Busca de antecedentes realizada sem necessidade de cadastro do cliente.',
                'notes': [f'Consulta de antecedentes realizada para "{criminal_check}" sem cadastro de cliente.'],
                'criminal_records': criminal_records
            }
        else:
            flash('Selecione um cliente ou informe CPF/nome para consulta.', 'error')
    
    customers = query_db('SELECT * FROM customers ORDER BY name')
    return render_template('background_check.html', title='Background Check', subtitle='Avaliação de risco do condutor', customers=customers, background_result=background_result)


@app.route('/rental-history')
@login_required
def rental_history():
    rentals = [dict(row) for row in query_db(
        'SELECT r.*, c.name AS customer_name, c.email AS customer_email, v.brand AS vehicle_brand, v.model AS vehicle_model, v.plate AS vehicle_plate FROM reservations r '
        'JOIN customers c ON r.customer_id = c.id JOIN vehicles v ON r.vehicle_id = v.id ORDER BY r.start_date DESC'
    )]
    
    today = datetime.date.today().isoformat()
    upcoming = [r for r in rentals if r['end_date'] > today and r['status'] == 'confirmada']
    completed = [r for r in rentals if r['end_date'] <= today]
    
    stats = {
        'total_rentals': len(rentals),
        'upcoming_rentals': len(upcoming),
        'completed_rentals': len(completed)
    }
    
    return render_template('rental_history.html', title='Locações', subtitle='Histórico e gestão de locações de veículos', 
                         rentals=rentals, upcoming=upcoming, completed=completed, stats=stats)


@app.route('/payments', methods=['GET', 'POST'])
@login_required
def payments():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action', 'create')
        
        if action == 'create':
            customer_id = int(request.form.get('customer_id', 0))
            vehicle_id = int(request.form.get('vehicle_id', 0))
            amount = float(request.form.get('amount', 0) or 0)
            payment_method = request.form.get('payment_method', 'pix')
            installments = int(request.form.get('installments', 1))
            
            if not customer_id or not amount or amount <= 0:
                flash('Preencha os dados corretamente.', 'error')
                return redirect(url_for('payments'))
            
            if payment_method == 'pix':
                db.execute('INSERT INTO payments (customer_id, vehicle_id, amount, due_date, status, payment_method) VALUES (?, ?, ?, ?, ?, ?)',
                          (customer_id, vehicle_id, amount, datetime.date.today().isoformat(), 'pago', 'PIX'))
                flash(f'Pagamento de R$ {amount:.2f} via PIX registrado com sucesso!')
                
            elif payment_method == 'parceled':
                if installments < 2 or installments > 12:
                    flash('Parcelas devem estar entre 2 e 12.', 'error')
                    return redirect(url_for('payments'))
                
                installment_value = amount / installments
                for i in range(installments):
                    due_date = (datetime.date.today() + datetime.timedelta(days=30 * (i + 1))).isoformat()
                    db.execute('INSERT INTO payments (customer_id, vehicle_id, amount, due_date, status, payment_method) VALUES (?, ?, ?, ?, ?, ?)',
                              (customer_id, vehicle_id, installment_value, due_date, 'pendente', f'Parcelado ({i+1}/{installments})'))
                db.commit()
                flash(f'Parcelamento de R$ {amount:.2f} em {installments}x de R$ {installment_value:.2f} criado com sucesso!')
            
            elif payment_method == 'debit':
                db.execute('INSERT INTO payments (customer_id, vehicle_id, amount, due_date, status, payment_method) VALUES (?, ?, ?, ?, ?, ?)',
                          (customer_id, vehicle_id, amount, datetime.date.today().isoformat(), 'pago', 'Débito'))
                flash(f'Pagamento de R$ {amount:.2f} via débito registrado com sucesso!')
                
            else:
                db.execute('INSERT INTO payments (customer_id, vehicle_id, amount, due_date, status, payment_method) VALUES (?, ?, ?, ?, ?, ?)',
                          (customer_id, vehicle_id, amount, datetime.date.today().isoformat(), 'pago', 'Cartão'))
                flash(f'Pagamento de R$ {amount:.2f} via cartão registrado com sucesso!')
            
            db.commit()
            return redirect(url_for('payments'))
    
    customers = query_db('SELECT * FROM customers ORDER BY name')
    vehicles = query_db('SELECT * FROM vehicles ORDER BY model')
    
    total_payments = query_db('SELECT COUNT(*) AS count FROM payments', one=True)['count']
    paid_amount = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'pago'", one=True)['total'] or 0
    pending_amount = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'pendente'", one=True)['total'] or 0
    overdue_amount = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'atrasado'", one=True)['total'] or 0
    
    recent_payments = [dict(row) for row in query_db(
        'SELECT p.*, c.name AS customer_name, v.model AS vehicle_model FROM payments p '
        'JOIN customers c ON p.customer_id = c.id LEFT JOIN vehicles v ON p.vehicle_id = v.id '
        'ORDER BY p.id DESC LIMIT 20'
    )]
    
    payment_methods = [dict(row) for row in query_db(
        "SELECT payment_method, COUNT(*) AS count, SUM(amount) AS total FROM payments GROUP BY payment_method"
    )]
    
    return render_template('payments.html', title='Pagamentos', subtitle='Integração com PIX, cartão e parcelamento',
                         customers=customers, vehicles=vehicles,
                         total_payments=total_payments, paid_amount=paid_amount, 
                         pending_amount=pending_amount, overdue_amount=overdue_amount,
                         recent_payments=recent_payments, payment_methods=payment_methods)


@app.route('/integrations')
@login_required
def integrations():
    return render_template('integrations.html', title='Integrações', subtitle='Google Maps, Waze e outras plataformas')


@app.route('/manifest.json')
def manifest():
    return send_from_directory(app.static_folder, 'manifest.json')


@app.route('/service-worker.js')
def service_worker():
    return send_from_directory(app.static_folder, 'service-worker.js')


@app.route('/offline')
def offline():
    return render_template('offline.html', title='Offline', subtitle='Você está sem conexão')


@app.route('/users', methods=['GET', 'POST'])
@admin_required
def users():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')
            if not username or not email or not password:
                flash('Preencha todos os campos do novo usuário.')
            elif query_db('SELECT id FROM users WHERE username = ?', (username,), one=True):
                flash('Nome de usuário já existe.')
            else:
                password_hash = generate_password_hash(password)
                db = get_db()
                db.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                           (username, email, password_hash, role or 'operator'))
                db.commit()
                flash('Usuário criado com sucesso.')
        elif action == 'update_role':
            user_id = int(request.form.get('user_id'))
            role = request.form.get('role')
            if user_id and role:
                db = get_db()
                db.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
                db.commit()
                flash('Função do usuário atualizada.')
        return redirect(url_for('users'))

    raw_users = query_db('SELECT id, username, email, role FROM users ORDER BY username')
    users = [dict(row) for row in raw_users]
    return render_template('users.html', title='Usuários', subtitle='Gerenciamento de acessos', users=users)


@app.route('/admin')
@admin_required
def admin():
    total_users = query_db('SELECT COUNT(*) AS count FROM users', one=True)['count']
    total_customers = query_db('SELECT COUNT(*) AS count FROM customers', one=True)['count']
    total_vehicles = query_db('SELECT COUNT(*) AS count FROM vehicles', one=True)['count']
    total_payments = query_db('SELECT COUNT(*) AS count FROM payments', one=True)['count']
    active_payments = query_db("SELECT COUNT(*) AS count FROM payments WHERE status = 'pago'", one=True)['count']
    pending_payments = query_db("SELECT COUNT(*) AS count FROM payments WHERE status = 'atrasado'", one=True)['count']
    total_fines = query_db('SELECT COUNT(*) AS count FROM fines', one=True)['count']
    total_maintenance = query_db('SELECT COUNT(*) AS count FROM maintenance', one=True)['count']
    role_counts = [dict(row) for row in query_db('SELECT role, COUNT(*) AS count FROM users GROUP BY role')]
    recent_users = [dict(row) for row in query_db('SELECT id, username, email, role FROM users ORDER BY id DESC LIMIT 5')]
    return render_template('admin.html', title='Admin', subtitle='Painel de administração', total_users=total_users, total_customers=total_customers, total_vehicles=total_vehicles, total_payments=total_payments, active_payments=active_payments, pending_payments=pending_payments, total_fines=total_fines, total_maintenance=total_maintenance, role_counts=role_counts, recent_users=recent_users)


@app.route('/finance', methods=['GET', 'POST'])
@roles_required('admin', 'operator')
def finance():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action', 'create_payment')
        if action == 'create_payment':
            customer_id = int(request.form.get('customer_id', 0))
            vehicle_id = int(request.form.get('vehicle_id', 0))
            amount = float(request.form.get('amount', 0) or 0)
            due_date = request.form.get('due_date', '')
            status = request.form.get('status', 'pendente')
            if session.get('role') != 'admin':
                status = 'pendente'
            payment_method = request.form.get('payment_method', 'Boleto')
            
            if not customer_id or not vehicle_id or not due_date or amount <= 0:
                flash('Preencha todos os campos obrigatórios com valores válidos.', 'error')
                return redirect(url_for('finance'))

            try:
                due_date_obj = datetime.datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de vencimento inválida. Use o formato AAAA-MM-DD.', 'error')
                return redirect(url_for('finance'))

            if status == 'pendente' and due_date_obj <= datetime.date.today():
                flash('Pagamentos pendentes devem ter data de vencimento no futuro.', 'error')
                return redirect(url_for('finance'))

            allowed_statuses = ['pago', 'pendente', 'atrasado']
            if status not in allowed_statuses:
                status = 'pendente'

            db.execute('INSERT INTO payments (customer_id, vehicle_id, amount, due_date, status, payment_method) VALUES (?, ?, ?, ?, ?, ?)',
                       (customer_id, vehicle_id, amount, due_date, status, payment_method))
            db.commit()
            flash('Pagamento registrado com sucesso.')
            return redirect(url_for('finance'))
        elif action == 'correct_payment':
            if session.get('role') != 'admin':
                flash('Apenas administradores podem corrigir pagamentos.', 'error')
                return redirect(url_for('finance'))

            payment_id = int(request.form.get('payment_id', 0))
            new_status = request.form.get('status', 'pendente')
            new_amount = request.form.get('amount')
            correction_note = request.form.get('correction_note', '').strip() or 'Correção manual pelo administrador.'

            if not payment_id or new_status not in ['pago', 'pendente', 'atrasado']:
                flash('Selecione um pagamento válido e informe o novo status.', 'error')
                return redirect(url_for('finance'))

            payment = query_db('SELECT * FROM payments WHERE id = ?', (payment_id,), one=True)
            if not payment:
                flash('Pagamento não encontrado.', 'error')
                return redirect(url_for('finance'))

            try:
                due_date_obj = datetime.datetime.strptime(payment['due_date'], '%Y-%m-%d').date()
            except ValueError:
                flash('Data de vencimento inválida no pagamento selecionado.', 'error')
                return redirect(url_for('finance'))

            if new_amount is not None and new_amount != '':
                try:
                    new_amount = float(new_amount)
                except ValueError:
                    flash('Valor inválido para o pagamento.', 'error')
                    return redirect(url_for('finance'))
                if new_amount <= 0:
                    flash('O valor do pagamento deve ser maior que zero.', 'error')
                    return redirect(url_for('finance'))
            else:
                new_amount = payment['amount']

            if new_status == 'pendente' and due_date_obj <= datetime.date.today():
                flash('Não é permitido deixar parcelas pendentes com data de vencimento passada.', 'error')
                return redirect(url_for('finance'))

            old_amount = payment['amount']
            old_status = payment['status']

            db.execute('UPDATE payments SET amount = ?, status = ? WHERE id = ?', (new_amount, new_status, payment_id))
            db.execute('INSERT INTO payment_audit (payment_id, changed_by, changed_at, old_status, new_status, old_amount, new_amount, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (payment_id, session.get('user_id'), datetime.datetime.now().isoformat(), old_status, new_status, old_amount, new_amount, correction_note))
            db.commit()
            flash('Pagamento corrigido e auditado com sucesso.')
            return redirect(url_for('finance'))

    total_income = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'pago'", one=True)['total'] or 0
    overdue_amount = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'atrasado'", one=True)['total'] or 0
    pending_fine_total = query_db("SELECT SUM(amount) AS total FROM fines WHERE status = 'pendente'", one=True)['total'] or 0
    pending_fine_count = query_db("SELECT COUNT(*) AS count FROM fines WHERE status = 'pendente'", one=True)['count']
    upcoming_maintenance = query_db("SELECT COUNT(*) AS count FROM maintenance WHERE next_service_date >= date('now') AND next_service_date <= date('now', '+30 day')", one=True)['count']
    total_vehicles = query_db('SELECT COUNT(*) AS count FROM vehicles', one=True)['count']
    overdue_debtors = query_db("SELECT COUNT(DISTINCT customer_id) AS count FROM payments WHERE status = 'atrasado'", one=True)['count']
    payment_method_counts = [dict(row) for row in query_db("SELECT COALESCE(payment_method, 'Desconhecido') AS payment_method, COUNT(*) AS count FROM payments GROUP BY payment_method")]
    
    # Alertas de vencimento
    today = datetime.date.today()
    upcoming_due = query_db("SELECT COUNT(*) AS count FROM payments WHERE status IN ('pendente', 'atrasado') AND due_date >= date('now') AND due_date <= date('now', '+7 day')", one=True)['count']
    overdue = query_db("SELECT COUNT(*) AS count FROM payments WHERE due_date < date('now') AND status != 'pago'", one=True)['count']
    
    payments = [dict(row) for row in query_db('SELECT p.*, c.name AS customer, c.id AS customer_id, v.model AS vehicle, v.plate AS plate FROM payments p JOIN customers c ON p.customer_id = c.id JOIN vehicles v ON p.vehicle_id = v.id ORDER BY p.due_date DESC LIMIT 20')]
    
    # Adicionar status de alerta a cada pagamento
    for payment in payments:
        payment['alert_status'] = None
        if payment['status'] != 'pago':
            payment_date = datetime.datetime.strptime(payment['due_date'], '%Y-%m-%d').date()
            days_until = (payment_date - today).days
            if days_until < 0:
                payment['alert_status'] = 'vencido'
            elif days_until <= 7:
                payment['alert_status'] = 'prestes_vencer'
    
    overdue_payments = [dict(row) for row in query_db('SELECT p.*, c.name AS customer, v.model AS vehicle FROM payments p JOIN customers c ON p.customer_id = c.id JOIN vehicles v ON p.vehicle_id = v.id WHERE p.status = "atrasado" ORDER BY p.due_date DESC')]
    client_options = [dict(row) for row in query_db('SELECT DISTINCT c.id, c.name FROM customers c ORDER BY c.name')]
    vehicles_options = [dict(row) for row in query_db('SELECT id, model, plate FROM vehicles ORDER BY model')]
    correction_payments = [dict(row) for row in query_db(
        'SELECT p.id, c.name AS customer, v.model AS vehicle, p.amount, p.due_date, p.status FROM payments p '
        'JOIN customers c ON p.customer_id = c.id JOIN vehicles v ON p.vehicle_id = v.id '
        'ORDER BY p.due_date DESC LIMIT 50'
    )]
    payment_audit_logs = [dict(row) for row in query_db(
        'SELECT a.*, u.username AS changed_by_name FROM payment_audit a LEFT JOIN users u ON a.changed_by = u.id ORDER BY a.changed_at DESC LIMIT 15'
    )]
    revenue_history = [dict(row) for row in query_db("SELECT strftime('%Y-%m', due_date) AS month, SUM(amount) AS total FROM payments WHERE status = 'pago' GROUP BY month ORDER BY month DESC LIMIT 6")]
    assets_value = total_vehicles * 12000
    liabilities = overdue_amount + pending_fine_total
    
    return render_template(
        'finance.html',
        title='Financeiro',
        subtitle='Finanças da empresa, faturamento e indicadores',
        total_income=total_income,
        overdue_amount=overdue_amount,
        pending_fine_total=pending_fine_total,
        pending_fine_count=pending_fine_count,
        upcoming_maintenance=upcoming_maintenance,
        total_vehicles=total_vehicles,
        overdue_debtors=overdue_debtors,
        payment_method_counts=payment_method_counts,
        payments=payments,
        overdue_payments=overdue_payments,
        client_options=client_options,
        vehicles_options=vehicles_options,
        correction_payments=correction_payments,
        payment_audit_logs=payment_audit_logs,
        revenue_history=revenue_history,
        assets_value=assets_value,
        liabilities=liabilities,
        upcoming_due=upcoming_due,
        overdue=overdue
    )


@app.route('/api/dashboard')
@login_required
def dashboard_api():
    total_clients = query_db('SELECT COUNT(*) AS count FROM customers', one=True)['count']
    total_vehicles = query_db('SELECT COUNT(*) AS count FROM vehicles', one=True)['count']
    active_rentals = query_db("SELECT COUNT(*) AS count FROM vehicles WHERE status = 'alugado'", one=True)['count']
    overdue_payments = query_db("SELECT COUNT(*) AS count FROM payments WHERE status = 'atrasado'", one=True)['count']
    total_income = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'pago'", one=True)['total'] or 0
    pending_fines = query_db("SELECT COUNT(*) AS count FROM fines WHERE status = 'pendente'", one=True)['count']
    upcoming_maintenance = query_db("SELECT COUNT(*) AS count FROM maintenance WHERE next_service_date <= date('now', '+30 day')", one=True)['count']
    overdue_debtors = query_db("SELECT COUNT(DISTINCT customer_id) AS count FROM payments WHERE status = 'atrasado'", one=True)['count']
    predicted_revenue = query_db("SELECT SUM(amount) AS total FROM payments WHERE due_date >= date('now')", one=True)['total'] or 0

    vehicles = [dict(row) for row in query_db('SELECT * FROM vehicles ORDER BY id DESC LIMIT 6')]
    payments = [dict(row) for row in query_db('SELECT p.id, c.name AS customer, v.model AS vehicle, p.amount, p.due_date, p.status FROM payments p JOIN customers c ON p.customer_id = c.id JOIN vehicles v ON p.vehicle_id = v.id ORDER BY p.due_date DESC LIMIT 6')]
    clients = [dict(row) for row in query_db('SELECT * FROM customers ORDER BY id DESC LIMIT 6')]

    locations = [
        {
            'vehicle': row['model'],
            'lat': row['latitude'],
            'lng': row['longitude'],
            'status': row['status']
        }
        for row in query_db('SELECT model, latitude, longitude, status FROM vehicles')
    ]

    rent_to_own = [
        {'month': f'Mês {i}', 'value': 1000 + i * 200}
        for i in range(1, 7)
    ]

    status_distribution = [
        {'label': 'Alugado', 'value': query_db("SELECT COUNT(*) AS count FROM vehicles WHERE status = 'alugado'", one=True)['count']},
        {'label': 'Disponível', 'value': query_db("SELECT COUNT(*) AS count FROM vehicles WHERE status = 'disponível'", one=True)['count']},
        {'label': 'Em manutenção', 'value': query_db("SELECT COUNT(*) AS count FROM vehicles WHERE status = 'manutenção'", one=True)['count']}
    ]

    return jsonify({
        'summary': {
            'totalClients': total_clients,
            'totalVehicles': total_vehicles,
            'activeRentals': active_rentals,
            'overduePayments': overdue_payments,
            'totalIncome': total_income,
            'pendingFines': pending_fines,
            'upcomingMaintenance': upcoming_maintenance,
            'predictedRevenue': predicted_revenue,
            'overdueDebtors': overdue_debtors
        },
        'vehicles': vehicles,
        'payments': payments,
        'clients': clients,
        'locations': locations,
        'rentToOwn': rent_to_own,
        'statusDistribution': status_distribution
    })


@app.route('/api/payments/customer/<int:customer_id>')
@login_required
def customer_payments_api(customer_id):
    rows = query_db(
        'SELECT p.*, v.model AS vehicle FROM payments p JOIN vehicles v ON p.vehicle_id = v.id WHERE p.customer_id = ? ORDER BY p.due_date DESC',
        (customer_id,)
    )
    return jsonify([dict(row) for row in rows])


@app.route('/api/telemetry')
@login_required
def telemetry_api():
    rows = query_db('SELECT t.*, v.model AS vehicle FROM telemetry t JOIN vehicles v ON t.vehicle_id = v.id ORDER BY t.timestamp DESC')
    return jsonify([dict(row) for row in rows])


@app.route('/export/payments')
@login_required
def export_payments():
    rows = query_db('SELECT p.id, c.name AS customer, v.model AS vehicle, p.amount, p.due_date, p.status FROM payments p JOIN customers c ON p.customer_id = c.id JOIN vehicles v ON p.vehicle_id = v.id ORDER BY p.due_date DESC')
    lines = ['ID,Cliente,Veículo,Valor,Vencimento,Status']
    for row in rows:
        escaped = [
            f'"{str(row[k]).replace("\"", "\"\"")}"' if row[k] is not None else ''
            for k in ['id', 'customer', 'vehicle', 'amount', 'due_date', 'status']
        ]
        lines.append(','.join(escaped))
    csv_data = '\n'.join(lines)
    return app.response_class(csv_data, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=relatorio_financeiro.csv'})


@app.route('/api/customers', methods=['GET', 'POST'])
@login_required
def customers_api():
    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        name = (payload.get('name') or '').strip()
        document = (payload.get('document') or '').strip()
        email = (payload.get('email') or '').strip()
        phone = (payload.get('phone') or '').strip()
        if not name or not document:
            return jsonify({'error': 'Nome e documento são obrigatórios.'}), 400
        
        if email and query_db('SELECT id FROM customers WHERE email = ?', (email,), one=True):
            return jsonify({'error': 'Email já está registrado.'}), 400
        
        if phone and query_db('SELECT id FROM customers WHERE phone = ?', (phone,), one=True):
            return jsonify({'error': 'Telefone já está registrado.'}), 400
        
        try:
            score = int(payload.get('score', 650) or 650)
        except (TypeError, ValueError):
            score = 650
        db = get_db()
        db.execute('INSERT INTO customers (name, document, email, phone, score) VALUES (?, ?, ?, ?, ?)',
                   (name, document, email, phone, score))
        db.commit()
        return jsonify({'status': 'ok'})

    rows = query_db('SELECT * FROM customers ORDER BY name')
    return jsonify([dict(row) for row in rows])


@app.route('/api/vehicles', methods=['GET', 'POST'])
@login_required
def vehicles_api():
    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        model = (payload.get('model') or '').strip()
        plate = (payload.get('plate') or '').strip()
        status = payload.get('status')
        insurance = payload.get('insurance')
        try:
            owner_id = int(payload.get('owner_id') or 0)
        except (TypeError, ValueError):
            owner_id = 0
        if not model or not plate:
            return jsonify({'error': 'Modelo e placa são obrigatórios.'}), 400
        db = get_db()
        db.execute('INSERT INTO vehicles (model, plate, status, insurance, latitude, longitude, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (model, plate, status, insurance, -23.55, -46.63, owner_id if owner_id > 0 else None))
        db.commit()
        return jsonify({'status': 'ok'})

    rows = query_db('SELECT * FROM vehicles ORDER BY model')
    return jsonify([dict(row) for row in rows])


@app.route('/api/documents', methods=['POST'])
@login_required
def documents_api():
    owner_type = request.form.get('owner_type')
    raw_owner = request.form.get('owner_id')
    doc_type = request.form.get('doc_type')
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    try:
        owner_id = int(raw_owner.split(':')[-1])
    except Exception:
        owner_id = None

    if owner_type not in ('customer', 'vehicle'):
        return jsonify({'error': 'Tipo de proprietário inválido'}), 400

    if owner_id is None or owner_id <= 0:
        return jsonify({'error': 'Proprietário inválido'}), 400

    filename = secure_filename(file.filename)
    if not filename or not allowed_file(filename):
        return jsonify({'error': 'Tipo de arquivo inválido'}), 400

    unique_name = f"{int(time.time())}_{filename}"
    destination = UPLOAD_FOLDER / unique_name
    file.save(destination)
    text = extract_text_from_file(destination)
    db = get_db()
    db.execute('INSERT INTO documents (owner_type, owner_id, doc_type, filename, note) VALUES (?, ?, ?, ?, ?)',
               (owner_type, owner_id, doc_type, unique_name, f'OCR: {text[:120]}'))
    db.commit()
    return jsonify({'text': text})


@app.route('/api/background-check', methods=['POST'])
@login_required
def background_check_api():
    payload = request.get_json(silent=True) or {}
    try:
        customer_id = int(payload.get('customer_id', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Cliente inválido'}), 400
    result = calculate_driver_score(customer_id)
    if not result:
        return jsonify({'error': 'Cliente não encontrado'}), 404
    return jsonify(result)


@app.route('/api/theme', methods=['POST'])
@login_required
def theme_api():
    payload = request.get_json(silent=True) or {}
    theme = payload.get('theme', 'light')
    if theme in ['light', 'dark']:
        session['theme'] = theme
        return jsonify({'success': True, 'theme': theme})
    return jsonify({'error': 'Tema inválido'}), 400


@app.route('/api/address/cep/<cep>')
def address_api(cep):
    """Consulta endereço via API ViaCEP"""
    try:
        cep_clean = ''.join(filter(str.isdigit, cep))
        if len(cep_clean) != 8:
            return jsonify({'error': 'CEP inválido'}), 400
        
        url = f'https://viacep.com.br/ws/{cep_clean}/json/'
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if 'erro' in data:
            return jsonify({'error': 'CEP não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'street': data.get('logradouro', ''),
            'neighborhood': data.get('bairro', ''),
            'city': data.get('localidade', ''),
            'state': data.get('uf', '')
        })
    except urllib.error.URLError:
        return jsonify({'error': 'Erro ao consultar CEP'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ===== NOVAS ROTAS PARA FUNCIONALIDADES SOLICITADAS =====

@app.route('/api/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Deleta um usuário do sistema (apenas admin)"""
    db = get_db()
    user = query_db('SELECT id FROM users WHERE id = ?', (user_id,), one=True)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Não permitir deletar o próprio admin
    if user_id == session.get('user_id'):
        return jsonify({'error': 'Não é possível deletar sua própria conta'}), 400
    
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    return jsonify({'status': 'ok', 'message': 'Usuário deletado com sucesso'})


@app.route('/api/admin/reset-health', methods=['POST'])
@admin_required
def reset_admin_health():
    """Reseta as métricas de saúde administrativa"""
    db = get_db()
    
    # Zerar as métricas limpando dados ou atualizando status
    db.execute("UPDATE payments SET status = 'pendente' WHERE status = 'atrasado'")
    db.execute('DELETE FROM fines')
    db.execute('DELETE FROM maintenance')
    
    db.commit()
    return jsonify({
        'status': 'ok', 
        'message': 'Saúde administrativa resetada com sucesso',
        'zeroed_items': {
            'overdue_payments': 'resetados para pendente',
            'fines': 'removidas',
            'maintenance': 'removidas'
        }
    })


@app.route('/export/inspection/<int:inspection_id>')
@login_required
def export_inspection_pdf(inspection_id):
    """Exporta um relatório de vistoria em PDF"""
    inspection = query_db(
        'SELECT i.*, v.model, v.plate, v.brand, u.username AS inspector_name FROM vehicle_inspection i '
        'JOIN vehicles v ON i.vehicle_id = v.id '
        'JOIN users u ON i.inspector_id = u.id '
        'WHERE i.id = ?',
        (inspection_id,), one=True
    )
    
    if not inspection:
        abort(404)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Relatório de Vistoria de Veículo', ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.ln(4)
    
    # Informações da vistoria
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, 'Dados da Vistoria', ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f'ID da Vistoria: {inspection_id}', ln=True)
    pdf.cell(0, 7, f'Data: {inspection["inspection_date"]}', ln=True)
    pdf.cell(0, 7, f'Inspetor: {inspection["inspector_name"]}', ln=True)
    pdf.cell(0, 7, f'Tipo de Vistoria: {inspection["inspection_type"].replace("_", " ").title()}', ln=True)
    pdf.ln(4)
    
    # Informações do veículo
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, 'Dados do Veículo', ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f'Marca/Modelo: {inspection["brand"]} {inspection["model"]}', ln=True)
    pdf.cell(0, 7, f'Placa: {inspection["plate"]}', ln=True)
    pdf.cell(0, 7, f'Quilometragem: {inspection["mileage"]} km', ln=True)
    pdf.cell(0, 7, f'Nível de Combustível: {inspection["fuel_level"]}/F', ln=True)
    pdf.ln(4)
    
    # Condições
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, 'Condições Gerais', ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f'Condição Geral: {inspection["condition"].title()}', ln=True)
    pdf.ln(4)
    
    # Observações
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, 'Observações', ln=True)
    pdf.set_font('Arial', '', 10)
    observations = inspection["notes"] or "Nenhuma observação registrada"
    pdf.multi_cell(0, 7, observations)
    pdf.ln(4)
    
    # Rodapé
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 7, f'Relatório gerado em {datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', ln=True)
    pdf.cell(0, 7, 'MotoRent - Sistema de Gerenciamento de Frota', ln=True)
    
    pdf_buffer = io.BytesIO(pdf.output(dest='S').encode('latin-1'))
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=f'vistoria_{inspection_id}.pdf')


@app.route('/export/finance-pdf')
@login_required
def export_finance_pdf():
    """Exporta relatório financeiro em PDF"""
    total_income = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'pago'", one=True)['total'] or 0
    overdue_amount = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'atrasado'", one=True)['total'] or 0
    pending_amount = query_db("SELECT SUM(amount) AS total FROM payments WHERE status = 'pendente'", one=True)['total'] or 0
    total_payments = query_db('SELECT COUNT(*) AS count FROM payments', one=True)['count']
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Relatório Financeiro MotoRent', ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.ln(4)
    
    # Resumo financeiro
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, 'Resumo Financeiro', ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f'Receita Paga: R$ {total_income:,.2f}', ln=True)
    pdf.cell(0, 7, f'Valores em Atraso: R$ {overdue_amount:,.2f}', ln=True)
    pdf.cell(0, 7, f'Valores Pendentes: R$ {pending_amount:,.2f}', ln=True)
    pdf.cell(0, 7, f'Total de Pagamentos: {total_payments}', ln=True)
    pdf.ln(4)
    
    # Histórico de pagamentos
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, 'Histórico de Pagamentos (últimos 20)', ln=True)
    pdf.set_font('Arial', '', 9)
    
    payments_rows = query_db('SELECT p.id, p.customer_id, p.vehicle_id, p.amount, p.due_date, p.status, p.payment_method, c.name AS customer, v.model AS vehicle FROM payments p JOIN customers c ON p.customer_id = c.id JOIN vehicles v ON p.vehicle_id = v.id ORDER BY p.due_date DESC LIMIT 20')
    payments = [dict(row) for row in payments_rows]
    
    # Cabeçalho da tabela
    pdf.cell(30, 6, 'Data', border=1)
    pdf.cell(50, 6, 'Cliente', border=1)
    pdf.cell(40, 6, 'Veículo', border=1)
    pdf.cell(25, 6, 'Valor', border=1)
    pdf.cell(25, 6, 'Status', border=1)
    pdf.ln()
    
    # Dados da tabela
    for payment in payments:
        pdf.cell(30, 6, payment['due_date'][:10], border=1)
        pdf.cell(50, 6, payment['customer'][:15], border=1)
        pdf.cell(40, 6, payment['vehicle'][:12], border=1)
        pdf.cell(25, 6, f"R$ {payment['amount']:.2f}", border=1)
        pdf.cell(25, 6, payment['status'][:8], border=1)
        pdf.ln()
    
    pdf.ln(4)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 7, f'Relatório gerado em {datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', ln=True)
    
    pdf_buffer = io.BytesIO(pdf.output(dest='S').encode('latin-1'))
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='relatorio_financeiro.pdf')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(debug=debug, port=port, host='0.0.0.0')
    