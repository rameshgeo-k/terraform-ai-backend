"""
Admin authentication service.
"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.admin import Admin
from app.schemas.admin_schema import AdminCreate, AdminUpdate
from app.core.security import verify_password, get_password_hash
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def authenticate_admin(db: Session, email: str, password: str) -> Admin:
    """
    Authenticate an admin user.
    
    Args:
        db: Database session
        email: Admin email
        password: Admin password
        
    Returns:
        Admin object if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not verify_password(password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )
    
    return admin


def create_admin(db: Session, admin_data: AdminCreate) -> Admin:
    """
    Create a new admin user.
    
    Args:
        db: Database session
        admin_data: Admin creation data
        
    Returns:
        Created Admin object
        
    Raises:
        HTTPException: If admin already exists
    """
    # Check if admin exists
    existing_admin = db.query(Admin).filter(
        (Admin.email == admin_data.email) | (Admin.username == admin_data.username)
    ).first()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email or username already exists"
        )
    
    # Create admin
    admin = Admin(
        email=admin_data.email,
        username=admin_data.username,
        hashed_password=get_password_hash(admin_data.password),
        full_name=admin_data.full_name,
        is_active=True
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    logger.info(f"Admin created: {admin.email}")
    return admin


def get_all_admin_users(db: Session, skip: int = 0, limit: int = 100) -> List[Admin]:
    """
    Get all admins with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of admins
    """
    return db.query(Admin).offset(skip).limit(limit).all()


def get_admin_by_id(db: Session, admin_id: int) -> Admin:
    """Get admin by ID."""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    return admin


def get_admin_by_email(db: Session, email: str) -> Admin:
    """Get admin by email."""
    return db.query(Admin).filter(Admin.email == email).first()


def update_admin(db: Session, admin_id: int, admin_data: AdminUpdate) -> Admin:
    """
    Update admin information.
    
    Args:
        db: Database session
        admin_id: Admin ID
        admin_data: Updated admin data
        
    Returns:
        Updated admin object
        
    Raises:
        HTTPException: If admin not found
    """
    admin = get_admin_by_id(db, admin_id)
    
    update_data = admin_data.dict(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(admin, field, value)
    
    db.commit()
    db.refresh(admin)
    
    logger.info(f"Admin updated: {admin.email}")
    return admin


def toggle_admin_status(db: Session, admin_id: int, is_active: bool) -> Admin:
    """
    Activate or deactivate admin.
    
    Args:
        db: Database session
        admin_id: Admin ID
        is_active: New active status
        
    Returns:
        Updated admin object
    """
    admin = get_admin_by_id(db, admin_id)
    admin.is_active = is_active
    
    db.commit()
    db.refresh(admin)
    
    status_text = "activated" if is_active else "deactivated"
    logger.info(f"Admin {status_text}: {admin.email}")
    return admin


def delete_admin(db: Session, admin_id: int) -> None:
    """
    Delete admin.
    
    Args:
        db: Database session
        admin_id: Admin ID
        
    Raises:
        HTTPException: If admin not found
    """
    admin = get_admin_by_id(db, admin_id)
    
    db.delete(admin)
    db.commit()
    
    logger.info(f"Admin deleted: {admin.email}")
