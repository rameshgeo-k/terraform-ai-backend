"""
Authentication service for customer registration and login.
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.schemas.customer_schema import CustomerCreate, CustomerLogin, Token
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def register_customer(db: Session, customer_data: CustomerCreate) -> Customer:
    """
    Register a new customer.
    
    Args:
        db: Database session
        customer_data: Customer registration data
        
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
        logger.warning(f"Registration attempt for existing customer: {customer_data.email}")
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
        hashed_password=hashed_password
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    logger.info(f"New customer registered: {new_customer.email}")
    return new_customer


def authenticate_customer(db: Session, login_data: CustomerLogin) -> Token:
    """
    Authenticate customer and generate tokens.
    
    Args:
        db: Database session
        login_data: Customer login credentials
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    customer = db.query(Customer).filter(Customer.email == login_data.email).first()
    
    if not customer or not verify_password(login_data.password, customer.hashed_password):
        logger.warning(f"Failed login attempt for: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not customer.is_active:
        logger.warning(f"Login attempt for inactive customer: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is inactive"
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(customer.id)})
    refresh_token = create_refresh_token(data={"sub": str(customer.id)})
    
    logger.info(f"Customer logged in: {customer.email}")
    return Token(access_token=access_token, refresh_token=refresh_token)


def get_current_customer(db: Session, token_payload: dict) -> Customer:
    """
    Get current customer from token payload.
    
    Args:
        db: Database session
        token_payload: Decoded JWT token payload
        
    Returns:
        Current customer object
        
    Raises:
        HTTPException: If customer not found or token invalid
    """
    customer_id = token_payload.get("sub")
    if customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    customer = db.query(Customer).filter(Customer.id == int(customer_id)).first()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer
