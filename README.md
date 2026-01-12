# InfraPilot Backend

A production-ready FastAPI backend for InfraPilot, providing infrastructure management, AI integration, and Terraform automation.

## Features

- 🔐 **JWT-based Authentication** - Secure user registration and login with role-based access control
- 👥 **User Management** - Admin panel for managing users and permissions
- 🤖 **AI Model Configuration** - Manage Chat AI and Terraform AI model settings
- 🏗️ **Terraform Integration** - Execute and monitor infrastructure automation jobs
- 📊 **Admin Dashboard** - Web-based admin panel for system management
- 🔄 **RESTful API** - Clean, modular API design with comprehensive documentation
- ✅ **Unit Tests** - Test coverage for core functionality
- 🗄️ **PostgreSQL Database** - SQLAlchemy ORM with Alembic migrations

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL with SQLAlchemy 2.x
- **Authentication**: JWT with passlib (bcrypt)
- **Server**: Uvicorn
- **Testing**: Pytest
- **Validation**: Pydantic 2.x

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── users.py        # User profile endpoints
│   │       ├── models.py       # Model configuration endpoints
│   │       ├── terraform.py    # Terraform job endpoints
│   │       └── admin.py        # Admin management endpoints
│   ├── core/
│   │   ├── config.py           # Application configuration
│   │   ├── database.py         # Database connection
│   │   ├── security.py         # JWT and password utilities
│   │   └── utils.py            # Helper functions
│   ├── models/
│   │   ├── user.py             # User database model
│   │   ├── model_config.py     # AI model configuration model
│   │   └── terraform_job.py    # Terraform job model
│   ├── schemas/
│   │   ├── user_schema.py      # User Pydantic schemas
│   │   ├── model_schema.py     # Model config schemas
│   │   └── terraform_schema.py # Terraform job schemas
│   ├── services/
│   │   ├── auth_service.py     # Authentication logic
│   │   ├── user_service.py     # User management logic
│   │   ├── model_service.py    # Model configuration logic
│   │   └── terraform_service.py # Terraform job logic
│   ├── admin/
│   │   └── routes.py           # Admin panel routes
│   └── tests/
│       ├── test_auth.py        # Authentication tests
│       ├── test_users.py       # User tests
│       └── test_terraform.py   # Terraform tests
├── .env.example                # Example environment variables
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Installation

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update the following:
   - `DATABASE_URL`: PostgreSQL connection string
   - `JWT_SECRET_KEY`: Generate a secure random key
   - `ADMIN_EMAIL`: Admin user email
   - `ADMIN_PASSWORD`: Admin user password

5. **Create PostgreSQL database**
   ```bash
   createdb infrapilot
   # Or using psql:
   # psql -U postgres -c "CREATE DATABASE infrapilot;"
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```
   
   Or to initialize without migrations:
   ```bash
   python -c "from app.core.database import init_db; init_db()"
   ```

## Running the Application

### Development Mode

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m app.main
```

The application will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Admin Panel**: http://localhost:8000/admin/panel

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT tokens

### Users
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update current user profile

### Model Configurations (Admin)
- `POST /api/models/` - Create model configuration
- `GET /api/models/` - List all model configurations
- `GET /api/models/{id}` - Get model configuration by ID
- `PUT /api/models/{id}` - Update model configuration
- `DELETE /api/models/{id}` - Delete model configuration

### Terraform
- `POST /api/terraform/apply` - Create and execute Terraform job
- `GET /api/terraform/jobs` - List user's Terraform jobs
- `GET /api/terraform/jobs/{id}` - Get job details
- `GET /api/terraform/logs/{id}` - Get job logs

### Admin
- `GET /api/admin/users` - List all users
- `PATCH /api/admin/users/{id}/activate` - Activate user
- `PATCH /api/admin/users/{id}/deactivate` - Deactivate user
- `DELETE /api/admin/users/{id}` - Delete user
- `GET /api/admin/terraform` - List all Terraform jobs

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py

# Run with verbose output
pytest -v
```

## Database Migrations (with Alembic)

### Initial Setup (Already Configured)

The project comes with Alembic already configured:
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment setup
- `alembic/versions/001_initial.py` - Initial migration creating all tables

### Migration Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# View migration history
alembic history --verbose

# Create a new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Upgrade to specific version
alembic upgrade <revision_id>
```

### Creating New Migrations

When you modify models (add/remove columns, change types, etc.):

```bash
# 1. Make changes to your models in app/models/

# 2. Generate migration automatically
alembic revision --autogenerate -m "Add new column to users"

# 3. Review the generated migration in alembic/versions/

# 4. Apply the migration
alembic upgrade head
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Required |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | 7 |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost:3000 |
| `DEBUG` | Enable debug mode | True |
| `ENVIRONMENT` | Environment name | development |
| `LOG_LEVEL` | Logging level | INFO |

## Creating Admin User

After first run, create an admin user:

```python
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

db = SessionLocal()
admin = User(
    email="admin@infrapilot.com",
    username="admin",
    hashed_password=get_password_hash("admin123"),
    role=UserRole.ADMIN,
    is_active=True
)
db.add(admin)
db.commit()
```

## Security Considerations

- Change default `JWT_SECRET_KEY` in production
- Use strong passwords for admin accounts
- Enable HTTPS in production
- Configure appropriate CORS origins
- Regularly update dependencies
- Use environment-specific configuration files

## Development

### Code Style

```bash
# Format code with black
black app/

# Lint with flake8
flake8 app/

# Type checking with mypy
mypy app/
```

### Adding New Routes

1. Create route file in `app/api/routes/`
2. Import and include router in `app/main.py`
3. Add corresponding service logic in `app/services/`
4. Create tests in `app/tests/`

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Ensure database exists

### Import Errors
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### JWT Token Issues
- Verify `JWT_SECRET_KEY` is set
- Check token expiration settings

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please create an issue in the GitHub repository.

## Contributors

InfraPilot Development Team