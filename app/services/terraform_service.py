"""
Terraform job service for managing infrastructure operations.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.terraform_job import TerraformJob, JobStatus
from app.schemas.terraform_schema import TerraformJobCreate, TerraformJobUpdate, TerraformGenerateRequest
from app.core.utils import parse_terraform_output
from app.utils.logging_utils import setup_logger
from app.services.ai.terraform_generator import generate_terraform_code as ai_generate_terraform

logger = setup_logger(__name__)


async def generate_terraform_code(db: Session, request: TerraformGenerateRequest) -> str:
    """
    Generate Terraform code using LangChain AI.
    
    Args:
        db: Database session
        request: Generation request with provider and resources
        
    Returns:
        Generated Terraform code as string
    """
    # Try AI generation first
    try:
        ai_code = await ai_generate_terraform(db, request)
        if ai_code:
            logger.info(f"Generated Terraform code using AI for project: {request.project_name}")
            return ai_code
    except Exception as e:
        logger.warning(f"AI generation failed, using template: {str(e)}")
    
    # Fallback to template-based generation
    logger.info(f"Using template generation for project: {request.project_name}")
    return _generate_template_code(request)


def _generate_template_code(request: TerraformGenerateRequest) -> str:
    """
    Generate template-based Terraform code (fallback).
    
    Args:
        request: Generation request
        
    Returns:
        Template-generated code
    """
    provider = request.provider
    project_name = request.project_name
    resources = request.resources
    
    # Generate provider block
    code = f'# {project_name}\n'
    if request.description:
        code += f'# {request.description}\n'
    code += '\n'
    
    if provider == 'aws':
        code += '''terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

'''
        # Generate AWS resources
        for resource in resources:
            if resource.type == 'ec2':
                code += f'''resource "aws_instance" "{resource.id}" {{
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  
  tags = {{
    Name = "{project_name}-{resource.label}"
  }}
}}

'''
            elif resource.type == 's3':
                code += f'''resource "aws_s3_bucket" "{resource.id}" {{
  bucket = "{project_name}-{resource.id}"
  
  tags = {{
    Name = "{project_name}-{resource.label}"
  }}
}}

'''
            elif resource.type == 'vpc':
                code += f'''resource "aws_vpc" "{resource.id}" {{
  cidr_block = "10.0.0.0/16"
  
  tags = {{
    Name = "{project_name}-{resource.label}"
  }}
}}

'''
            elif resource.type == 'rds':
                code += f'''resource "aws_db_instance" "{resource.id}" {{
  allocated_storage    = 20
  engine              = "mysql"
  engine_version      = "8.0"
  instance_class      = "db.t3.micro"
  db_name             = "{project_name.replace('-', '_')}"
  username            = "admin"
  password            = "changeme123"
  skip_final_snapshot = true
  
  tags = {{
    Name = "{project_name}-{resource.label}"
  }}
}}

'''
    
    elif provider == 'azure':
        code += '''terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "''' + project_name + '''-rg"
  location = "East US"
}

'''
        for resource in resources:
            if resource.type == 'vm':
                code += f'''resource "azurerm_virtual_machine" "{resource.id}" {{
  name                  = "{project_name}-{resource.id}"
  location              = azurerm_resource_group.main.location
  resource_group_name   = azurerm_resource_group.main.name
  vm_size              = "Standard_B1s"
  
  # Additional configuration needed
}}

'''
    
    elif provider == 'gcp':
        code += '''terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "my-project-id"
  region  = "us-central1"
}

'''
        for resource in resources:
            if resource.type == 'compute_instance':
                code += f'''resource "google_compute_instance" "{resource.id}" {{
  name         = "{project_name}-{resource.id}"
  machine_type = "e2-micro"
  zone         = "us-central1-a"
  
  boot_disk {{
    initialize_params {{
      image = "debian-cloud/debian-11"
    }}
  }}
  
  network_interface {{
    network = "default"
  }}
}}

'''
    
    return code


def create_terraform_job(db: Session, customer_id: int, job_data: TerraformJobCreate) -> TerraformJob:
    """
    Create a new Terraform job.
    
    Args:
        db: Database session
        customer_id: Customer ID creating the job
        job_data: Terraform job data
        
    Returns:
        Created Terraform job
    """
    new_job = TerraformJob(
        customer_id=customer_id,
        job_name=job_data.job_name,
        terraform_config=job_data.terraform_config,
        command=job_data.command,
        status=JobStatus.PENDING
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    logger.info(f"Terraform job created: {new_job.job_name} (ID: {new_job.id})")
    return new_job


def get_terraform_job(db: Session, job_id: int, customer_id: Optional[int] = None) -> TerraformJob:
    """
    Get Terraform job by ID.
    
    Args:
        db: Database session
        job_id: Job ID
        customer_id: Optional customer ID to filter by ownership
        
    Returns:
        Terraform job
        
    Raises:
        HTTPException: If job not found
    """
    query = db.query(TerraformJob).filter(TerraformJob.id == job_id)
    
    if customer_id:
        query = query.filter(TerraformJob.customer_id == customer_id)
    
    job = query.first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terraform job not found"
        )
    return job


def get_user_terraform_jobs(
    db: Session,
    customer_id: int,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[JobStatus] = None
) -> List[TerraformJob]:
    """
    Get all Terraform jobs for a customer.
    
    Args:
        db: Database session
        customer_id: Customer ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        status_filter: Optional status filter
        
    Returns:
        List of Terraform jobs
    """
    query = db.query(TerraformJob).filter(TerraformJob.customer_id == customer_id)
    
    if status_filter:
        query = query.filter(TerraformJob.status == status_filter)
    
    return query.order_by(TerraformJob.created_at.desc()).offset(skip).limit(limit).all()


def get_all_terraform_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[TerraformJob]:
    """
    Get all Terraform jobs (admin only).
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of all Terraform jobs
    """
    return db.query(TerraformJob).order_by(TerraformJob.created_at.desc()).offset(skip).limit(limit).all()


def execute_terraform_job(db: Session, job_id: int) -> TerraformJob:
    """
    Execute a Terraform job.
    
    Args:
        db: Database session
        job_id: Job ID
        
    Returns:
        Updated Terraform job
    """
    from app.services.terraform_executor import execute_terraform_command
    
    job = get_terraform_job(db, job_id)
    
    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job cannot be executed. Current status: {job.status}"
        )
    
    # Execute terraform command
    # In production, this should be run in a background task/queue
    try:
        return execute_terraform_command(db, job)
    except Exception as e:
        logger.error(f"Terraform execution failed: {str(e)}")
        job.status = JobStatus.FAILED
        job.error_log = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
        return job


def update_terraform_job(db: Session, job_id: int, job_data: TerraformJobUpdate) -> TerraformJob:
    """
    Update Terraform job.
    
    Args:
        db: Database session
        job_id: Job ID
        job_data: Updated job data
        
    Returns:
        Updated Terraform job
    """
    job = get_terraform_job(db, job_id)
    
    update_data = job_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    db.commit()
    db.refresh(job)
    
    logger.info(f"Terraform job updated: {job.job_name} (ID: {job.id})")
    return job


def cancel_terraform_job(db: Session, job_id: int) -> TerraformJob:
    """
    Cancel a running Terraform job.
    
    Args:
        db: Database session
        job_id: Job ID
        
    Returns:
        Cancelled Terraform job
        
    Raises:
        HTTPException: If job cannot be cancelled
    """
    job = get_terraform_job(db, job_id)
    
    if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job cannot be cancelled. Current status: {job.status}"
        )
    
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)
    
    logger.info(f"Terraform job cancelled: {job.job_name} (ID: {job.id})")
    return job


def delete_terraform_job(db: Session, job_id: int) -> None:
    """
    Delete a Terraform job.
    
    Args:
        db: Database session
        job_id: Job ID
        
    Raises:
        HTTPException: If job not found
    """
    job = get_terraform_job(db, job_id)
    
    db.delete(job)
    db.commit()
    
    logger.info(f"Terraform job deleted: {job.job_name} (ID: {job.id})")
