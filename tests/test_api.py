"""
API Tests
Test health and basic endpoints
"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ollama_connected" in data
    assert "rag_initialized" in data


def test_models_endpoint(client: TestClient):
    """Test models endpoint"""
    response = client.get("/v1/models")
    assert response.status_code in [200, 503]  # May fail if Ollama not running
