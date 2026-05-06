@echo off
REM Script de inicialização rápida do projeto MotoRent

echo.
echo ======================================
echo   INICIALIZADOR DO PROJETO MOTORENT
echo ======================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Erro: Python não está instalado ou não está no PATH
    echo.
    echo Baixe Python em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python detectado

REM Criar ambiente virtual se não existir
if not exist "venv" (
    echo.
    echo 📦 Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Erro ao criar ambiente virtual
        pause
        exit /b 1
    )
    echo ✅ Ambiente virtual criado
)

REM Ativar ambiente virtual
echo.
echo 🔄 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instalar/atualizar dependências
echo.
echo 📚 Instalando dependências...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)
echo ✅ Dependências instaladas

REM Criar banco de dados
if not exist "database.db" (
    echo.
    echo 🗄️  Criando banco de dados...
    python db_init.py
    if errorlevel 1 (
        echo ❌ Erro ao criar banco de dados
        pause
        exit /b 1
    )
    echo ✅ Banco de dados criado
)

REM Iniciar aplicação
echo.
echo 🚀 Iniciando aplicação...
echo.
echo ======================================
echo   SERVIDOR RODANDO EM 5000
echo   http://127.0.0.1:5000
echo ======================================
echo.
echo Credenciais:
echo   Usuário: admin
echo   Senha: admin123
echo.
echo Pressione CTRL+C para parar
echo ======================================
echo.

python app.py
pause
