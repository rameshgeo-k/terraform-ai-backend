"""
Terraform job tracking model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class JobStatus(str, enum.Enum):
    """Terraform job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TerraformJob(Base):
    """Terraform job database model."""
    __tablename__ = "terraform_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    job_name = Column(String, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    terraform_config = Column(JSON, nullable=False)  # Terraform configuration JSON
    command = Column(String, nullable=False)  # e.g., "apply", "plan", "destroy"
    output_log = Column(Text)  # Terraform command output
    error_log = Column(Text)  # Error messages if any
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="terraform_jobs")
    
    def __repr__(self):
        return f"<TerraformJob(id={self.id}, name='{self.job_name}', status='{self.status}')>"
