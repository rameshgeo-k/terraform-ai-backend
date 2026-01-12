"""
Application Configuration
Centralized settings management using Pydantic
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
from pathlib import Path
import yaml


class ServerSettings(BaseSettings):
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    log_level: str = "info"


class ModelSettings(BaseSettings):
    """Model configuration"""
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "terraform-codellama"
    timeout: int = 300
    keep_alive: str = "5m"


class InferenceSettings(BaseSettings):
    """Inference configuration"""
    default_max_tokens: int = 512
    default_temperature: float = 0.7
    default_top_p: float = 0.9
    default_top_k: int = 50
    max_prompt_length: int = 4096
    stream_chunk_size: int = 1


class RAGSettings(BaseSettings):
    """RAG configuration"""
    chroma_persist_directory: str = "./chroma"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    default_top_k: int = 3
    chunk_size: int = 512
    chunk_overlap: int = 50
    collection_name: str = "documents"


class SecuritySettings(BaseSettings):
    """Security configuration"""
    cors_origins: List[str] = ["*"]
    max_request_size: int = 10485760  # 10MB
    request_timeout: int = 300


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    directory: str = "./logs"
    level: str = "info"
    format: str = "json"
    rotation: str = "1 day"
    retention: str = "30 days"


class Settings(BaseSettings):
    """Main application settings"""
    
    # Application info
    app_name: str = "Terraform AI Assistant"
    app_version: str = "1.0.0"
    
    # Sub-configurations
    server: ServerSettings = ServerSettings()
    model: ModelSettings = ModelSettings()
    inference: InferenceSettings = InferenceSettings()
    rag: RAGSettings = RAGSettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @classmethod
    def from_yaml(cls, config_path: str = "config/server_config.yaml") -> "Settings":
        """Load settings from YAML file"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            # Return default settings if config file doesn't exist
            return cls()
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls(
            server=ServerSettings(**config_data.get('server', {})),
            model=ModelSettings(**config_data.get('model', {})),
            inference=InferenceSettings(**config_data.get('inference', {})),
            rag=RAGSettings(**config_data.get('rag', {})),
            security=SecuritySettings(**config_data.get('security', {})),
            logging=LoggingSettings(**config_data.get('logging', {}))
        )


# Global settings instance
settings = Settings.from_yaml()
