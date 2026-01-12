# Copilot Instructions for InfraPilot (Backend)

You are an expert backend engineer helping me generate a clean, production-ready FastAPI backend for a project called **InfraPilot**.

### Goal:
Create the initial backend structure with:
- Admin Panel (for managing users, models, terraform jobs)
- Auth (JWT-based)
- API routes (modular)
- Config loading (dotenv or AWS Secrets Manager)
- SQLAlchemy ORM for database
- Alembic for migrations
- Unit test stubs

### Stack:
- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Uvicorn
- Passlib (for password hashing)
- PyJWT
- FastAPI-Admin (simple admin UI)
- Pydantic for schema validation
- PostgreSQL
- Directory structure should follow clean architecture

### Project Name:
`infra_pilot_backend`

### Folder Structure:
backend/
│
├── app/
│ ├── main.py
│ ├── api/
│ │ ├── routes/
│ │ │ ├── auth.py
│ │ │ ├── admin.py
│ │ │ ├── users.py
│ │ │ ├── models.py
│ │ │ └── terraform.py
│ ├── core/
│ │ ├── config.py
│ │ ├── security.py
│ │ ├── database.py
│ │ └── utils.py
│ ├── models/
│ │ ├── user.py
│ │ ├── model_config.py
│ │ ├── terraform_job.py
│ ├── schemas/
│ │ ├── user_schema.py
│ │ ├── model_schema.py
│ │ ├── terraform_schema.py
│ ├── services/
│ │ ├── auth_service.py
│ │ ├── user_service.py
│ │ ├── terraform_service.py
│ │ └── model_service.py
│ ├── admin/
│ │ ├── templates/
│ │ └── routes.py
│ └── tests/
│ ├── test_auth.py
│ ├── test_users.py
│ └── test_terraform.py
│
├── alembic/
│ ├── versions/
│ │ └── 001_initial.py
│ ├── env.py
│ ├── script.py.mako
│ └── README
│
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md


### Functional Requirements:
1. **Auth**
   - `/auth/register`, `/auth/login` endpoints
   - JWT access/refresh tokens
   - Password hashing (bcrypt)
   - Role-based access (user/admin)

2. **Admin**
   - `/admin/users` → list, activate/deactivate
   - `/admin/models` → view/edit model configurations (Chat AI, Terraform AI)
   - `/admin/terraform` → list terraform jobs, status

3. **User**
   - `/users/me` → view own profile
   - `/users/update` → update info

4. **Terraform**
   - `/terraform/apply` → accept config JSON, mock apply
   - `/terraform/jobs` → list jobs
   - `/terraform/logs/{id}` → view logs

### Config Requirements:
- Load `.env` using python-dotenv
- DB connection from `DATABASE_URL`
- JWT secret from env
- CORS for localhost:3000 (frontend)
- Logging configuration

### Admin UI (Optional MVP)
- Integrate FastAPI-Admin
- Basic CRUD view for User, ModelConfig, TerraformJob tables
- Protect with admin login

### Include:
- Swagger docs
- Example tests with pytest
- Example .env content
- Alembic migrations setup with initial migration

### Database Migrations (Alembic):
1. **Setup**
   - `alembic.ini` configured with DATABASE_URL from settings
   - `alembic/env.py` imports all models and sets target_metadata
   - `alembic/versions/` contains migration scripts

2. **Commands**
   - `alembic revision --autogenerate -m "message"` - Create new migration
   - `alembic upgrade head` - Apply all pending migrations
   - `alembic downgrade -1` - Rollback last migration
   - `alembic current` - Show current migration version
   - `alembic history` - Show migration history

3. **Initial Migration**
   - Creates users table with UserRole enum (user/admin)
   - Creates model_configs table for AI model configurations
   - Creates terraform_jobs table with JobStatus enum
   - Includes all foreign keys and indexes