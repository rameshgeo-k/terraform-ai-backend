"""
Chat Completion Endpoints
OpenAI-compatible chat API with file attachment support
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import json
import time
import logging
import base64
from typing import Optional, List

from app.schemas.requests import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelsResponse,
    Message
)
from app.services.ollama import OllamaService
from app.services.rag import RAGService
from app.utils.helpers import log_request
from app.utils.file_processor import FileProcessor

router = APIRouter()
logger = logging.getLogger(__name__)


def get_ollama_service() -> OllamaService:
    """Dependency injection for Ollama service"""
    from app.main import ollama_service
    return ollama_service


def get_rag_service() -> RAGService:
    """Dependency injection for RAG service"""
    from app.main import rag_service
    return rag_service


@router.get("/models", response_model=ModelsResponse)
async def get_models(ollama: OllamaService = Depends(get_ollama_service)):
    """Get available models"""
    if ollama is None:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    
    model_info = await ollama.get_model_info()
    
    return {
        "object": "list",
        "data": [model_info]
    }


@router.post("/chat/completions")
async def chat_completion(
    request: ChatCompletionRequest,
    ollama: OllamaService = Depends(get_ollama_service),
    rag: RAGService = Depends(get_rag_service)
):
    """
    OpenAI-compatible chat completion endpoint
    Supports both streaming and non-streaming responses
    Now supports file attachments in messages
    """
    start_time = time.time()
    
    if ollama is None:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    
    try:
        # Process messages and extract text from attachments
        processed_messages = []
        for msg in request.messages:
            content = msg.content
            
            # Process attachments if present
            if msg.attachments:
                attachment_texts = []
                for attachment in msg.attachments:
                    try:
                        # Decode base64 content if needed
                        if attachment.content.startswith('data:'):
                            # Format: data:mime/type;base64,content
                            base64_content = attachment.content.split(',')[1]
                            file_bytes = base64.b64decode(base64_content)
                        else:
                            # Assume it's already decoded text or base64
                            try:
                                file_bytes = base64.b64decode(attachment.content)
                            except:
                                # If decode fails, treat as plain text
                                attachment_texts.append(f"\n\n--- {attachment.filename} ---\n{attachment.content}")
                                continue
                        
                        # Extract text from file
                        extraction_result = await FileProcessor.extract_text(
                            file_content=file_bytes,
                            filename=attachment.filename,
                            mime_type=attachment.mime_type
                        )
                        
                        attachment_texts.append(
                            f"\n\n--- Content from {attachment.filename} ---\n{extraction_result['text']}"
                        )
                    
                    except Exception as e:
                        logger.error(f"Error processing attachment {attachment.filename}: {e}")
                        attachment_texts.append(
                            f"\n\n--- Error processing {attachment.filename}: {str(e)} ---"
                        )
                
                # Append attachment texts to message content
                if attachment_texts:
                    content = content + ''.join(attachment_texts)
            
            processed_messages.append({"role": msg.role, "content": content})
        
        # Estimate input tokens
        prompt_text = " ".join([msg["content"] for msg in processed_messages])
        input_tokens = ollama.count_tokens(prompt_text)
        
        if request.stream:
            # Streaming response
            async def generate():
                try:
                    streamer = await ollama.chat(
                        messages=processed_messages,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        top_k=request.top_k,
                        stream=True
                    )
                    
                    async for text in streamer:
                        chunk = {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": "terraform-codellama",
                            "choices": [{
                                "index": 0,
                                "delta": {"content": text},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # Send final chunk
                    final_chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "terraform-codellama",
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    error_chunk = {"error": str(e)}
                    yield f"data: {json.dumps(error_chunk)}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        else:
            # Non-streaming response
            result = await ollama.chat(
                messages=processed_messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                stream=False
            )
            
            generated_text = result['content']
            output_tokens = result.get('eval_count', ollama.count_tokens(generated_text))
            prompt_tokens = result.get('prompt_eval_count', input_tokens)
            inference_time = time.time() - start_time
            
            # Log request
            log_request(
                endpoint="/v1/chat/completions",
                input_tokens=prompt_tokens,
                output_tokens=output_tokens,
                inference_time=inference_time
            )
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "terraform-codellama",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": prompt_tokens + output_tokens
                }
            }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
