"""
Pydantic schemas for Terraform job operations.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ResourceConfig(BaseModel):
    """Schema for resource configuration."""
    id: str
    type: str
    label: str
    config: Dict[str, Any] = Field(default_factory=dict)


class TerraformGenerateRequest(BaseModel):
    """Schema for Terraform code generation request."""
    provider: str = Field(..., description="Cloud provider: aws, azure, gcp")
    project_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    resources: List[ResourceConfig] = Field(..., description="List of resources to generate")


class TerraformJobBase(BaseModel):
    """Base Terraform job schema."""
    job_name: str = Field(..., min_length=1, max_length=200)
    terraform_config: Dict[str, Any] = Field(..., description="Terraform configuration as JSON")
    command: str = Field(..., description="Terraform command: apply, plan, destroy")


class TerraformJobCreate(TerraformJobBase):
    """Schema for creating a new Terraform job."""
    pass


class TerraformJobUpdate(BaseModel):
    """Schema for updating Terraform job."""
    status: Optional[str] = None
    output_log: Optional[str] = None
    error_log: Optional[str] = None


class TerraformJobResponse(TerraformJobBase):
    """Schema for Terraform job response."""
    id: int
    customer_id: int
    status: str
    output_log: Optional[str] = None
    error_log: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TerraformJobList(BaseModel):
    """Schema for Terraform job list response."""
    jobs: list[TerraformJobResponse]
    total: int
    page: int
    page_size: int
