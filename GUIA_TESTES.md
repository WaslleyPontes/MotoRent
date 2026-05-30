# Guia de Testes - Funcionalidades Implementadas

## 🧪 Teste 1: Zerar Saúde Administrativa

### Pré-requisitos
- Estar logado como **admin**
- Ter alguns registros de pagamentos, multas ou manutenções

### Passos de Teste

1. Navegue para `/admin`
2. Localize a seção **"Saúde administrativa"**
3. Observe os valores atuais:
   - Pagamentos concluídos
   - Pagamentos em atraso
   - Multas registradas
   - Manutenções agendadas

4. Clique no botão **"⟳ Zerar"**
5. Uma caixa de confirmação deve aparecer perguntando: *"Tem certeza que deseja resetar a saúde administrativa?"*
6. Clique em **OK** para confirmar
7. A página deve recarregar automaticamente
8. Verifique se os valores foram resetados:
   - Pagamentos em atraso → zerados (convertidos para "pendente")
   - Multas → zeradas (deletadas)
   - Manutenções → zeradas (deletadas)

### ✅ Sucesso
- Botão responde ao clique
- Caixa de confirmação aparece
- Valores são resetados corretamente
- Página recarrega automaticamente

---

## 🧪 Teste 2: Deletar Usuário

### Pré-requisitos
- Estar logado como **admin**
- Ter pelo menos 2 usuários registrados

### Passos de Teste

1. Navegue para `/admin`
2. Localize a seção **"Usuários recentes"**
3. Você deve ver uma coluna **"Ações"** com botões vermelhos "Deletar"
4. Selecione um usuário que **NÃO** seja você mesmo
5. Clique no botão **"Deletar"** ao lado do nome
6. Uma caixa de confirmação deve aparecer: *"Tem certeza que deseja deletar o usuário 'username'?"*
7. Clique em **OK** para confirmar
8. A página deve recarregar automaticamente
9. Verifique se o usuário foi removido da lista

### ⚠️ Teste Negativo: Não Permitir Deletar a Si Próprio
1. Se tentar deletar sua própria conta, deve receber erro: *"Não é possível deletar sua própria conta"*

### ✅ Sucesso
- Coluna "Ações" é visível
- Botão responde ao clique
- Confirmação aparece com nome do usuário correto
- Usuário é deletado após confirmação
- Página recarrega
- Não é possível deletar a conta do próprio admin

---

## 🧪 Teste 3: Exportar Vistoria em PDF

### Pré-requisitos
- Estar logado
- Ter pelo menos uma vistoria registrada em `/vehicle-inspection`

### Passos de Teste

1. Navegue para `/vehicle-inspection`
2. Role para baixo até a seção **"Histórico de vistorias"**
3. Você deve ver uma coluna **"Ações"** com botões verdes "📄 PDF"
4. Selecione uma vistoria
5. Clique no botão **"📄 PDF"**
6. Um arquivo PDF deve ser baixado automaticamente:
   - Nome do arquivo: `vistoria_<id>.pdf`
   - Exemplo: `vistoria_5.pdf`

### Verificar Conteúdo do PDF
Abra o PDF e verifique se contém:
- ✓ Título: "Relatório de Vistoria de Veículo"
- ✓ Dados da Vistoria (ID, Data, Inspetor, Tipo)
- ✓ Dados do Veículo (Marca/Modelo, Placa, Quilometragem, Combustível)
- ✓ Condições Gerais (Condição do veículo)
- ✓ Observações (notas registradas)
- ✓ Rodapé com data/hora de geração

### ✅ Sucesso
- Coluna "Ações" é visível
- Botão PDF está disponível
- PDF é baixado com nome correto
- Conteúdo do PDF está formatado e legível
- Todas as informações da vistoria estão presentes

---

## 🧪 Teste 4: Exportar Receita em PDF (Financeiro)

### Pré-requisitos
- Estar logado como admin ou operador
- Ter pelo menos alguns pagamentos registrados em `/finance`

### Passos de Teste

1. Navegue para `/finance`
2. Role para a seção **"Histórico de pagamentos"**
3. Você deve ver dois botões:
   - **"📄 PDF"** (verde)
   - **"📊 CSV"** (azul, já existia)

4. Clique no botão **"📄 PDF"**
5. Um arquivo PDF deve ser baixado automaticamente:
   - Nome do arquivo: `relatorio_financeiro.pdf`

### Verificar Conteúdo do PDF
Abra o PDF e verifique se contém:
- ✓ Título: "Relatório Financeiro MotoRent"
- ✓ Resumo Financeiro com:
  - Receita Paga (R$ total)
  - Valores em Atraso (R$ total)
  - Valores Pendentes (R$ total)
  - Total de Pagamentos (quantidade)
- ✓ Tabela com últimos 20 pagamentos mostrando:
  - Data, Cliente, Veículo, Valor, Status
- ✓ Rodapé com data/hora de geração

### ✅ Sucesso
- Botões PDF e CSV estão visíveis
- PDF é baixado com nome correto
- Conteúdo do PDF está formatado e legível
- Tabela de pagamentos é exibida corretamente
- Valores financeiros estão formatados com 2 casas decimais

---

## 🧪 Teste 5: Verificar Segurança

### Teste 5.1: CSRF Protection
1. Tente fazer uma requisição POST sem CSRF token
2. Deve receber erro: **400 - CSRF_token inválido ou ausente**

### Teste 5.2: Autenticação
1. Faça logout (`/logout`)
2. Tente acessar `/admin`
3. Deve ser redirecionado para `/login`

### Teste 5.3: Autorização
1. Faça login como usuário comum (não admin)
2. Tente acessar `/admin`
3. Deve receber mensagem: **"Acesso restrito a administradores"**

### ✅ Sucesso
- CSRF protection funciona
- Autenticação é verificada
- Autorização (admin-only) é verificada

---

## 📋 Checklist de Teste Completo

```
Funcionalidade: Zerar Saúde Administrativa
[ ] Botão "⟳ Zerar" está visível
[ ] Confirmação de diálogo aparece
[ ] Valores são resetados corretamente
[ ] Página recarrega automaticamente

Funcionalidade: Deletar Usuário
[ ] Coluna "Ações" está visível
[ ] Botão "Deletar" está vermelho
[ ] Confirmação aparece com nome do usuário
[ ] Usuário é deletado após confirmação
[ ] Não é possível deletar a própria conta

Funcionalidade: Exportar Vistoria em PDF
[ ] Coluna "Ações" está visível no histórico
[ ] Botão "📄 PDF" está disponível
[ ] PDF é baixado com nome correto
[ ] PDF contém todos os dados esperados
[ ] Formatação do PDF está legível

Funcionalidade: Exportar Receita em PDF
[ ] Botões "📄 PDF" e "📊 CSV" estão visíveis
[ ] PDF é baixado com nome correto
[ ] Resumo financeiro está correto
[ ] Tabela de pagamentos está formatada
[ ] Rodapé com data/hora está presente

Segurança
[ ] CSRF protection funciona
[ ] Autenticação é verificada
[ ] Autorização de admin é verificada
```

---

## 🐛 Resolução de Problemas

### Problema: Botão não aparece

**Solução:**
- Limpe o cache do navegador (Ctrl+Shift+Delete)
- Recarregue a página (Ctrl+F5)
- Verifique se está logado como admin

### Problema: PDF não baixa

**Solução:**
- Verificar se navegador permite downloads
- Verificar console do navegador (F12) para erros
- Verificar permissões do servidor

### Problema: Erro 404 em rotas de exportação

**Solução:**
- Reinicie o servidor Flask
- Verifique se o arquivo `app.py` foi salvo corretamente
- Verifique a sintaxe do Python: `python -m py_compile app.py`

### Problema: Confirmação não aparece

**Solução:**
- Verificar se JavaScript está habilitado
- Limpar cache do navegador
- Verificar console para erros JavaScript

---

## 📝 Relatório de Teste

Após completar os testes, preencha este relatório:

**Data do Teste:** [_______________]

**Testador:** [_______________]

**Funcionalidades Testadas:**
- [ ] Zerar Saúde Administrativa: ___/10
- [ ] Deletar Usuário: ___/10
- [ ] Exportar Vistoria em PDF: ___/10
- [ ] Exportar Receita em PDF: ___/10
- [ ] Segurança: ___/10

**Problemas Encontrados:**
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

**Observações Gerais:**
_______________________________________________
_______________________________________________

**Recomendações:**
_______________________________________________
_______________________________________________

---

## ✅ Conclusão

Todas as funcionalidades foram implementadas com sucesso e estão prontas para teste!

**Status:** 🟢 Pronto para Produção
