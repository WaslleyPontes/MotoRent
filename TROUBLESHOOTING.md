# Troubleshooting - MotoRent

Guia de resolução de problemas comuns.

## 🚫 Erros Comuns

### 1. "ModuleNotFoundError: No module named 'flask'"

**Causa:** Dependências não instaladas ou ambiente virtual não ativado.

**Solução:**
```powershell
# Certifique-se que está na pasta correta
cd "c:\Users\PROCAMPO\Desktop\Nova pasta"

# Ative o ambiente virtual
venv\Scripts\Activate

# Reinstale as dependências
pip install -r requirements.txt
```

---

### 2. "database.db" não encontrado

**Causa:** Banco de dados não foi inicializado.

**Solução:**
```powershell
# Na pasta do projeto:
python db_init.py

# Você deve ver a mensagem:
# Banco de dados criado em C:\...\database.db
```

---

### 3. Porta 5000 já está em uso

**Causa:** Outra aplicação está usando a mesma porta.

**Solução - Opção 1:** Use outra porta
```powershell
$env:PORT=5001
python app.py
```

**Solução - Opção 2:** Encerre o processo que usa a porta
```powershell
# Encontre o PID
netstat -ano | findstr ":5000"

# Finalize o processo (substitua PID)
taskkill /PID <PID> /F
```

---

### 4. "No module named 'dotenv'"

**Causa:** python-dotenv não instalado.

**Solução:**
```powershell
pip install python-dotenv
```

---

### 5. Erro ao fazer login - "Usuario ou senha incorretos"

**Possíveis causas:**
- Usuário digitado incorretamente (Case-sensitive)
- Banco de dados não foi inicializado

**Solução:**
```powershell
# Credenciais corretas:
Usuário: admin (minúsculo)
Senha: admin123

# Se ainda não funcionar, reinicialize o banco:
python db_init.py
```

---

### 6. Erro de CORS ou requisições bloqueadas

**Causa:** Headers de segurança/CSP muito restritivos.

**Solução:** Edite `.env`
```env
FLASK_ENV=development
```

---

### 7. OCR não funciona (Windows)

**Causa:** Tesseract OCR não instalado.

**Solução:**
O sistema funciona sem OCR. Se quiser OCR:

1. Baixe o instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Instale em: `C:\Program Files\Tesseract-OCR`
3. Configure no `.env`:
```env
# Opcional - caminho do Tesseract
PYTESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

### 8. Erro: "CSRF token inválido"

**Causa:** Sessão expirada ou cookie de segurança incorreto em produção.

**Solução:**
- Limpe os cookies do navegador
- Faça logout e login novamente

Se persistir em produção, verifique se está usando HTTPS.

---

### 9. Emails de recuperação de senha não funcionam

**Causa:** SMTP não configurado.

**Solução:** Configure no `.env`:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-app (usar App Password no Gmail)
MAIL_USE_TLS=True
```

---

### 10. Aplicação roda lentamente

**Causa:** Modo debug ativado ou muitos dados no banco.

**Solução:**
- Em produção: `FLASK_ENV=production`
- Aumente tamanho de índices no SQLite
- Configure cache (futuro)

---

## ✅ Checklist de Inicialização

Antes de reportar bugs, verifique:

- [ ] Python 3.10+ instalado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas: `pip list | grep Flask`
- [ ] Banco de dados existe: `database.db` na pasta
- [ ] Arquivo `.env` existe e contém `FLASK_ENV=development`
- [ ] Nenhuma outra app na porta 5000: `netstat -ano | findstr ":5000"`
- [ ] Firewall permite conexão em localhost

---

## 🔧 Resetar Tudo

Se algo deu muito errado:

```powershell
# 1. Delete o banco de dados
Remove-Item database.db

# 2. Delete o cache Python
Remove-Item __pycache__ -Recurse -Force
Remove-Item *.pyc

# 3. Delete o ambiente virtual
Remove-Item venv -Recurse -Force

# 4. Recrie do zero
python -m venv venv
venv\Scripts\Activate
pip install -r requirements.txt
python db_init.py
python app.py
```

---

## 📞 Informações de Debug

Para obter mais detalhes de erro, rode com:

```powershell
$env:FLASK_ENV="development"
$env:FLASK_DEBUG=1
python app.py
```

Ou adicione ao arquivo `app.py` antes da última linha:
```python
if __name__ == '__main__':
    app.logger.setLevel('DEBUG')
    app.run(debug=True, port=5000)
```

---

## 🆘 Último Recurso

Se nada funcionar:

1. Leia os logs completos do Flask
2. Verifique se há problemas de encoding em caracteres especiais
3. Teste com um novo projeto Flask mínimo para isolar o problema
4. Considere usar um ambiente de produção (Heroku, Railway, etc)

---

**Versão:** 1.0  
**Último atualizado:** Maio 2026
