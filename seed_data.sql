-- seed_data.sql
-- Insere dados de teste para clientes e veículos no MotoRent.
-- Execute no SQLite com: sqlite3 moto_rent.db < seed_data.sql

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

INSERT OR IGNORE INTO customers (name, document_type, document, email, phone, phone2, score, internal_notes, cep, street, number, neighborhood, city, state, complement)
VALUES
('João Silva', 'CPF', '123.456.789-01', 'joao.silva@motorent.com', '(85) 99999-0001', '(85) 98888-0001', 750, 'Cliente VIP', '60840-000', 'Av. República', '150', 'Meireles', 'Fortaleza', 'CE', ''),
('Maria Oliveira', 'CPF', '987.654.321-00', 'maria.oliveira@motorent.com', '(85) 99999-0002', '(85) 98888-0002', 710, 'Cliente recorrente', '60110-000', 'Av. Bezerra de Menezes', '320', 'Aldeota', 'Fortaleza', 'CE', ''),
('Carlos Pereira', 'CPF', '321.654.987-88', 'carlos.pereira@motorent.com', '(85) 99999-0003', '(85) 98888-0003', 680, 'Cliente para manutenção', '60320-000', 'Rua Padre Cícero', '780', 'Parangaba', 'Fortaleza', 'CE', 'Apto 101');

INSERT OR IGNORE INTO vehicles (brand, model, plate, color, status, insurance, latitude, longitude, owner_id)
VALUES
('Honda', 'Honda Start 160', 'QZE4E59', 'Azul', 'disponível', 'Seguro Ativo', -3.72339, -38.52707, (SELECT id FROM customers WHERE email = 'joao.silva@motorent.com')),
('Yamaha', 'Yamaha Crosser Z ABS', 'LSK9M12', 'Branco', 'disponível', 'Seguro Ativo', -3.73364, -38.58923, NULL),
('Haojue', 'NK 160', 'PTA1R34', 'Preta', 'manutenção', 'Seguro Ativo', -3.71042, -38.52666, (SELECT id FROM customers WHERE email = 'maria.oliveira@motorent.com')),
('Honda', 'Bros 160 CBS', 'RXT2C45', 'Vermelha', 'alugado', 'Seguro Ativo', -3.73968, -38.52335, (SELECT id FROM customers WHERE email = 'carlos.pereira@motorent.com'));

COMMIT;
