# Sistema de Gestão de Salão - Backend API

Uma API REST completa desenvolvida em Django para gerenciamento de salões de beleza, oferecendo funcionalidades para agendamentos, clientes, equipe e serviços.

## 🚀 Funcionalidades

- **Gestão de Clientes**: CRUD completo para cadastro e gerenciamento de clientes
- **Gestão de Equipe**: Cadastro de profissionais com especialidades
- **Gestão de Serviços**: Catálogo de serviços com preços e durações
- **Sistema de Agendamentos**: Agendamento completo com status e controle de workflow, incluindo prevenção de conflitos que impede a marcação de horários quando o profissional já estiver ocupado
- **API REST**: Endpoints completos com documentação Swagger
- **Validação Brasileira**: Formatação e validação de telefones brasileiros
- **CORS Configurado**: Pronto para integração com frontend

## 🛠️ Tecnologias Utilizadas

- **Django 5.2.4**: Framework web principal
- **Django REST Framework 3.16.0**: API REST
- **django-cors-headers**: Configuração CORS
- **drf-yasg**: Documentação Swagger/OpenAPI
- **python-dotenv**: Gerenciamento de variáveis de ambiente
- **SQLite/PostgreSQL**: Banco de dados
- **Docker**: Containerização (opcional)

## 📋 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)
- Git

## 🔧 Instalação e Configuração

### 1. Clone o Repositório

```bash
git clone https://github.com/andrepombo/salao-backend.git
cd salao-backend
```

### 2. Crie um Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Chave secreta do Django (gere uma nova para produção)
SECRET_KEY=sua-chave-secreta-aqui

# Modo debug (False em produção)
DEBUG=True

# Hosts permitidos
ALLOWED_HOSTS=localhost,127.0.0.1

# Origens CORS permitidas
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173

# URL do banco de dados (deixe vazio para usar SQLite)
DATABASE_URL=

# Fuso horário
TIME_ZONE=America/Sao_Paulo

# Código do idioma
LANGUAGE_CODE=pt-br
```

### 5. Execute as Migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crie um Superusuário (Opcional)

```bash
python manage.py createsuperuser
```

### 7. Execute o Servidor

```bash
python manage.py runserver
```

A API estará disponível em: `http://localhost:8000`

## 📚 Documentação da API

### Swagger/OpenAPI
- **URL**: `http://localhost:8000/swagger/`

### Endpoints Principais

#### Clientes
- `GET /api/clients/` - Listar clientes
- `POST /api/clients/` - Criar cliente
- `GET /api/clients/{id}/` - Obter cliente específico
- `PUT /api/clients/{id}/` - Atualizar cliente
- `DELETE /api/clients/{id}/` - Deletar cliente

#### Equipe
- `GET /api/team/` - Listar membros da equipe
- `POST /api/team/` - Criar membro da equipe
- `GET /api/team/{id}/` - Obter membro específico
- `PUT /api/team/{id}/` - Atualizar membro
- `DELETE /api/team/{id}/` - Deletar membro

#### Serviços
- `GET /api/services/` - Listar serviços
- `POST /api/services/` - Criar serviço
- `GET /api/services/{id}/` - Obter serviço específico
- `PUT /api/services/{id}/` - Atualizar serviço
- `DELETE /api/services/{id}/` - Deletar serviço

#### Agendamentos
- `GET /api/appointments/` - Listar agendamentos
- `POST /api/appointments/` - Criar agendamento
- `GET /api/appointments/{id}/` - Obter agendamento específico
- `PUT /api/appointments/{id}/` - Atualizar agendamento
- `DELETE /api/appointments/{id}/` - Deletar agendamento

## 🗂️ Estrutura do Projeto

```
salao-backend/
├── apps/                    # Aplicações Django
│   ├── appointments/        # Gestão de agendamentos
│   ├── clients/            # Gestão de clientes
│   ├── services/           # Gestão de serviços
│   └── team/               # Gestão da equipe
├── core/                   # Configurações principais
│   ├── settings.py         # Configurações Django
│   ├── urls.py            # URLs principais
│   └── wsgi.py            # WSGI config
├── media/                  # Arquivos de mídia
├── staticfiles/           # Arquivos estáticos
├── .env.example           # Exemplo de variáveis de ambiente
├── .gitignore            # Arquivos ignorados pelo Git
├── manage.py             # Script de gerenciamento Django
├── requirements.txt      # Dependências Python
└── README.md            # Este arquivo
```

## 🐳 Docker (Opcional)

### Desenvolvimento com Docker

```bash
# Construir e executar
docker-compose -f docker-compose.dev.yml up --build

# Executar migrações
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

# Criar superusuário
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### Produção com Docker

```bash
docker-compose up --build -d
```

## 🔍 Modelos de Dados

### Cliente
- `name`: Nome completo
- `email`: Email (opcional)
- `phone`: Telefone (11 dígitos)
- `address`: Endereço (opcional)
- `created_at`: Data de criação

### Membro da Equipe
- `name`: Nome completo
- `email`: Email (opcional)
- `phone`: Telefone (11 dígitos)
- `address`: Endereço (opcional)
- `specialties`: Especialidades (ManyToMany com Serviços)
- `created_at`: Data de criação

### Serviço
- `name`: Nome do serviço
- `description`: Descrição (opcional)
- `price`: Preço (decimal)
- `duration_minutes`: Duração em minutos
- `created_at`: Data de criação

### Agendamento
- `client`: Cliente (ForeignKey)
- `team_member`: Profissional (ForeignKey)
- `services`: Serviços (ManyToMany)
- `appointment_date`: Data do agendamento
- `appointment_time`: Horário do agendamento
- `status`: Status (agendado, confirmado, em andamento, concluído, cancelado, não compareceu)
- `total_price`: Preço total
- `notes`: Observações (opcional)
- `created_at`: Data de criação

## 🔧 Validações Especiais

### Telefone Brasileiro
- **Formato**: 11 dígitos (ex: 11987654321)
- **Exibição**: (11) 98765-4321
- **Validação**: Regex `^\d{11}$`

### Preços e Durações
- **Preço**: Deve ser maior que 0
- **Duração**: Deve ser maior que 0 minutos

## 🚀 Deploy

### Variáveis de Ambiente para Produção

```env
SECRET_KEY=sua-chave-secreta-super-segura
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
DATABASE_URL=postgresql://user:password@localhost:5432/salao_db
```

### Comandos de Deploy

```bash
# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Executar migrações
python manage.py migrate

# Executar servidor (use gunicorn em produção)
gunicorn core.wsgi:application
```


## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Entre em contato com a equipe de desenvolvimento

## 🔄 Changelog

### v1.0.0
- ✅ Sistema completo de gestão de salão
- ✅ API REST com Django REST Framework
- ✅ Validação brasileira de telefones
- ✅ Sistema de agendamentos com workflow
- ✅ Documentação Swagger/OpenAPI
- ✅ Suporte a Docker
- ✅ Configuração via variáveis de ambiente
