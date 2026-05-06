# Sistema de Locação de Motos - Guia Rápido

Sistema completo de gerenciamento de locação de motos com intenção de venda, desenvolvido em **Flask + SQLite + JavaScript moderno**.

## 🎯 Funcionalidades Principais

✅ **Autenticação** - Login com roles (admin/operator)  
✅ **Dashboard** - Métricas, gráficos interativos e mapa de localização  
✅ **Clientes** - Cadastro com validação de CPF, email e telefone  
✅ **Veículos** - Gerenciamento de frota com rastreamento  
✅ **Financeiro** - Controle de pagamentos e multas  
✅ **Manutenção** - Agenda preventiva e preditiva  
✅ **Background Check** - Verificação de risco de condutor  
✅ **OCR** - Extração de texto de documentos  
✅ **Telemetria** - Rastreamento de veículos com GPS  
✅ **PWA** - Funciona offline com Service Worker  

---

## 🚀 Instalação Rápida

### 1️⃣ Preparar Ambiente

```powershell
# Abrir PowerShell e navegar até a pasta
cd "c:\Users\PROCAMPO\Desktop\Nova pasta"

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
venv\Scripts\Activate
```

### 2️⃣ Instalar Dependências

```powershell
pip install -r requirements.txt
```

### 3️⃣ Criar Banco de Dados

```powershell
python db_init.py
```

Você verá: `Banco de dados criado em C:\...\database.db`

### 4️⃣ Executar Aplicação

```powershell
python app.py
```

Acesse: **http://127.0.0.1:5000**

---

## 🔐 Credenciais Padrão

| Usuário | Senha | Perfil |
|---------|-------|--------|
| **admin** | admin123 | Administrador |
| **operador** | operador123 | Operador |

---

## 📋 Estrutura do Projeto

```
Nova pasta/
├── app.py                    # Aplicação Flask principal
├── db_init.py               # Inicializador do banco de dados
├── requirements.txt         # Dependências Python
├── .env                     # Variáveis de ambiente (não commitar)
├── .env.example            # Template de variáveis
├── database.db             # Banco de dados SQLite
│
├── templates/              # HTML templates
│   ├── index.html         # Dashboard principal
│   ├── login.html         # Tela de login
│   ├── customers.html     # Gestão de clientes
│   ├── vehicles.html      # Gestão de veículos
│   ├── finance.html       # Financeiro
│   ├── maintenance.html   # Manutenção
│   ├── background_check.html # Verificação de risco
│   ├── upload.html        # Upload com OCR
│   └── ...
│
├── static/                 # Arquivos estáticos
│   ├── css/style.css      # Estilos globais
│   ├── js/
│   │   ├── app.js         # JS principal
│   │   └── forms.js       # Manipulação de formulários
│   ├── manifest.json      # PWA manifest
│   └── service-worker.js  # Service Worker para offline
│
└── uploads/               # Documentos enviados
```

---

## ⚙️ Configuração (Variáveis de Ambiente)

Edite o arquivo `.env`:

```env
# Flask
FLASK_ENV=development       # production em produção
FLASK_DEBUG=1
SECRET_KEY=sua-chave-secreta

# Servidor
PORT=5000
HOST=0.0.0.0

# Email (opcional para recuperação de senha)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-app
MAIL_USE_TLS=True

# Banco de Dados
DATABASE_URL=sqlite:///database.db
```

---

## 🔧 Correções e Melhorias Implementadas

✅ **Bugs Corrigidos:**
- Porta corrigida de 5001 para 5000
- Configuração de segurança para modo desenvolvimento
- Campos de clientes com `document_type` correto
- Validação de importação de `python-dotenv`

✅ **Dependências Atualizadas:**
- Flask 3.0+
- Werkzeug 3.0+
- Pillow 10.0+
- Adicionado `python-dotenv` para variáveis de ambiente
- Adicionado `gunicorn` para produção

✅ **Melhorias de Segurança:**
- HTTPS configurável por ambiente
- Cookies seguros apenas em produção
- CSRF token em todos os formulários
- Headers de segurança (CSP, X-Frame-Options, etc)
- Validação de duplicatas em documento, email e telefone

---

## 🚨 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'flask'"
```powershell
# Certifique-se que o venv está ativado e reinstale
pip install -r requirements.txt
```

### Erro: "database.db" não criado
```powershell
# Execute o inicializador manualmente
python db_init.py
```

### Porta 5000 já em uso
```powershell
# Use outra porta
$env:PORT=5001
python app.py
```

### OCR não funciona (Windows)
```powershell
# Baixe Tesseract OCR em: https://github.com/UB-Mannheim/tesseract/wiki
# O sistema funciona sem OCR, será exibido aviso
```

---

## 📱 Recursos Avançados

- **Integração com ViaCEP** - Preenchimento automático de endereço por CEP
- **Gráficos interativos** - Chart.js para análise de dados
- **Mapa dinâmico** - Leaflet com localização de veículos
- **Exportação CSV** - Relatórios financeiros
- **PWA** - Instalável como app no celular/desktop
- **Dark Mode** - Tema escuro por padrão
- **Responsivo** - Funciona perfeitamente em mobile

---

## 📞 Próximos Passos

1. Adicionar autenticação com banco externo
2. Integrar com APIs de pagamento (Stripe, MercadoPago)
3. Implementar notificações por SMS/Email
4. Adicionar relatórios em PDF
5. Configurar backup automático do banco de dados
6. Deploy em servidor (Heroku, Railway, Render)

---

## 📄 Licença

Projeto educacional - Use livremente para fins de aprendizado.

**Última atualização:** Maio de 2026
