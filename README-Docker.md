# Hair Salon API - Docker Setup

Este documento explica como usar Docker e Docker Compose para executar a API do sistema de salão de beleza.

## 📋 Pré-requisitos

- Docker
- Docker Compose
- Git

## 🚀 Início Rápido

### Desenvolvimento

```bash
# Iniciar ambiente de desenvolvimento
./docker-scripts.sh dev-up

# Parar ambiente de desenvolvimento
./docker-scripts.sh dev-down
```

### Produção

```bash
# Iniciar ambiente de produção
./docker-scripts.sh prod-up

# Parar ambiente de produção
./docker-scripts.sh prod-down
```

## 🛠️ Comandos Úteis

### Gerenciamento de Containers

```bash
# Ver logs do desenvolvimento
./docker-scripts.sh logs dev

# Ver logs da produção
./docker-scripts.sh logs

# Executar comandos Django no desenvolvimento
./docker-scripts.sh manage dev migrate
./docker-scripts.sh manage dev collectstatic

# Criar superusuário
./docker-scripts.sh superuser dev

# Resetar banco de dados (CUIDADO: apaga todos os dados!)
./docker-scripts.sh reset-db dev
```

### Comandos Docker Manuais

```bash
# Construir imagens
docker-compose build

# Iniciar serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down

# Remover volumes (apaga dados do banco)
docker-compose down -v
```

## 🗄️ Configuração do Banco de Dados

### Desenvolvimento
- **Host**: localhost
- **Porta**: 5433
- **Banco**: salao_dev_db
- **Usuário**: salao_dev_user
- **Senha**: dev_password123

### Produção
- **Host**: localhost
- **Porta**: 5432
- **Banco**: salao_db
- **Usuário**: salao_user
- **Senha**: salao_password123

## 📡 Endpoints da API

Após iniciar os containers, a API estará disponível em:

- **API Base**: http://localhost:8000/api/
- **Documentação Swagger**: http://localhost:8000/
- **Admin Django**: http://localhost:8000/admin/

### Principais Endpoints

- `GET /api/clients/` - Listar clientes
- `GET /api/services/` - Listar serviços
- `GET /api/team/` - Listar equipe
- `GET /api/appointments/` - Listar agendamentos

## 🔧 Estrutura dos Containers

### Web (Django)
- **Porta**: 8000
- **Volumes**: Código fonte montado para desenvolvimento
- **Dependências**: PostgreSQL

### Database (PostgreSQL)
- **Porta**: 5432 (prod) / 5433 (dev)
- **Volumes**: Dados persistentes
- **Backup**: Dados salvos em volumes Docker

### Redis (Opcional)
- **Porta**: 6379
- **Uso**: Cache e sessões (para uso futuro)

## 🔒 Variáveis de Ambiente

As seguintes variáveis são configuradas automaticamente:

```env
DEBUG=1
DATABASE_URL=postgresql://user:password@db:5432/database
```

## 📝 Logs e Debugging

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f web
docker-compose logs -f db

# Acessar container em execução
docker-compose exec web bash
docker-compose exec db psql -U salao_user -d salao_db
```

## 🚨 Troubleshooting

### Problema: Porta já em uso
```bash
# Parar todos os containers
docker-compose down

# Verificar portas em uso
netstat -tlnp | grep :8000
```

### Problema: Erro de permissão
```bash
# Dar permissão ao script
chmod +x docker-scripts.sh
```

### Problema: Banco de dados não conecta
```bash
# Verificar se o container do banco está rodando
docker-compose ps

# Resetar banco de dados
./docker-scripts.sh reset-db dev
```

## 📦 Deploy em Produção

Para deploy em produção, use o arquivo `docker-compose.yml`:

```bash
# Produção
docker-compose up --build -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

## 🔄 Backup e Restore

### Backup do Banco de Dados
```bash
docker-compose exec db pg_dump -U salao_user salao_db > backup.sql
```

### Restore do Banco de Dados
```bash
docker-compose exec -T db psql -U salao_user salao_db < backup.sql
```
