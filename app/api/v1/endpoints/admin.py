"""
Admin Endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import yaml
import json
from typing import Dict, Any, List

from app.core.config import settings

router = APIRouter()

class ConfigUpdate(BaseModel):
    server: Dict[str, Any] = {}
    model: Dict[str, Any] = {}
    inference: Dict[str, Any] = {}
    rag: Dict[str, Any] = {}
    security: Dict[str, Any] = {}
    logging: Dict[str, Any] = {}

class ModelPullRequest(BaseModel):
    name: str

@router.get("/config")
async def get_config():
    """Get current server configuration"""
    try:
        with open("config/server_config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read config: {str(e)}")

@router.post("/config")
async def update_config(config: ConfigUpdate):
    """Update server configuration"""
    try:
        # Read existing config to preserve comments/structure if possible, 
        # but for now we'll just load, update, and dump.
        # To preserve comments we'd need a more advanced yaml parser like ruamel.yaml,
        # but standard pyyaml is what we have.
        
        current_config = {}
        try:
            with open("config/server_config.yaml", "r") as f:
                current_config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            pass

        # Deep update helper
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d

        # Update sections
        if config.server: deep_update(current_config.setdefault('server', {}), config.server)
        if config.model: deep_update(current_config.setdefault('model', {}), config.model)
        if config.inference: deep_update(current_config.setdefault('inference', {}), config.inference)
        if config.rag: deep_update(current_config.setdefault('rag', {}), config.rag)
        if config.security: deep_update(current_config.setdefault('security', {}), config.security)
        if config.logging: deep_update(current_config.setdefault('logging', {}), config.logging)

        # Write back
        with open("config/server_config.yaml", "w") as f:
            yaml.dump(current_config, f, default_flow_style=False)
            
        return {"status": "success", "message": "Configuration updated. Please restart the server for changes to take effect."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")

@router.get("/models")
async def list_models(request: Request):
    """List available models"""
    if not hasattr(request.app.state, "ollama_service") or not request.app.state.ollama_service:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    return await request.app.state.ollama_service.list_models()

@router.get("/status")
async def get_status(request: Request):
    """Get current service status including running model"""
    if not hasattr(request.app.state, "ollama_service") or not request.app.state.ollama_service:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    
    ollama_service = request.app.state.ollama_service
    model_info = await ollama_service.get_model_info()
    
    return {
        "model_name": settings.model.model_name,
        "running": model_info.get("running", False),
        "loaded": model_info.get("loaded", False)
    }

@router.post("/models/pull")
async def pull_model(request: Request, request_body: ModelPullRequest):
    """Pull a new model"""
    if not hasattr(request.app.state, "ollama_service") or not request.app.state.ollama_service:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    
    ollama_service = request.app.state.ollama_service
    
    async def generate():
        try:
            async for progress in ollama_service.pull_model(request_body.name):
                yield json.dumps(progress) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@router.post("/models/create")
async def create_model(request: Request):
    """Create the default model from Modelfile"""
    if not hasattr(request.app.state, "ollama_service") or not request.app.state.ollama_service:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    
    ollama_service = request.app.state.ollama_service
    model_name = settings.model.model_name
    
    async def generate():
        try:
            async for progress in ollama_service.create_model(model_name):
                yield json.dumps(progress) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@router.delete("/models/{name:path}")
async def delete_model(name: str, request: Request):
    """Delete a model"""
    if not hasattr(request.app.state, "ollama_service") or not request.app.state.ollama_service:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    
    try:
        success = await request.app.state.ollama_service.delete_model(name)
        if success:
            return {"status": "success", "message": f"Model {name} deleted"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete model {name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting model: {str(e)}")

@router.post("/models/activate")
async def activate_model(request: Request, request_body: ModelPullRequest):
    """Set a model as the active model"""
    try:
        # Read current config
        with open("config/server_config.yaml", "r") as f:
            config = yaml.safe_load(f) or {}
        
        # Update model name
        if 'model' not in config:
            config['model'] = {}
        config['model']['model_name'] = request_body.name
        
        # Write back
        with open("config/server_config.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Update settings in memory
        settings.model.model_name = request_body.name
        
        # Update ollama service
        if hasattr(request.app.state, "ollama_service") and request.app.state.ollama_service:
            request.app.state.ollama_service.model_name = request_body.name
        
        return {"status": "success", "message": f"Active model set to {request_body.name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate model: {str(e)}")


@router.post("/service/stop")
async def stop_service(request: Request):
    """Unload current model"""
    if not hasattr(request.app.state, "ollama_service") or not request.app.state.ollama_service:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    
    success = await request.app.state.ollama_service.unload_model()
    if success:
        return {"status": "success", "message": "Model unloaded"}
    else:
        raise HTTPException(status_code=500, detail="Failed to unload model")

@router.post("/service/load")
async def load_service(request: Request):
    """Load/preload the active model into memory"""
    if not hasattr(request.app.state, "ollama_service") or not request.app.state.ollama_service:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    
    ollama_service = request.app.state.ollama_service
    
    try:
        # Send a simple chat request to load the model
        # This will trigger Ollama to load the model into memory
        await ollama_service.chat(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
            stream=False
        )
        return {"status": "success", "message": f"Model {ollama_service.model_name} loaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

