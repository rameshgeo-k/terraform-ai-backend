"""
Background task service for executing terraform commands.
"""
import subprocess
import os
import tempfile
import shutil
from typing import Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.terraform_job import TerraformJob, JobStatus
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

# Directory for terraform working directories
TERRAFORM_WORK_DIR = os.getenv("TERRAFORM_WORK_DIR", "/tmp/terraform_jobs")


def execute_terraform_command(db: Session, job: TerraformJob) -> TerraformJob:
    """
    Execute actual terraform command for a job.
    
    Args:
        db: Database session
        job: Terraform job to execute
        
    Returns:
        Updated job with execution results
    """
    job_dir = None
    
    try:
        # Create working directory for this job
        job_dir = Path(TERRAFORM_WORK_DIR) / f"job_{job.id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Write terraform configuration to file
        tf_file = job_dir / "main.tf"
        terraform_code = job.terraform_config.get("code", "")
        
        if not terraform_code:
            raise ValueError("No Terraform code found in job configuration")
        
        tf_file.write_text(terraform_code)
        
        # Update job status to running
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Starting terraform {job.command} for job {job.id}")
        
        # Initialize terraform
        init_result = _run_terraform_command("init", job_dir)
        if init_result["returncode"] != 0:
            raise Exception(f"Terraform init failed: {init_result['stderr']}")
        
        output_log = f"=== Terraform Init ===\n{init_result['stdout']}\n\n"
        
        # Run the actual command
        if job.command == "plan":
            result = _run_terraform_command("plan", job_dir)
        elif job.command == "apply":
            result = _run_terraform_command("apply", job_dir, auto_approve=True)
        elif job.command == "destroy":
            result = _run_terraform_command("destroy", job_dir, auto_approve=True)
        else:
            raise ValueError(f"Unknown command: {job.command}")
        
        output_log += f"=== Terraform {job.command.capitalize()} ===\n{result['stdout']}\n"
        
        # Update job with results
        if result["returncode"] == 0:
            job.status = JobStatus.COMPLETED
            job.output_log = output_log
            logger.info(f"Terraform job {job.id} completed successfully")
        else:
            job.status = JobStatus.FAILED
            job.output_log = output_log
            job.error_log = result["stderr"]
            logger.error(f"Terraform job {job.id} failed: {result['stderr']}")
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_log = str(e)
        logger.error(f"Error executing terraform job {job.id}: {str(e)}")
    
    finally:
        job.completed_at = datetime.utcnow()
        db.commit()
        
        # Clean up working directory
        if job_dir and job_dir.exists():
            try:
                shutil.rmtree(job_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up job directory {job_dir}: {str(e)}")
    
    return job


def _run_terraform_command(
    command: str,
    working_dir: Path,
    auto_approve: bool = False
) -> dict:
    """
    Run a terraform command in the specified directory.
    
    Args:
        command: Terraform command (init, plan, apply, destroy)
        working_dir: Directory containing terraform files
        auto_approve: Whether to add -auto-approve flag
        
    Returns:
        Dict with returncode, stdout, stderr
    """
    cmd = ["terraform", command]
    
    if auto_approve and command in ["apply", "destroy"]:
        cmd.append("-auto-approve")
    
    # Add no-color flag for cleaner logs
    cmd.append("-no-color")
    
    logger.info(f"Running command: {' '.join(cmd)} in {working_dir}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    except subprocess.TimeoutExpired:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": "Command timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(e)
        }


async def execute_terraform_job_async(db: Session, job_id: int):
    """
    Execute terraform job asynchronously (for background tasks).
    
    Args:
        db: Database session
        job_id: Job ID to execute
    """
    from app.services.terraform_service import get_terraform_job
    
    try:
        job = get_terraform_job(db, job_id)
        execute_terraform_command(db, job)
    except Exception as e:
        logger.error(f"Async execution failed for job {job_id}: {str(e)}")
