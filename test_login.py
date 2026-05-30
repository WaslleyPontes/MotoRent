import requests
import json

# Testar login
url = 'http://localhost:5000/login'
data = {'username': 'admin', 'password': '123456'}

response = requests.post(url, data=data)
print(f"Status Code: {response.status_code}")
print(f"URL: {response.url}")
print(f"Headers: {response.headers}")
print(f"Content (first 500 chars): {response.text[:500]}")
