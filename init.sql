-- Arquivo de inicialização do banco de dados PostgreSQL
-- Este arquivo será executado automaticamente quando o container for criado

-- Criar extensões úteis se necessário
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Outras configurações iniciais podem ser adicionadas aqui
SELECT 'Database initialized successfully' as status;
