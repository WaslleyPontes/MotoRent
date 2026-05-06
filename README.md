# Sistema de Locação de Motos com Dashboard

Este projeto é um protótipo de um sistema de locação de motos com intenção de venda. Ele combina:

- Frontend em HTML, CSS e JavaScript
- Backend em Python usando Flask
- Banco de dados SQLite simples
- Dashboard dark mode, responsivo e mobile-friendly
- Gráficos com Chart.js
- Mapa interativo com Leaflet
- Autenticação básica de usuário
- Cadastro de clientes e veículos
- Upload de documentos com suporte a OCR
- Background check e scoring de condutor

## Funcionalidades implementadas

- Login e registro de usuário com roles (`admin` e `operator`)
- Dashboard principal com métricas, gráficos e mapa
- Telas de cadastro de clientes e veículos
- Gestão de multas e multas pendentes
- Manutenção preditiva e agenda de revisões
- Telemetria com dados de localização e velocidade
- Upload de documentos com OCR embutido
- API de background check e score de risco
- Painel de administração de usuários (somente admin)

## Requisitos

- Python 3.10+ instalado
- Acesso à internet para baixar bibliotecas CDN do frontend
- Para OCR real, instale o Tesseract OCR no Windows e configure o `pytesseract`

## Passo a passo para preparar o ambiente

1. Abra o terminal na pasta do projeto:

```powershell
cd "c:\Users\wasll\Desktop\Nova pasta"
```

2. Crie e ative um ambiente virtual Python:

```powershell
python -m venv venv
venv\Scripts\activate
```

3. Instale as dependências:

```powershell
pip install -r requirements.txt
```

4. Crie o banco de dados inicial:

```powershell
python db_init.py
```

5. (Opcional) Gere os ícones PWA se quiser recriá-los:

```powershell
python generate_icons.py
```

6. Execute o servidor Flask:

```powershell
python app.py
```

7. Abra no navegador:

```text
http://127.0.0.1:5000
```

## Acesso inicial

- Usuário: `admin`
- Senha: `admin123`

## Estrutura das páginas

- `/` - Dashboard principal
- `/login` - Tela de login
- `/register` - Registro de usuário
- `/customers` - Cadastro e listagem de clientes
- `/vehicles` - Cadastro e listagem de veículos
- `/fines` - Gestão de multas
- `/maintenance` - Manutenção preventiva e preditiva
- `/telemetry` - Telemetria e rastreamento
- `/upload-document` - Upload de documentos com OCR
- `/background-check` - Verificação de antecedentes
- `/users` - Gestão de usuários (admin apenas)

## Sugestões de próximos passos

- Adicionar autenticação com roles (admin, operador)
- Criar painel de multas e histórico de infrações
- Implementar telemetria real com GPS de veículos
- Usar API externa de background check para dados reais
- Adicionar relatórios de manutenção preditiva e risco
- Melhorar UI responsiva para celulares e desktops
- Criar menu mobile e navegação otimizada para toque
- Transformar em PWA para acesso offline e instalação no celular

---

## Estrutura do projeto

- `app.py` - servidor Flask e rotas principais
- `db_init.py` - cria o banco SQLite e sementes iniciais
- `templates/` - páginas HTML com Jinja2
- `static/css/style.css` - estilos da interface
- `static/js/app.js` - lógica do dashboard
- `static/js/forms.js` - scripts de navegação e formulários
- `requirements.txt` - dependências Python
