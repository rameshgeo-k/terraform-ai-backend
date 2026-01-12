"""
Tests for Terraform endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_auth_token():
    """Helper function to get authentication token."""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "email": "terraformtest@example.com",
            "username": "terraformtest",
            "password": "password123"
        }
    )
    
    response = client.post(
        "/api/auth/login",
        json={
            "email": "terraformtest@example.com",
            "password": "password123"
        }
    )
    return response.json()["access_token"]


def test_create_terraform_job():
    """Test creating a Terraform job."""
    token = get_auth_token()
    
    response = client.post(
        "/api/terraform/apply",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "job_name": "Test Infrastructure",
            "terraform_config": {
                "provider": "aws",
                "region": "us-east-1",
                "resources": []
            },
            "command": "apply"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["job_name"] == "Test Infrastructure"
    assert data["status"] in ["pending", "running", "completed"]


def test_list_terraform_jobs():
    """Test listing Terraform jobs."""
    token = get_auth_token()
    
    # Create a job first
    client.post(
        "/api/terraform/apply",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "job_name": "Test Job",
            "terraform_config": {"test": "config"},
            "command": "plan"
        }
    )
    
    # List jobs
    response = client.get(
        "/api/terraform/jobs",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_terraform_job_logs():
    """Test getting Terraform job logs."""
    token = get_auth_token()
    
    # Create a job
    create_response = client.post(
        "/api/terraform/apply",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "job_name": "Log Test Job",
            "terraform_config": {"test": "config"},
            "command": "apply"
        }
    )
    job_id = create_response.json()["id"]
    
    # Get logs
    response = client.get(
        f"/api/terraform/logs/{job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "status" in data
    assert "output_log" in data
