# Teste com Dados Reais

## Objetivo
Criar um conjunto mínimo de dados reais para validar cadastro, edição, exclusão, reservas e vendas no MotoRent.

---

## 1. Dados de Clientes
Use a tela `Clientes` para cadastrar os itens abaixo.

### Cliente 1
- Nome: João Silva
- Documento: CPF 123.456.789-01
- E-mail: joao.silva@motorent.com
- Telefone: (85) 99999-0001
- Telefone 2: (85) 98888-0001
- CEP: 60840-000
- Rua: Av. República
- Número: 150
- Bairro: Meireles
- Cidade: Fortaleza
- Estado: CE

### Cliente 2
- Nome: Maria Oliveira
- Documento: CPF 987.654.321-00
- E-mail: maria.oliveira@motorent.com
- Telefone: (85) 99999-0002
- Telefone 2: (85) 98888-0002
- CEP: 60110-000
- Rua: Av. Bezerra de Menezes
- Número: 320
- Bairro: Aldeota
- Cidade: Fortaleza
- Estado: CE

### Cliente 3
- Nome: Carlos Pereira
- Documento: CPF 321.654.987-88
- E-mail: carlos.pereira@motorent.com
- Telefone: (85) 99999-0003
- Telefone 2: (85) 98888-0003
- CEP: 60320-000
- Rua: Rua Padre Cícero
- Número: 780
- Bairro: Parangaba
- Cidade: Fortaleza
- Estado: CE

---

## 2. Dados de Veículos
Use a tela `Veículos` para cadastrar os itens abaixo.

### Veículo 1
- Marca: Honda
- Modelo: Honda Start 160
- Placa: QZE4E59
- Cor: Azul
- Status: disponível
- Seguro: Seguro Ativo
- Cliente: João Silva

### Veículo 2
- Marca: Yamaha
- Modelo: Yamaha Crosser Z ABS
- Placa: LSK9M12
- Cor: Branco
- Status: disponível
- Seguro: Seguro Ativo
- Cliente: (não selecionar)

### Veículo 3
- Marca: Haojue
- Modelo: NK 160
- Placa: PTA1R34
- Cor: Preta
- Status: manutenção
- Seguro: Seguro Ativo
- Cliente: Maria Oliveira

### Veículo 4
- Marca: Honda
- Modelo: Bros 160 CBS
- Placa: RXT2C45
- Cor: Vermelha
- Status: alugado
- Seguro: Seguro Ativo
- Cliente: Carlos Pereira

---

## 3. Roteiro de Testes
### Passo 1: Login e Registro
1. Acesse `/register` e crie um usuário de teste.
2. Faça login em `/login`.
3. Verifique se a aplicação redireciona para o dashboard.

### Passo 2: Cadastro de Clientes
1. Cadastre os três clientes listados acima.
2. Verifique se os clientes aparecem na tabela.
3. Edite um cliente e altere o telefone secundário.
4. Tente cadastrar outro cliente com o mesmo `phone2` para validar a rejeição.

### Passo 3: Cadastro de Veículos
1. Cadastre os quatro veículos listados acima.
2. Verifique se os modelos novos aparecem e podem ser selecionados.
3. Edite um veículo e altere a cor, o status e o cliente.
4. Exclua um veículo e confirme que ele desaparece da tabela.

### Passo 4: Reservas e PDV
1. Crie uma reserva para `Yamaha Crosser Z ABS` com início em `2026-06-10` e fim em `2026-06-15`.
2. Verifique se o status do veículo muda para `reservado`.
3. No PDV, registre a venda de um veículo disponível.
4. Verifique se o veículo muda para `vendido` e se o dono é atualizado.

### Passo 5: Dashboard e Relatórios
1. Acesse o dashboard e confira os cartões de receita e status de frota.
2. Verifique se os valores de veículos disponíveis, alugados e em manutenção estão corretos.
3. Se houver telemetria ativada, confira o mapa e as informações de localização.

---

## 4. Verificações Especiais
- `phone2` deve ser salvo sem conflito.
- `model` deve carregar opções atualizadas para Honda/Yamaha/Haojue.
- Exclusão de veículo deve funcionar sem erro no front.
- CSRF deve continuar protegido em ações POST.

---

## 5. Observações
- Se quiser, gere dados SQL direto ou use a interface para maior cobertura.
- Use este roteiro em modo manual para validar comportamento real antes de liberar a aplicação.
