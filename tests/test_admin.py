import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.services.ollama import OllamaService

client = TestClient(app)

@pytest.fixture
def mock_ollama_service():
    mock = AsyncMock()
    mock.list_models.return_value = [{"name": "test-model", "size": 1024}]
    mock.delete_model.return_value = True
    mock.unload_model.return_value = True
    
    # Mock pull_model as an async generator
    async def mock_pull(name):
        yield {"status": "downloading", "completed": 10, "total": 100}
        yield {"status": "done"}
    
    mock.pull_model.side_effect = mock_pull
    
    # Patch app.state.ollama_service
    app.state.ollama_service = mock
    yield mock
    # Cleanup
    if hasattr(app.state, "ollama_service"):
        del app.state.ollama_service

def test_get_config():
    response = client.get("/v1/admin/config")
    assert response.status_code == 200
    data = response.json()
    assert "server" in data
    assert "model" in data

def test_update_config():
    # Save original config first to restore later (or mock the file write)
    # For this test we'll just check if the endpoint accepts the data
    # In a real scenario we'd mock the file operations
    
    with patch("builtins.open", MagicMock()) as mock_open:
        with patch("yaml.dump") as mock_dump:
            payload = {
                "server": {"port": 9000},
                "model": {"model_name": "new-model"}
            }
            response = client.post("/v1/admin/config", json=payload)
            assert response.status_code == 200
            assert response.json()["status"] == "success"

def test_list_models(mock_ollama_service):
    response = client.get("/v1/admin/models")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "test-model"

def test_pull_model(mock_ollama_service):
    response = client.post("/v1/admin/models/pull", json={"name": "llama3"})
    assert response.status_code == 200
    # Streaming response check is tricky with TestClient, but we check status
    assert response.headers["content-type"] == "application/x-ndjson"

def test_delete_model(mock_ollama_service):
    response = client.delete("/v1/admin/models/test-model")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_stop_service(mock_ollama_service):
    response = client.post("/v1/admin/service/stop")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_dashboard_redirect():
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/dashboard.html"
