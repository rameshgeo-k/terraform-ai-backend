"""
Customer routes - includes auth, profile management, and admin CRUD.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.customer_schema import CustomerCreate, CustomerLogin, CustomerUpdate, CustomerResponse, Token
from app.services.user_service import (
    get_all_customers, 
    get_customer_by_id,
    create_customer,
    update_customer,
    toggle_customer_status, 
    delete_customer
)
from app.services.auth_service import register_customer, authenticate_customer, get_current_customer
from app.api.routes.admin import get_current_admin

router = APIRouter(tags=["Customers"])


# ============================================================================
# PUBLIC ROUTES - Customer Authentication (no auth required)
# ============================================================================

@router.post("/customers/register", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def register(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    """
    Register a new customer (public).
    
    Args:
        customer_data: Customer registration data
        db: Database session
        
    Returns:
        Created customer information
    """
    return register_customer(db, customer_data)


@router.post("/customers/login", response_model=Token)
def login(login_data: CustomerLogin, db: Session = Depends(get_db)):
    """
    Authenticate customer and return JWT tokens (public).
    
    Args:
        login_data: Customer login credentials
        db: Database session
        
    Returns:
        Access and refresh tokens
    """
    return authenticate_customer(db, login_data)


# ============================================================================
# CUSTOMER ROUTES - Self-service profile management (customer auth required)
# ============================================================================

def get_customer_from_token(authorization: str = Header(...), db: Session = Depends(get_db)):
    """Dependency to get current customer from authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return get_current_customer(db, payload)


@router.get("/customers/me", response_model=CustomerResponse)
def get_current_customer_profile(current_customer = Depends(get_customer_from_token)):
    """
    Get current customer's profile.
    
    Args:
        current_customer: Current authenticated customer
        
    Returns:
        Customer profile information
    """
    return current_customer


@router.put("/customers/me", response_model=CustomerResponse)
def update_current_customer_profile(
    customer_data: CustomerUpdate,
    current_customer = Depends(get_customer_from_token),
    db: Session = Depends(get_db)
):
    """
    Update current customer's profile.
    
    Args:
        customer_data: Updated customer data
        current_customer: Current authenticated customer
        db: Database session
        
    Returns:
        Updated customer information
    """
    return update_customer(db, current_customer.id, customer_data)


# ============================================================================
# ADMIN ROUTES - Customer management CRUD (admin auth required)
# ============================================================================

@router.get("/customers", response_model=List[CustomerResponse])
def list_all_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Get all customers (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        admin: Current admin user
        
    Returns:
        List of all customers
    """
    return get_all_customers(db, skip, limit)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Get a specific customer by ID (admin only).
    
    Args:
        customer_id: Customer ID
        db: Database session
        admin: Current admin user
        
    Returns:
        Customer information
    """
    return get_customer_by_id(db, customer_id)


@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_new_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Create a new customer (admin only).
    
    Args:
        customer_data: Customer creation data
        db: Database session
        admin: Current admin user
        
    Returns:
        Created customer information
    """
    return create_customer(db, customer_data)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer_info(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Update customer information (admin only).
    
    Args:
        customer_id: Customer ID
        customer_data: Updated customer data
        db: Database session
        admin: Current admin user
        
    Returns:
        Updated customer information
    """
    return update_customer(db, customer_id, customer_data)


@router.patch("/customers/{customer_id}/activate", response_model=CustomerResponse)
def activate_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Activate a customer account (admin only).
    
    Args:
        customer_id: Customer ID to activate
        db: Database session
        admin: Current admin user
        
    Returns:
        Updated customer information
    """
    return toggle_customer_status(db, customer_id, True)


@router.patch("/customers/{customer_id}/deactivate", response_model=CustomerResponse)
def deactivate_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Deactivate a customer account (admin only).
    
    Args:
        customer_id: Customer ID to deactivate
        db: Database session
        admin: Current admin user
        
    Returns:
        Updated customer information
    """
    return toggle_customer_status(db, customer_id, False)


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_account(
    customer_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Delete a customer account (admin only).
    
    Args:
        customer_id: Customer ID to delete
        db: Database session
        admin: Current admin user
    """
    delete_customer(db, customer_id)
