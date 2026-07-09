from app import app

client = app.test_client()

# GET login page
login_page = client.get('/login')
print('GET /login', login_page.status_code)
html = login_page.get_data(as_text=True)
import re
m = re.search(r'name="csrf_token" value="([^"]+)"', html)
token = m.group(1) if m else ''
print('csrf token present', bool(token))

# Login
login_resp = client.post('/login', data={'username':'admin','password':'admin123','csrf_token':token}, follow_redirects=True)
print('POST /login', login_resp.status_code, login_resp.request.path)
print('contains dashboard', 'Dashboard' in login_resp.get_data(as_text=True))

# Main routes
for path in ['/', '/customers', '/vehicles', '/reservations', '/pos', '/finance', '/payments', '/fines', '/maintenance', '/telemetry', '/upload-document', '/background-check', '/integrations', '/faq', '/users', '/admin']:
    resp = client.get(path)
    print(path, resp.status_code)
