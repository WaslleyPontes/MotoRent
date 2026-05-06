# Script PowerShell de inicialização do projeto MotoRent
# Use: .\run.ps1

Write-Host "`n" -ForegroundColor Green
Write-Host "╔════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   INICIALIZADOR MOTORENT (PS1)     ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════╝" -ForegroundColor Green
Write-Host "`n" -ForegroundColor Green

# Verificar Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro: Python não encontrado" -ForegroundColor Red
    Write-Host "Baixe em: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Criar venv se necessário
if (-not (Test-Path "venv")) {
    Write-Host "`n📦 Criando ambiente virtual..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Ambiente virtual criado" -ForegroundColor Green
    } else {
        Write-Host "❌ Erro ao criar ambiente virtual" -ForegroundColor Red
        exit 1
    }
}

# Ativar venv
Write-Host "`n🔄 Ativando ambiente virtual..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Instalar dependências
Write-Host "`n📚 Instalando dependências..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependências instaladas" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao instalar dependências" -ForegroundColor Red
    exit 1
}

# Criar banco se necessário
if (-not (Test-Path "database.db")) {
    Write-Host "`n🗄️  Criando banco de dados..." -ForegroundColor Yellow
    python db_init.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Banco de dados criado" -ForegroundColor Green
    } else {
        Write-Host "❌ Erro ao criar banco de dados" -ForegroundColor Red
        exit 1
    }
}

# Iniciar app
Write-Host "`n" -ForegroundColor Green
Write-Host "🚀 INICIALIZANDO SERVIDOR" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "📱 Acesse: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "👤 Usuário: admin" -ForegroundColor Cyan
Write-Host "🔑 Senha: admin123" -ForegroundColor Cyan
Write-Host "⏹️  Ctrl+C para parar" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "`n" -ForegroundColor Green

python app.py

Write-Host "`n✅ Servidor finalizado`n" -ForegroundColor Green
