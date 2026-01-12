"""
Ollama Client Service
Handles communication with Ollama API for model inference
"""

import httpx
import json
import logging
from typing import Optional, Dict, Any, AsyncIterator

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama API"""
    
    def __init__(self):
        """Initialize Ollama service"""
        self.base_url = settings.model.ollama_base_url
        self.model_name = settings.model.model_name
        self.timeout = settings.model.timeout
        self.keep_alive = settings.model.keep_alive
        
        self.client = httpx.AsyncClient(timeout=self.timeout)
        
        logger.info(f"Ollama service initialized: {self.base_url}, model: {self.model_name}")
    
    async def health_check(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> list:
        """List available models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return data.get('models', [])
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def get_running_models(self) -> list:
        """Get currently running/loaded models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/ps")
            if response.status_code == 200:
                data = response.json()
                return data.get('models', [])
            return []
        except Exception as e:
            logger.error(f"Failed to get running models: {e}")
            return []
    
    async def chat(
        self,
        messages: list,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stream: bool = False
    ) -> Any:
        """
        Chat completion using Ollama
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stream: Whether to stream tokens
            
        Returns:
            Generated response or async iterator for streaming
        """
        
        # Use defaults from settings
        max_tokens = max_tokens or settings.inference.default_max_tokens
        temperature = temperature if temperature is not None else settings.inference.default_temperature
        top_p = top_p if top_p is not None else settings.inference.default_top_p
        top_k = top_k if top_k is not None else settings.inference.default_top_k
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
            },
            "keep_alive": self.keep_alive
        }
        
        if stream:
            return self._chat_stream(payload)
        else:
            return await self._chat_non_stream(payload)
    
    async def _chat_non_stream(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Non-streaming chat"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'content': data.get('message', {}).get('content', ''),
                    'total_duration': data.get('total_duration', 0),
                    'prompt_eval_count': data.get('prompt_eval_count', 0),
                    'eval_count': data.get('eval_count', 0)
                }
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
        except httpx.TimeoutException:
            logger.error("Chat request to Ollama timed out")
            raise RuntimeError("Chat timeout")
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise
    
    async def _chat_stream(self, payload: Dict[str, Any]) -> AsyncIterator[str]:
        """Streaming chat"""
        try:
            async with self.client.stream(
                'POST',
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_msg = f"Ollama API error: {response.status_code}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if 'message' in data and 'content' in data['message']:
                                yield data['message']['content']
                            
                            if data.get('done', False):
                                break
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON: {line}")
                            continue
                            
        except httpx.TimeoutException:
            logger.error("Streaming chat request to Ollama timed out")
            raise RuntimeError("Chat streaming timeout")
        except Exception as e:
            logger.error(f"Chat streaming error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count (approximate)"""
        return len(text) // 4
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        models = await self.list_models()
        running_models = await self.get_running_models()
        
        model_info = None
        for model in models:
            if model.get('name', '').startswith(self.model_name):
                model_info = model
                break
        
        # Check if model is actually running
        is_running = any(m.get('name', '').startswith(self.model_name) for m in running_models)
        
        return {
            "id": self.model_name,
            "type": "causal-lm",
            "base_model": "CodeLlama-7b-Instruct-hf",
            "adapter": "terraform-cloud-codellama-7b",
            "format": "GGUF",
            "backend": "ollama",
            "loaded": model_info is not None,
            "running": is_running,
            "size": model_info.get('size', 0) if model_info else 0,
            "modified_at": model_info.get('modified_at', '') if model_info else ''
        }
    
    async def pull_model(self, model_name: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Pull a model from Ollama library
        
        Args:
            model_name: Name of the model to pull
            
        Yields:
            Progress updates
        """
        try:
            payload = {"name": model_name, "stream": True}
            async with self.client.stream(
                'POST',
                f"{self.base_url}/api/pull",
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_msg = f"Failed to pull model: {response.status_code}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            yield data
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            raise

    async def create_model(self, model_name: str, modelfile_path: str = "Modelfile") -> AsyncIterator[Dict[str, Any]]:
        """
        Create a model from a Modelfile
        
        Args:
            model_name: Name of the model to create
            modelfile_path: Path to the Modelfile
            
        Yields:
            Progress updates
        """
        try:
            # Read Modelfile
            try:
                with open(modelfile_path, 'r') as f:
                    modelfile_content = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"Modelfile not found at {modelfile_path}")

            payload = {
                "name": model_name, 
                "modelfile": modelfile_content,
                "stream": True
            }
            
            async with self.client.stream(
                'POST',
                f"{self.base_url}/api/create",
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_msg = f"Failed to create model: {response.status_code}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            yield data
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Error creating model {model_name}: {e}")
            raise

    async def delete_model(self, model_name: str) -> bool:
        """
        Delete a model
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            True if successful
        """
        try:
            # First, try to unload the model if it's running
            running_models = await self.get_running_models()
            is_running = any(m.get('name', '').startswith(model_name) for m in running_models)
            
            if is_running:
                logger.info(f"Model {model_name} is running, unloading before deletion...")
                # Unload by sending empty chat with keep_alive=0
                try:
                    payload = {
                        "model": model_name,
                        "messages": [],
                        "keep_alive": 0
                    }
                    await self.client.post(f"{self.base_url}/api/chat", json=payload)
                except Exception as e:
                    logger.warning(f"Failed to unload model before deletion: {e}")
            
            # Now delete
            import json as json_lib
            response = await self.client.request(
                'DELETE',
                f"{self.base_url}/api/delete",
                content=json_lib.dumps({"name": model_name}),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully deleted model {model_name}")
                return True
            else:
                logger.error(f"Failed to delete model {model_name}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting model {model_name}: {e}")
            raise

    async def unload_model(self) -> bool:
        """
        Unload current model from memory by setting keep_alive to 0
        """
        try:
            # Send an empty chat request with keep_alive=0 to unload
            payload = {
                "model": self.model_name,
                "messages": [],
                "keep_alive": 0
            }
            await self.client.post(f"{self.base_url}/api/chat", json=payload)
            return True
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("Ollama service closed")
