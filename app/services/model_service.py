"""
Model configuration service.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.model_config import ModelConfig
from app.schemas.model_schema import ModelConfigCreate, ModelConfigUpdate
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def create_model_config(db: Session, config_data: ModelConfigCreate) -> ModelConfig:
    """
    Create a new model configuration.
    
    Args:
        db: Database session
        config_data: Model configuration data
        
    Returns:
        Created model configuration
        
    Raises:
        HTTPException: If configuration with name already exists or if trying to create
                       multiple active models of the same type
    """
    existing_config = db.query(ModelConfig).filter(ModelConfig.name == config_data.name).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model configuration with name '{config_data.name}' already exists"
        )
    
    # If setting as active, deactivate other models of the same type
    if config_data.is_active:
        existing_active = db.query(ModelConfig).filter(
            ModelConfig.model_type == config_data.model_type,
            ModelConfig.is_active == True
        ).all()
        
        if existing_active:
            for model in existing_active:
                model.is_active = False
            logger.info(f"Deactivated {len(existing_active)} existing {config_data.model_type} model(s)")
    
    new_config = ModelConfig(**config_data.dict())
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    
    logger.info(f"Model configuration created: {new_config.name} (Active: {new_config.is_active})")
    return new_config


def get_model_config(db: Session, config_id: int) -> ModelConfig:
    """
    Get model configuration by ID.
    
    Args:
        db: Database session
        config_id: Configuration ID
        
    Returns:
        Model configuration
        
    Raises:
        HTTPException: If configuration not found
    """
    config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found"
        )
    return config


def get_all_model_configs(db: Session, skip: int = 0, limit: int = 100) -> List[ModelConfig]:
    """
    Get all model configurations.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of model configurations
    """
    return db.query(ModelConfig).offset(skip).limit(limit).all()


def update_model_config(db: Session, config_id: int, config_data: ModelConfigUpdate) -> ModelConfig:
    """
    Update model configuration.
    
    Args:
        db: Database session
        config_id: Configuration ID
        config_data: Updated configuration data
        
    Returns:
        Updated model configuration
    """
    config = get_model_config(db, config_id)
    
    update_data = config_data.dict(exclude_unset=True)
    
    # If activating this model, deactivate other models of the same type
    if 'is_active' in update_data and update_data['is_active'] is True:
        # Get the model_type (either from update or existing config)
        model_type = update_data.get('model_type', config.model_type)
        
        existing_active = db.query(ModelConfig).filter(
            ModelConfig.id != config_id,  # Exclude current model
            ModelConfig.model_type == model_type,
            ModelConfig.is_active == True
        ).all()
        
        if existing_active:
            for model in existing_active:
                model.is_active = False
            logger.info(f"Deactivated {len(existing_active)} existing {model_type} model(s)")
    
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    logger.info(f"Model configuration updated: {config.name} (Active: {config.is_active})")
    return config


def delete_model_config(db: Session, config_id: int) -> None:
    """
    Delete model configuration.
    
    Args:
        db: Database session
        config_id: Configuration ID
    """
    config = get_model_config(db, config_id)
    
    db.delete(config)
    db.commit()
    
    logger.info(f"Model configuration deleted: {config.name}")
