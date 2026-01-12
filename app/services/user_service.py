"""
Customer management service.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.security import get_password_hash
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def get_customer_by_id(db: Session, customer_id: int) -> Customer:
    """
    Get customer by ID.
    
    Args:
        db: Database session
        customer_id: Customer ID
        
    Returns:
        Customer object
        
    Raises:
        HTTPException: If customer not found
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


def get_all_customers(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
    """
    Get all customers with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of customers
    """
    return db.query(Customer).offset(skip).limit(limit).all()


def create_customer(db: Session, customer_data: CustomerCreate) -> Customer:
    """
    Create a new customer (admin function).
    
    Args:
        db: Database session
        customer_data: Customer creation data
        
    Returns:
        Created customer object
        
    Raises:
        HTTPException: If customer already exists
    """
    # Check if customer exists
    existing_customer = db.query(Customer).filter(
        (Customer.email == customer_data.email) | (Customer.username == customer_data.username)
    ).first()
    
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email or username already exists"
        )
    
    # Create new customer
    hashed_password = get_password_hash(customer_data.password)
    new_customer = Customer(
        email=customer_data.email,
        username=customer_data.username,
        full_name=customer_data.full_name,
        hashed_password=hashed_password,
        is_active=True
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    logger.info(f"Customer created by admin: {new_customer.email}")
    return new_customer


def update_customer(db: Session, customer_id: int, customer_data: CustomerUpdate) -> Customer:
    """
    Update customer information.
    
    Args:
        db: Database session
        customer_id: Customer ID
        customer_data: Updated customer data
        
    Returns:
        Updated customer object
        
    Raises:
        HTTPException: If customer not found
    """
    customer = get_customer_by_id(db, customer_id)
    
    update_data = customer_data.dict(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    db.commit()
    db.refresh(customer)
    
    logger.info(f"Customer updated: {customer.email}")
    return customer


def toggle_customer_status(db: Session, customer_id: int, is_active: bool) -> Customer:
    """
    Activate or deactivate customer.
    
    Args:
        db: Database session
        customer_id: Customer ID
        is_active: New active status
        
    Returns:
        Updated customer object
    """
    customer = get_customer_by_id(db, customer_id)
    customer.is_active = is_active
    
    db.commit()
    db.refresh(customer)
    
    status_text = "activated" if is_active else "deactivated"
    logger.info(f"Customer {status_text}: {customer.email}")
    return customer


def delete_customer(db: Session, customer_id: int) -> None:
    """
    Delete customer.
    
    Args:
        db: Database session
        customer_id: Customer ID
        
    Raises:
        HTTPException: If customer not found
    """
    customer = get_customer_by_id(db, customer_id)
    
    db.delete(customer)
    db.commit()
    
    logger.info(f"Customer deleted: {customer.email}")
