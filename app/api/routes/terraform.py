"""
Terraform job routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.terraform_schema import TerraformJobCreate, TerraformJobResponse, TerraformGenerateRequest
from app.services.terraform_service import (
    create_terraform_job,
    get_terraform_job,
    get_user_terraform_jobs,
    execute_terraform_job,
    cancel_terraform_job,
    delete_terraform_job,
    generate_terraform_code
)
from app.api.routes.customers import get_customer_from_token

router = APIRouter(prefix="/terraform", tags=["Terraform"])


@router.post("/generate", response_model=dict, status_code=status.HTTP_200_OK)
async def generate_code(
    request: TerraformGenerateRequest,
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Generate Terraform code using AI.
    
    Args:
        request: Generation request with provider, resources, etc.
        db: Database session
        current_customer: Current authenticated customer
        
    Returns:
        Generated Terraform code
    """
    code = await generate_terraform_code(db, request)
    return {
        "terraform_code": code,
        "provider": request.provider,
        "project_name": request.project_name
    }


@router.post("/jobs", response_model=TerraformJobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: TerraformJobCreate,
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Create a Terraform job (without executing).
    
    Args:
        job_data: Terraform job configuration
        db: Database session
        current_customer: Current authenticated customer
        
    Returns:
        Created Terraform job
    """
    return create_terraform_job(db, current_customer.id, job_data)


@router.post("/jobs/{job_id}/execute", response_model=TerraformJobResponse)
def execute_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Execute a pending Terraform job.
    
    Args:
        job_id: Job ID
        db: Database session
        current_customer: Current authenticated customer
        
    Returns:
        Executed job with results
    """
    job = get_terraform_job(db, job_id, current_customer.id)
    return execute_terraform_job(db, job_id)


@router.post("/apply", response_model=TerraformJobResponse, status_code=status.HTTP_201_CREATED)
def apply_terraform(
    job_data: TerraformJobCreate,
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Create and execute a Terraform apply job.
    
    Args:
        job_data: Terraform job configuration
        db: Database session
        current_customer: Current authenticated customer
        
    Returns:
        Created Terraform job
    """
    job = create_terraform_job(db, current_customer.id, job_data)
    # Execute the job asynchronously in production
    executed_job = execute_terraform_job(db, job.id)
    return executed_job


@router.get("/jobs", response_model=List[TerraformJobResponse])
def list_terraform_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Get all Terraform jobs for the current customer.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_customer: Current authenticated customer
        
    Returns:
        List of Terraform jobs
    """
    return get_user_terraform_jobs(db, current_customer.id, skip, limit)


@router.get("/jobs/{job_id}", response_model=TerraformJobResponse)
def get_job_details(
    job_id: int,
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Get Terraform job details by ID.
    
    Args:
        job_id: Job ID
        db: Database session
        current_customer: Current authenticated customer
        
    Returns:
        Terraform job details
    """
    return get_terraform_job(db, job_id, current_customer.id)


@router.get("/logs/{job_id}", response_model=dict)
def get_job_logs(
    job_id: int,
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Get Terraform job logs by ID.
    
    Args:
        job_id: Job ID
        db: Database session
        current_customer: Current authenticated customer
        
    Returns:
        Job logs (output and error)
    """
    job = get_terraform_job(db, job_id, current_customer.id)
    return {
        "job_id": job.id,
        "job_name": job.job_name,
        "status": job.status,
        "output_log": job.output_log,
        "error_log": job.error_log,
        "started_at": job.started_at,
        "completed_at": job.completed_at
    }


@router.patch("/jobs/{job_id}/cancel", response_model=TerraformJobResponse)
def cancel_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Cancel a running Terraform job.
    
    Args:
        job_id: Job ID
        db: Database session
        current_customer: Current authenticated customer
        
    Returns:
        Updated job with cancelled status
    """
    job = get_terraform_job(db, job_id, current_customer.id)
    if job.status not in ['pending', 'running']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job.status}"
        )
    return cancel_terraform_job(db, job_id)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Delete a Terraform job.
    
    Args:
        job_id: Job ID
        db: Database session
        current_customer: Current authenticated customer
    """
    job = get_terraform_job(db, job_id, current_customer.id)
    delete_terraform_job(db, job_id)
