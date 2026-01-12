#!/usr/bin/env python3
"""
Script to add Ollama model configuration to the database.
"""
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.model_config import ModelConfig
import app.models  # Import all models to ensure they're registered


def add_ollama_model(
    name: str = "Ollama Chat",
    model_identifier: str = "llama3.2",
    model_type: str = "chat",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    is_active: bool = False,
):
    """
    Add or update Ollama model configuration in the database.
    
    Args:
        name: Model display name
        model_identifier: Ollama model ID (e.g., 'llama3.2', 'mistral', 'codellama')
        model_type: Type of model ('chat', 'terraform', or 'both')
        base_url: Ollama server URL
        temperature: Model temperature
        max_tokens: Maximum tokens to generate
        is_active: Whether to set this as the active model
    """
    db: Session = SessionLocal()
    
    try:
        # Check if model already exists
        existing_model = db.query(ModelConfig).filter(
            ModelConfig.name == name
        ).first()
        
        if existing_model:
            print(f"⚠️  Model '{name}' already exists. Updating...")
            existing_model.model_type = model_type
            existing_model.provider = "ollama"
            existing_model.model_identifier = model_identifier
            existing_model.api_endpoint = base_url
            existing_model.parameters = {
                "base_url": base_url,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            existing_model.is_active = is_active
            existing_model.description = f"Ollama local model ({model_identifier})"
            
            db.commit()
            print(f"✅ Updated Ollama model: {name}")
        else:
            # Create new model
            model = ModelConfig(
                name=name,
                model_type=model_type,
                provider="ollama",
                model_identifier=model_identifier,
                api_endpoint=base_url,
                api_key_name=None,  # Ollama doesn't require API keys
                parameters={
                    "base_url": base_url,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                description=f"Ollama local model ({model_identifier})",
                is_active=is_active,
            )
            
            db.add(model)
            db.commit()
            db.refresh(model)
            
            print(f"✅ Added Ollama model: {name} (ID: {model.id})")
        
        # Display current active models
        print("\n📋 Current Active Models:")
        active_models = db.query(ModelConfig).filter(ModelConfig.is_active == True).all()
        
        if active_models:
            for m in active_models:
                print(f"  - {m.name} ({m.provider}/{m.model_identifier}) - Type: {m.model_type}")
        else:
            print("  No active models configured")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        db.close()


def list_ollama_models():
    """List all available Ollama models from the server."""
    import requests
    from app.core.config import settings
    
    try:
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            
            if models:
                print(f"\n🤖 Available Ollama models at {settings.OLLAMA_BASE_URL}:")
                for model in models:
                    print(f"  - {model.get('name')}")
            else:
                print("\n⚠️  No Ollama models found. Pull a model first:")
                print("    ollama pull llama3.2")
        else:
            print(f"\n❌ Could not connect to Ollama at {settings.OLLAMA_BASE_URL}")
            print("   Make sure Ollama is running: ollama serve")
    except Exception as e:
        print(f"\n⚠️  Could not list Ollama models: {str(e)}")
        print("   Make sure Ollama is installed and running")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add Ollama model configuration")
    parser.add_argument("--name", default="Ollama Chat", help="Model display name")
    parser.add_argument("--model", default="llama3.2", help="Ollama model identifier")
    parser.add_argument("--type", default="chat", choices=["chat", "terraform", "both"], 
                        help="Model type")
    parser.add_argument("--url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--temperature", type=float, default=0.7, help="Model temperature")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Maximum tokens")
    parser.add_argument("--active", action="store_true", help="Set as active model")
    parser.add_argument("--list", action="store_true", help="List available Ollama models")
    
    args = parser.parse_args()
    
    if args.list:
        list_ollama_models()
    else:
        print(f"\n🔧 Adding Ollama model configuration...")
        add_ollama_model(
            name=args.name,
            model_identifier=args.model,
            model_type=args.type,
            base_url=args.url,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            is_active=args.active,
        )
