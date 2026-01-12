Backend Copilot Instructions

## Project Overview
This backend is a Python FastAPI application structured for modularity and scalability. Key folders include:
- `app/api/v1/endpoints/`: API route handlers
- `app/services/`: Business logic and integrations
- `app/core/`: Configuration and logging
- `app/schemas/`: Pydantic models for requests/responses
- `app/utils/`: Utility functions
- `chroma/`: Local database (SQLite)
- `config/`: YAML configuration files
- `tests/`: Pytest-based test suite

## Setup & Development
- Use a virtual environment (`python3 -m venv .venv`) and install dependencies from `requirements.txt`.
- Run the server with `uvicorn app.main:app --reload`.
- Follow PEP8 and type hints for all Python code.
- Place new API endpoints in `app/api/v1/endpoints/` and register them in `router.py`.
- Add new business logic to `app/services/`.
- Use Pydantic models in `app/schemas/` for request/response validation.
- Store configuration in `config/server_config.yaml`.

## Copilot Usage Guidance
- Use Copilot for boilerplate, endpoint scaffolding, and utility functions.
- Request code reviews for complex logic or integrations.
- Document new features in `docs/` and update `README.md` as needed.
- Write and run tests for all new features (`pytest`).

## Contribution Conventions
- Use clear, descriptive commit messages.
- Ensure all code passes linting and tests before PRs.
- Update dependencies in `requirements.txt` when adding new packages.

---
