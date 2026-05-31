import re
import sys
from urllib.parse import urljoin

import requests

BASE_URL = 'http://localhost:5000'
USERNAME = 'testuser'
PASSWORD = 'Teste1234'
EMAIL = 'testuser@motorent.com'

CUSTOMER_DATA = {
    'name': 'João Silva',
    'document_type': 'CPF',
    'document': '123.456.789-01',
    'email': 'joao.silva@motorent.com',
    'phone': '(85) 99999-0001',
    'phone2': '(85) 98888-0001',
    'score': '750',
    'internal_notes': 'Cliente de teste automático',
    'cep': '60840-000',
    'street': 'Av. República',
    'number': '150',
    'neighborhood': 'Meireles',
    'city': 'Fortaleza',
    'state': 'CE',
    'complement': '',
}

VEHICLE_DATA = {
    'brand': 'Yamaha',
    'model': 'Yamaha Crosser Z ABS',
    'plate': 'LSK9M12',
    'color': 'Branco',
    'status': 'disponível',
    'insurance': 'Seguro Ativo',
    'owner_id': '',
}


def parse_csrf(html):
    match = re.search(r'<meta[^>]+name="csrf-token"[^>]+content="([^"]+)"', html)
    return match.group(1) if match else None


def extract_row_id(html, unique_token):
    rows = re.findall(r'<tr>(.*?)</tr>', html, flags=re.S)
    for row in rows:
        if unique_token in row:
            match = re.search(r'data-id="(\d+)"', row)
            if match:
                return match.group(1)
    return None


def get_available_vehicle_id(html):
    rows = re.findall(r'<tr>(.*?)</tr>', html, flags=re.S)
    for row in rows:
        if 'disponível' in row and 'Yamaha Crosser Z ABS' in row:
            match = re.search(r'data-id="(\d+)"', row)
            if match:
                return match.group(1)
    return None


def login(session):
    response = session.get(urljoin(BASE_URL, '/login'))
    response.raise_for_status()
    token = parse_csrf(response.text)
    if not token:
        print('Falha ao obter CSRF token em /login')
        return False

    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrf_token': token,
    }
    response = session.post(urljoin(BASE_URL, '/login'), data=payload)
    return response.url.rstrip('/') != urljoin(BASE_URL, '/login').rstrip('/')


def register(session):
    response = session.get(urljoin(BASE_URL, '/register'))
    response.raise_for_status()
    token = parse_csrf(response.text)
    if not token:
        print('Falha ao obter CSRF token em /register')
        return False

    payload = {
        'username': USERNAME,
        'email': EMAIL,
        'password': PASSWORD,
        'csrf_token': token,
    }
    response = session.post(urljoin(BASE_URL, '/register'), data=payload)
    return response.status_code in (200, 302)


def create_customer(session):
    response = session.get(urljoin(BASE_URL, '/customers'))
    response.raise_for_status()
    token = parse_csrf(response.text)
    if not token:
        raise RuntimeError('CSRF token não encontrado em /customers')

    payload = {
        'action': 'create',
        'csrf_token': token,
        **CUSTOMER_DATA,
    }
    response = session.post(urljoin(BASE_URL, '/customers'), data=payload)
    response.raise_for_status()
    return 'Cliente cadastrado com sucesso' in response.text or response.url.endswith('/customers')


def create_vehicle(session):
    response = session.get(urljoin(BASE_URL, '/vehicles'))
    response.raise_for_status()
    token = parse_csrf(response.text)
    if not token:
        raise RuntimeError('CSRF token não encontrado em /vehicles')

    payload = {
        'action': 'create',
        'csrf_token': token,
        **VEHICLE_DATA,
    }
    response = session.post(urljoin(BASE_URL, '/vehicles'), data=payload)
    response.raise_for_status()
    return 'Veículo registrado com sucesso' in response.text or response.url.endswith('/vehicles')


def update_customer(session, customer_id):
    response = session.get(urljoin(BASE_URL, '/customers'))
    response.raise_for_status()
    token = parse_csrf(response.text)
    if not token:
        raise RuntimeError('CSRF token não encontrado em /customers')

    updated = dict(CUSTOMER_DATA)
    updated['phone2'] = '(85) 98888-0011'
    updated['action'] = 'update'
    updated['customer_id'] = customer_id
    updated['csrf_token'] = token

    response = session.post(urljoin(BASE_URL, '/customers'), data=updated)
    response.raise_for_status()
    return 'Cliente atualizado com sucesso' in response.text or response.url.endswith('/customers')


def delete_vehicle(session, vehicle_id):
    response = session.get(urljoin(BASE_URL, '/vehicles'))
    response.raise_for_status()
    token = parse_csrf(response.text)
    if not token:
        raise RuntimeError('CSRF token não encontrado em /vehicles')

    payload = {
        'action': 'delete',
        'vehicle_id': vehicle_id,
        'csrf_token': token,
    }
    response = session.post(urljoin(BASE_URL, '/vehicles'), data=payload)
    response.raise_for_status()
    return 'Veículo excluído com sucesso' in response.text or response.url.endswith('/vehicles')


def ensure_logged_in(session):
    if login(session):
        print('Login efetuado com sucesso.')
        return True
    print('Login falhou. Tentando registrar usuário...')
    if not register(session):
        print('Falha ao registrar usuário de teste. Verifique a aplicação.')
        return False
    if login(session):
        print('Login efetuado após registro.')
        return True
    print('Falha no login mesmo após registro.')
    return False


def main():
    session = requests.Session()
    session.headers.update({'User-Agent': 'MotoRent-Test-Agent/1.0'})

    if not ensure_logged_in(session):
        sys.exit(1)

    print('Criando cliente de teste...')
    if not create_customer(session):
        print('Falha ao criar cliente.')
        sys.exit(1)
    print('Cliente criado com sucesso.')

    customers_page = session.get(urljoin(BASE_URL, '/customers'))
    customer_id = extract_row_id(customers_page.text, CUSTOMER_DATA['email'])
    if not customer_id:
        print('Não foi possível localizar o cliente criado.')
        sys.exit(1)
    print(f'Cliente criado com id: {customer_id}')

    print('Atualizando cliente de teste...')
    if not update_customer(session, customer_id):
        print('Falha ao atualizar cliente.')
        sys.exit(1)
    print('Cliente atualizado com sucesso.')

    print('Criando veículo de teste...')
    if not create_vehicle(session):
        print('Falha ao criar veículo.')
        sys.exit(1)
    print('Veículo criado com sucesso.')

    vehicles_page = session.get(urljoin(BASE_URL, '/vehicles'))
    vehicle_id = get_available_vehicle_id(vehicles_page.text)
    if not vehicle_id:
        print('Não foi possível localizar o veículo criado.')
        sys.exit(1)
    print(f'Veículo criado com id: {vehicle_id}')

    print('Excluindo veículo de teste...')
    if not delete_vehicle(session, vehicle_id):
        print('Falha ao excluir veículo.')
        sys.exit(1)
    print('Veículo excluído com sucesso.')

    print('Teste concluído com sucesso.')


if __name__ == '__main__':
    main()
