"""
Application configuration module.
Loads settings from environment variables using pydantic-settings.
"""
from typing import Annotated, Any
from pydantic_settings import BaseSettings
from pydantic import AnyUrl, BeforeValidator, computed_field


def parse_cors(v: Any) -> list[str] | str:
    """Parse BACKEND_CORS_ORIGINS environment variable."""
    if isinstance(v, str) and not v.startswith("["):
        parts = [i.strip() for i in v.split(",") if i.strip()]
        normalized: list[str] = []
        for p in parts:
            # leave absolute (http/https) and relative paths (starting with '/') as-is
            if p.startswith(("http://", "https://", "/")):
                normalized.append(p)
            else:
                # If scheme missing, assume http://
                normalized.append("http://" + p)
        return normalized
    elif isinstance(v, list) or isinstance(v, str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "InfraPilot Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.CORS_ORIGINS]

    # Admin
    ADMIN_EMAIL: str = "admin@infrapilot.com"
    ADMIN_PASSWORD: str = "admin123"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"  # "text" or "json"
    LOG_DIRECTORY: str = "logs"
    
    # AWS (Optional - for Bedrock AI models)
    # AWS_REGION is now configured per-model in the database parameters
    # This is only used as a fallback if not specified in model config
    AWS_REGION: str = "us-west-2"
    AWS_SECRET_NAME: str = ""
    AWS_PROFILE_ARN: str = ""
    BEDROCK_MODEL_PROVIDER: str = "anthropic"
    
    # Ollama Configuration (Optional - for local AI models)
    OLLAMA_BASE_URL: str = "http://localhost:11434"  # Default Ollama URL
    OLLAMA_MODEL: str = "llama3.2"  # Default Ollama model
    
    # Server Configuration
    API_PORT: int = 8000  # Port for the FastAPI backend
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
