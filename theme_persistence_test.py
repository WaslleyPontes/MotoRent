import requests
from bs4 import BeautifulSoup

base_url = 'http://127.0.0.1:5000'
session = requests.Session()

# Obter página de login para csrf
login_page = session.get(f'{base_url}/login', timeout=10)
print('Login GET status:', login_page.status_code)

soup = BeautifulSoup(login_page.text, 'html.parser')
csrf_meta = soup.find('meta', {'name': 'csrf-token'})
csrf_input = soup.find('input', {'name': 'csrf_token'})
print('CSRF meta present:', bool(csrf_meta))
print('CSRF input present:', bool(csrf_input))

csrf_token = None
if csrf_input:
    csrf_token = csrf_input.get('value')
elif csrf_meta:
    csrf_token = csrf_meta.get('content')

print('CSRF token length:', len(csrf_token) if csrf_token else 'none')

login_resp = session.post(
    f'{base_url}/login',
    data={'username': 'admin', 'password': 'admin123', 'csrf_token': csrf_token},
    allow_redirects=False,
    timeout=10,
)
print('Login POST status:', login_resp.status_code)
print('Login Location:', login_resp.headers.get('Location'))

# Toggle theme to dark
theme_resp = session.post(
    f'{base_url}/api/theme',
    json={'theme': 'dark'},
    headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf_meta.get('content') if csrf_meta else csrf_token},
    allow_redirects=False,
    timeout=10,
)
print('Theme POST status:', theme_resp.status_code)
print('Theme response:', theme_resp.text)

# Get home page and inspect body class
home = session.get(f'{base_url}/', timeout=10)
print('Home GET status:', home.status_code)
body_class = BeautifulSoup(home.text, 'html.parser').body.get('class')
print('Home body class:', body_class)

# Get another page to ensure persistence
customers = session.get(f'{base_url}/customers', timeout=10)
print('Customers GET status:', customers.status_code)
body_class_customers = BeautifulSoup(customers.text, 'html.parser').body.get('class')
print('Customers body class:', body_class_customers)
