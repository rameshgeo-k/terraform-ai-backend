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
        
        model_info = None
        for model in models:
            if model.get('name', '').startswith(self.model_name):
                model_info = model
                break
        
        return {
            "id": self.model_name,
            "type": "causal-lm",
            "base_model": "CodeLlama-7b-Instruct-hf",
            "adapter": "terraform-cloud-codellama-7b",
            "format": "GGUF",
            "backend": "ollama",
            "loaded": model_info is not None,
            "size": model_info.get('size', 0) if model_info else 0,
            "modified_at": model_info.get('modified_at', '') if model_info else ''
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("Ollama service closed")
