"""
Admin routes - includes auth, admin user management, and terraform jobs.
"""
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.admin_schema import AdminLogin, AdminCreate, AdminUpdate, AdminResponse
from app.schemas.customer_schema import Token
from app.schemas.terraform_schema import TerraformJobResponse
from app.services.admin_service import (
    authenticate_admin,
    get_admin_by_id,
    get_all_admin_users,
    create_admin,
    update_admin,
    toggle_admin_status,
    delete_admin
)
from app.services.terraform_service import get_all_terraform_jobs, cancel_terraform_job, delete_terraform_job
from jose import JWTError, jwt
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")


# ============================================================================get_all_admins
# ADMIN AUTHENTICATION (no auth required)
# ============================================================================

@router.post("/admin/login", response_model=Token)
def admin_login(
    credentials: AdminLogin,
    db: Session = Depends(get_db)
):
    """
    Admin login endpoint.
    
    Args:
        credentials: Admin email and password
        db: Database session
        
    Returns:
        Access and refresh tokens
    """
    admin = authenticate_admin(db, credentials.email, credentials.password)
    
    # Create access token with admin identifier
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(admin.id), "type": "admin", "email": admin.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


def get_current_admin(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> AdminResponse:
    """
    Get current admin from token.
    
    Args:
        request: FastAPI request object
        token: JWT token
        db: Database session
        
    Returns:
        Current admin
        
    Raises:
        HTTPException: If token is invalid or admin not found
    """
    # Log headers for debugging
    auth_header = request.headers.get("Authorization")
    logger.info(f"Authorization header: {auth_header}")
    logger.info(f"Token from oauth2_scheme: {token[:20] if token else 'None'}...")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        admin_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if admin_id is None or token_type != "admin":
            raise credentials_exception
            
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    admin = get_admin_by_id(db, int(admin_id))
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )
    
    return admin


@router.get("/admin/me", response_model=AdminResponse)
def get_admin_info(
    admin = Depends(get_current_admin)
):
    """
    Get current admin information.
    
    Args:
        admin: Current authenticated admin
        
    Returns:
        Current admin information
    """
    return admin


# ============================================================================
# ADMIN USER MANAGEMENT (admin auth required)
# ============================================================================

@router.get("/admin/users", response_model=List[AdminResponse])
def list_all_admins(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Get all admin users (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        admin: Current admin user
        
    Returns:
        List of all admin users
    """
    return get_all_admin_users(db, skip, limit)


@router.get("/admin/users/{admin_id}", response_model=AdminResponse)
def get_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Get a specific admin user by ID (admin only).
    
    Args:
        admin_id: Admin user ID
        db: Database session
        admin: Current admin user
        
    Returns:
        Admin user information
    """
    return get_admin_by_id(db, admin_id)


@router.post("/admin/users", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def create_new_admin(
    admin_data: AdminCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Create a new admin user (admin only).
    
    Args:
        admin_data: Admin creation data
        db: Database session
        admin: Current admin user
        
    Returns:
        Created admin user information
    """
    return create_admin(db, admin_data)


@router.put("/admin/users/{admin_id}", response_model=AdminResponse)
def update_admin_info(
    admin_id: int,
    admin_data: AdminUpdate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Update admin user information (admin only).
    
    Args:
        admin_id: Admin user ID
        admin_data: Updated admin data
        db: Database session
        admin: Current admin user
        
    Returns:
        Updated admin user information
    """
    return update_admin(db, admin_id, admin_data)


@router.patch("/admin/users/{admin_id}/activate", response_model=AdminResponse)
def activate_admin_user(
    admin_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Activate an admin user account (admin only).
    
    Args:
        admin_id: Admin user ID to activate
        db: Database session
        admin: Current admin user
        
    Returns:
        Updated admin user information
    """
    return toggle_admin_status(db, admin_id, True)


@router.patch("/admin/users/{admin_id}/deactivate", response_model=AdminResponse)
def deactivate_admin_user(
    admin_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Deactivate an admin user account (admin only).
    
    Args:
        admin_id: Admin user ID to deactivate
        db: Database session
        admin: Current admin user
        
    Returns:
        Updated admin user information
    """
    return toggle_admin_status(db, admin_id, False)


@router.delete("/admin/users/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_account(
    admin_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Delete an admin user account (admin only).
    
    Args:
        admin_id: Admin user ID to delete
        db: Database session
        admin: Current admin user
    """
    delete_admin(db, admin_id)


# ============================================================================
# TERRAFORM JOB MANAGEMENT (admin auth required)
# ============================================================================

@router.get("/admin/terraform", response_model=List[TerraformJobResponse])
def list_all_terraform_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Get all Terraform jobs (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        admin: Current admin user
        
    Returns:
        List of all Terraform jobs
    """
    return get_all_terraform_jobs(db, skip, limit)


@router.patch("/admin/terraform/{job_id}/cancel", response_model=TerraformJobResponse)
def cancel_job(
    job_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Cancel a running Terraform job (admin only).
    
    Args:
        job_id: Job ID to cancel
        db: Database session
        admin: Current admin user
        
    Returns:
        Updated Terraform job
    """
    return cancel_terraform_job(db, job_id)


@router.delete("/admin/terraform/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Delete a Terraform job (admin only).
    
    Args:
        job_id: Job ID to delete
        db: Database session
        admin: Current admin user
    """
    delete_terraform_job(db, job_id)
