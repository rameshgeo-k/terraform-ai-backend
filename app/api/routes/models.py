"""
Model configuration routes (admin only).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.model_schema import ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse
from app.services.model_service import (
    create_model_config,
    get_model_config,
    get_all_model_configs,
    update_model_config,
    delete_model_config
)
from app.api.routes.admin import get_current_admin

router = APIRouter(prefix="/models", tags=["Model Configurations"])


@router.post("/", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
def create_model(
    config_data: ModelConfigCreate,
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin)
):
    """
    Create a new model configuration (admin only).
    
    Args:
        config_data: Model configuration data
        db: Database session
        admin_user: Current admin user
        
    Returns:
        Created model configuration
    """
    return create_model_config(db, config_data)


@router.get("/", response_model=List[ModelConfigResponse])
def list_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin)
):
    """
    Get all model configurations (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        admin_user: Current admin user
        
    Returns:
        List of model configurations
    """
    return get_all_model_configs(db, skip, limit)


@router.get("/{config_id}", response_model=ModelConfigResponse)
def get_model(
    config_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin)
):
    """
    Get model configuration by ID (admin only).
    
    Args:
        config_id: Configuration ID
        db: Database session
        admin_user: Current admin user
        
    Returns:
        Model configuration
    """
    return get_model_config(db, config_id)


@router.put("/{config_id}", response_model=ModelConfigResponse)
def update_model(
    config_id: int,
    config_data: ModelConfigUpdate,
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin)
):
    """
    Update model configuration (admin only).
    
    Args:
        config_id: Configuration ID
        config_data: Updated configuration data
        db: Database session
        admin_user: Current admin user
        
    Returns:
        Updated model configuration
    """
    return update_model_config(db, config_id, config_data)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    config_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin)
):
    """
    Delete model configuration (admin only).
    
    Args:
        config_id: Configuration ID
        db: Database session
        admin_user: Current admin user
    """
    delete_model_config(db, config_id)
