# 🧪 GUIA DE TESTE DAS CORREÇÕES

## Visão Geral

Este guia descreve como testar cada uma das correções implementadas no MotoRent.

---

## 1️⃣ Validação de Força de Senha

### Teste 1.1: Registro com Senha Fraca
**Objetivo:** Verificar que senhas fracas são rejeitadas

**Passos:**
1. Ir para `/register`
2. Preencher formulário com:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `123` (senha fraca - menos de 8 caracteres)
3. Clicar em Registrar

**Resultado Esperado:** ❌ Mensagem de erro: "Senha deve ter no mínimo 8 caracteres."

### Teste 1.2: Registro com Senha Sem Número
**Passos:**
1. Senha: `AbcdefGh` (8 caracteres, mas sem número)

**Resultado Esperado:** ❌ Mensagem de erro: "Senha deve conter pelo menos 1 número."

### Teste 1.3: Registro com Senha Sem Maiúscula
**Passos:**
1. Senha: `abcdef123` (8+ caracteres com número, mas sem maiúscula)

**Resultado Esperado:** ❌ Mensagem de erro: "Senha deve conter pelo menos 1 letra maiúscula."

### Teste 1.4: Registro com Senha Forte ✅
**Passos:**
1. Senha: `StrongPass123` (8+ caracteres, número, maiúscula)

**Resultado Esperado:** ✅ "Conta criada com sucesso. Faça login agora."

### Teste 1.5: Reset de Senha com Validação
**Passos:**
1. Ir para `/forgot-password`
2. Informar email existente
3. Clicar em "Recuperar Senha"
4. Abrir link do email (ou usar direto o link fornecido)
5. Tentar redefinir com senha fraca: `123`

**Resultado Esperado:** ❌ Mensagem de erro de validação

---

## 2️⃣ Cookie SameSite Seguro

### Teste 2.1: Verificar Header de Cookie em Produção
**Objetivo:** Verificar que SameSite está configurado como 'Strict' em produção

**Passos:**
1. Usar browser dev tools (F12 → Storage → Cookies)
2. Acessar `/login` em modo produção (FLASK_ENV=production)
3. Verificar cookie `session`

**Resultado Esperado:**
- Em produção: `SameSite=Strict`
- Em desenvolvimento: `SameSite=Lax`

**Verificação via curl:**
```bash
curl -i https://seu-app.com/login | grep -i "set-cookie"
# Deve mostrar: Set-Cookie: ... SameSite=Strict
```

---

## 3️⃣ Validação CSRF Token

### Teste 3.1: POST sem CSRF Token
**Objetivo:** Verificar que requisições POST sem CSRF token são rejeitadas

**Passos:**
```bash
curl -X POST http://localhost:5000/customers \
  -d "action=create&name=Test" \
  -b "session=sua_sessao"
```

**Resultado Esperado:** ❌ Erro 400: "CSRF token inválido ou ausente."

### Teste 3.2: POST com CSRF Token Válido
**Passos:**
1. Acessar página que gera token (qualquer página GET)
2. Extrair token do formulário
3. Enviar POST com token válido

**Resultado Esperado:** ✅ Requisição aceita

### Teste 3.3: GET Sem Token (Deve Aceitar)
**Objetivo:** Verificar que GET não requer CSRF token

**Passos:**
```bash
curl -X GET http://localhost:5000/customers
```

**Resultado Esperado:** ✅ Página carregada normalmente (sem erro de CSRF)

---

## 4️⃣ Validação de Email Duplicado em API

### Teste 4.1: Criar Cliente via API com Email Duplicado
**Objetivo:** Verificar que API rejeita email duplicado

**Passos:**
```bash
# Primeiro cliente (sucesso)
curl -X POST http://localhost:5000/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"João","document":"12345678900","email":"joao@test.com"}'

# Segundo cliente com mesmo email (falha esperada)
curl -X POST http://localhost:5000/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Maria","document":"98765432100","email":"joao@test.com"}'
```

**Resultado Esperado:**
- Primeira: ✅ `{"status": "ok"}`
- Segunda: ❌ `{"error": "Email já está registrado."}`

### Teste 4.2: Criar Cliente via API com Telefone Duplicado
**Passos:**
```bash
curl -X POST http://localhost:5000/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Pedro","document":"11111111100","phone":"11999999999"}'

curl -X POST http://localhost:5000/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Paulo","document":"22222222200","phone":"11999999999"}'
```

**Resultado Esperado:**
- Primeira: ✅ `{"status": "ok"}`
- Segunda: ❌ `{"error": "Telefone já está registrado."}`

---

## 5️⃣ Tratamento de Exceções Melhorado

### Teste 5.1: Upload de Arquivo com OCR Desabilitado
**Objetivo:** Verificar mensagens de erro específicas quando OCR não está disponível

**Passos:**
1. Comentar imports de PIL/pytesseract para simular falta
2. Ir para `/upload-document`
3. Fazer upload de imagem

**Resultado Esperado:**
- ✅ Mensagem específica: "OCR não disponível neste ambiente..."
- ✅ Arquivo ainda é salvo com sucesso

### Teste 5.2: Erro de Arquivo não Encontrado
**Objetivo:** Verificar tratamento de erro específico em OCR

**Passos:**
1. Tentar salvar arquivo em local sem permissão

**Resultado Esperado:**
- ✅ Erro específico: "OCR falhou: arquivo não encontrado..."
- ❌ Não mensagem genérica "Exception"

### Teste 5.3: Upload com owner_id Inválido
**Objetivo:** Verificar tratamento robusto de owner_id malformado

**Passos:**
1. Enviar POST para `/upload-document` com:
   - `owner_id`: "invalido:xyz:123"
   - `file`: arquivo válido

**Resultado Esperado:**
- ✅ Trata corretamente mesmo com múltiplos `:`
- ✅ Ou erro gracioso: "Proprietário inválido"

---

## 🔍 TESTES DE INTEGRAÇÃO

### Teste I.1: Fluxo Completo de Novo Usuário
**Passos:**
1. ✅ Registrar com senha forte
2. ✅ Fazer login
3. ✅ Acessar dashboard
4. ✅ Criar cliente (validação de email/telefone)
5. ✅ Upload de documento

**Resultado Esperado:** Todos os passos funcionam sem erro

### Teste I.2: Fluxo de Recuperação de Senha
**Passos:**
1. ✅ Acessar `/forgot-password`
2. ✅ Informar email válido
3. ✅ Clicar no link do email (ou usar URL manualmente)
4. ✅ Tentar nova senha fraca → ❌ Rejeição
5. ✅ Tentar nova senha forte → ✅ Sucesso
6. ✅ Login com nova senha

**Resultado Esperado:** Todas as validações funcionam

### Teste I.3: API de Clientes com Validações
**Passos:**
1. ✅ Criar cliente válido via API
2. ✅ Tentar criar com email duplicado → Falha
3. ✅ Tentar criar com telefone duplicado → Falha
4. ✅ Tentar criar sem documento → Falha
5. ✅ Criar outro cliente válido com dados diferentes

**Resultado Esperado:** Validações funcionam como esperado

---

## 📱 TESTES EM DIFERENTES NAVEGADORES

Testar em:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile (iOS/Android)

Verificar:
- [ ] Cookies salvos corretamente
- [ ] Form validation funciona
- [ ] Mensagens de erro aparecem
- [ ] Redirect após ações funcionam

---

## 🛠️ TESTES COM FERRAMENTAS

### Teste com curl
```bash
# Testar CSRF
curl -i -X POST http://localhost:5000/customers \
  -d "action=create" \
  --cookie "session=abc123"

# Testar API com email duplicado
curl -X POST http://localhost:5000/api/customers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer token" \
  -d '{"name":"Test","document":"123","email":"test@test.com"}'
```

### Teste com Python
```python
import requests

# Teste de força de senha
response = requests.post('http://localhost:5000/register', data={
    'username': 'testuser',
    'email': 'test@test.com',
    'password': '123'  # Senha fraca
})
assert 'mínimo 8 caracteres' in response.text

# Teste de email duplicado via API
response = requests.post('http://localhost:5000/api/customers', json={
    'name': 'Test',
    'document': '123',
    'email': 'duplicate@test.com'
})
assert response.status_code == 201  # Primeiro sucede

response = requests.post('http://localhost:5000/api/customers', json={
    'name': 'Test2',
    'document': '456',
    'email': 'duplicate@test.com'  # Mesmo email
})
assert response.status_code == 400  # Segundo falha
```

---

## ✅ CHECKLIST FINAL

- [ ] Validação de senha funciona em `/register`
- [ ] Validação de senha funciona em `/reset-password`
- [ ] Cookie SameSite está correto
- [ ] CSRF token obrigatório em POST/PUT/DELETE
- [ ] CSRF token não obrigatório em GET
- [ ] Email duplicado rejeitado em `/api/customers`
- [ ] Telefone duplicado rejeitado em `/api/customers`
- [ ] Mensagens de erro são específicas (não genéricas)
- [ ] Arquivo ainda é salvo quando OCR falha
- [ ] Nenhum erro 500 causado pelas mudanças
- [ ] Fluxo de login completo funciona
- [ ] Fluxo de reset de senha completo funciona

---

## 📊 RESULTADOS

Após completar todos os testes, preencher:

| Teste | Status | Notas |
|-------|--------|-------|
| Validação de Senha | ✅/❌ | |
| Cookie SameSite | ✅/❌ | |
| CSRF Token | ✅/❌ | |
| Email Duplicado | ✅/❌ | |
| Exceções Específicas | ✅/❌ | |
| Integração | ✅/❌ | |
| Performance | ✅/❌ | |

---

**Data de Teste:** _______________  
**Testado por:** _______________  
**Status Final:** ✅ APROVADO / ❌ REPROVADO / ⚠️ APROVADO COM RESSALVAS

