# Terraform AI Assistant

Production-ready FastAPI application powered by **CodeLlama-7b** with Terraform-specific fine-tuning and advanced **RAG (Retrieval-Augmented Generation)** capabilities.

## 🎯 Overview

An intelligent assistant specialized in Terraform and Infrastructure as Code (IaC) that provides expert guidance, code generation, and document analysis. Built with a fine-tuned CodeLlama-7b model merged with a Terraform LoRA adapter, this system offers OpenAI-compatible APIs with powerful file processing and semantic search capabilities.

## 🏗️ Project Structure

```
/var/www/projects/AI Assistant/
├── app/
│   ├── __init__.py           # Application package
│   ├── main.py               # FastAPI entry point & lifespan management
│   ├── api/                  # API layer
│   │   └── v1/               # API version 1
│   │       ├── router.py     # Main API router
│   │       └── endpoints/    # Endpoint modules
│   │           ├── health.py # Health check endpoints
│   │           ├── chat.py   # Chat completion with attachments
│   │           ├── rag.py    # RAG document management
│   │           └── files.py  # File upload & processing
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Pydantic settings management
│   │   └── logging.py        # Structured logging setup
│   ├── schemas/              # Pydantic models
│   │   └── requests.py       # Request/Response schemas
│   ├── services/             # Business logic
│   │   ├── ollama.py         # Ollama API client
│   │   └── rag.py            # ChromaDB RAG service
│   └── utils/                # Utilities
│       ├── helpers.py        # Helper functions
│       └── file_processor.py # Multi-format file text extraction
├── config/                   # Configuration
│   └── server_config.yaml    # YAML-based settings
├── models/                   # Model files
│   └── CodeLlama-7b-Terraform-Merged-f16.gguf
├── tests/                    # Test suite
│   ├── conftest.py           # pytest fixtures
│   └── test_api.py           # API tests
├── chroma/                   # ChromaDB vector database
├── logs/                     # Application logs
├── scripts/                  # Setup & utility scripts
│   └── setup.sh              # Automated installation
├── docs/                     # Documentation
│   ├── FEATURE_ATTACHMENTS.md
│   └── MODEL_SETUP.md
├── Modelfile                 # Ollama model configuration
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── RESTRUCTURE_SUMMARY.md    # Architecture documentation
```

## ✨ Features

### 🤖 AI Capabilities
- **Terraform-Specialized Model**: CodeLlama-7b with merged Terraform LoRA adapter
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI chat completions
- **Streaming Support**: Real-time token streaming for responsive UX
- **Context-Aware Responses**: Up to 4096 token context window

### 📄 File Processing
- **Multi-Format Support**: PDF, DOCX, DOC, TXT, MD, code files (py, js, ts, tf, etc.)
- **Inline Attachments**: Attach files directly to chat messages
- **Automatic Text Extraction**: Smart extraction from documents and code
- **File Upload API**: Store files in RAG for later retrieval

### 🔍 RAG (Retrieval-Augmented Generation)
- **Semantic Search**: ChromaDB vector database with sentence-transformers
- **Document Management**: Full CRUD operations on stored documents
- **Context Building**: Automatic context injection from relevant documents
- **Hybrid Queries**: Combine semantic search with LLM generation

### 🏭 Production-Ready
- **Type Safety**: Full Pydantic validation throughout
- **Structured Logging**: JSON logging with request tracking
- **Health Monitoring**: Service health checks and statistics
- **Error Handling**: Comprehensive exception handling
- **CORS Support**: Configurable cross-origin policies
- **Configuration Management**: YAML + environment variables
- **API Versioning**: Clean versioned API structure

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Ollama** (will be installed by setup script if needed)
- **CodeLlama-7b-Terraform-Merged-f16.gguf** model file

### Automated Setup (Recommended)

```bash
# 1. Ensure GGUF model is in the models directory
# models/CodeLlama-7b-Terraform-Merged-f16.gguf

# 2. Run setup script
cd scripts
./setup.sh
```

The setup script will:
- Install Ollama (if not already installed)
- Create Python virtual environment
- Install all dependencies
- Import model to Ollama
- Verify installation

### Manual Installation

1. **Clone and navigate**:
   ```bash
   cd "/var/www/projects/AI Assistant"
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Import model to Ollama**:
   ```bash
   ollama create terraform-codellama -f Modelfile
   ```

5. **Run the server**:
   ```bash
   python -m app.main
   ```

   Or with uvicorn:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## 📋 API Endpoints

### Health & Info

#### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "rag_initialized": true
}
```

#### Model Information
```bash
GET /v1/models
```

### Chat Completion

#### Standard Chat
```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "How do I create a VPC in Terraform?"}
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": false
}
```

#### Chat with File Attachments
```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "Review this Terraform code",
      "attachments": [
        {
          "filename": "main.tf",
          "content": "base64_encoded_content",
          "mime_type": "text/x-terraform"
        }
      ]
    }
  ]
}
```

#### Streaming Chat
```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "Explain Terraform modules"}],
  "stream": true
}
```

### File Upload & Management

#### Upload File
```bash
POST /v1/files/upload
Content-Type: multipart/form-data

file=@document.pdf
store_in_rag=true
metadata={"category": "documentation"}
```

**Supported formats:**
- **Documents**: PDF, DOCX, DOC, TXT, MD
- **Code**: PY, JS, TS, JAVA, CPP, C, GO, RS, TF
- **Data**: JSON, XML, YAML, CSV, HTML
- **Scripts**: SH

#### List Files
```bash
GET /v1/files?limit=10&offset=0
```

#### Get File
```bash
GET /v1/files/{file_id}
```

#### Delete File
```bash
DELETE /v1/files/{file_id}
```

### RAG Operations

#### Add Document
```bash
POST /v1/rag/documents
Content-Type: application/json

{
  "text": "Terraform best practices for AWS...",
  "metadata": {"category": "terraform", "source": "docs"}
}
```

#### Query Documents (Semantic Search)
```bash
POST /v1/rag/query
Content-Type: application/json

{
  "query": "VPC configuration best practices",
  "top_k": 3
}
```

#### RAG-Enhanced Chat
```bash
POST /v1/rag/chat
Content-Type: application/json

{
  "query": "How do I configure a VPC with private subnets?",
  "top_k": 3,
  "temperature": 0.7,
  "stream": false
}
```

#### Get/Update/Delete Documents
```bash
GET    /v1/rag/documents/{doc_id}
PUT    /v1/rag/documents/{doc_id}
DELETE /v1/rag/documents/{doc_id}
```

#### List Documents
```bash
GET /v1/rag/documents?limit=10&offset=0
```

#### RAG Statistics
```bash
GET /v1/rag/stats
```

## ⚙️ Configuration

### YAML Configuration (`config/server_config.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1
  reload: false
  log_level: "info"
  
model:
  ollama_base_url: "http://localhost:11434"
  model_name: "terraform-codellama"
  timeout: 300
  keep_alive: "5m"
  
inference:
  default_max_tokens: 512
  default_temperature: 0.7
  default_top_p: 0.9
  default_top_k: 50
  max_prompt_length: 4096
  
rag:
  chroma_persist_directory: "./chroma"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  default_top_k: 3
  collection_name: "documents"

security:
  cors_origins: ["*"]
  max_request_size: 10485760  # 10MB
  request_timeout: 300

logging:
  directory: "./logs"
  level: "info"
  format: "json"
```

### Environment Variables

All settings can be overridden with environment variables:

```bash
# .env file
APP_NAME="Terraform AI Assistant"
SERVER_HOST="0.0.0.0"
SERVER_PORT=8000
MODEL_OLLAMA_BASE_URL="http://localhost:11434"
MODEL_MODEL_NAME="terraform-codellama"
RAG_CHROMA_PERSIST_DIRECTORY="./chroma"
```

## 🧪 Testing

Run the test suite:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_api.py::test_health_check -v
```

## 📊 Logging

Logs are stored in the `logs/` directory:
- `requests.log` - All API requests with performance metrics
- `errors.log` - Error-level logs

JSON structured logging format:
```json
{
  "timestamp": "2025-11-20T10:30:45.123Z",
  "level": "INFO",
  "endpoint": "/v1/chat/completions",
  "input_tokens": 150,
  "output_tokens": 200,
  "inference_time": 2.34
}
```

## 🔧 Development

### Run with Auto-Reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Organization

- **Schemas** (`app/schemas/`): Pydantic models for validation
- **Services** (`app/services/`): Business logic (Ollama, RAG)
- **Endpoints** (`app/api/v1/endpoints/`): Route handlers
- **Core** (`app/core/`): Configuration, logging
- **Utils** (`app/utils/`): Helper functions, file processing

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📦 Dependencies

### Core
- `fastapi>=0.109.0` - Web framework
- `uvicorn[standard]>=0.27.0` - ASGI server
- `pydantic>=2.5.0` - Data validation
- `pydantic-settings>=2.1.0` - Settings management
- `httpx>=0.26.0` - Async HTTP client
- `python-multipart>=0.0.6` - File upload support

### RAG & ML
- `chromadb>=0.4.22` - Vector database
- `sentence-transformers>=2.3.0` - Embedding models

### File Processing
- `PyPDF2>=3.0.0` - PDF text extraction
- `python-docx>=1.0.0` - DOCX text extraction

### Utilities
- `pyyaml>=6.0.1` - YAML configuration
- `python-json-logger>=2.0.7` - Structured logging

### Development
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.23.0` - Async test support

## 🎯 Use Cases

### 1. Terraform Code Generation
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Generate a Terraform module for an AWS VPC with 3 public and 3 private subnets"
      }
    ]
  }'
```

### 2. Code Review with Attachments
Upload a Terraform file for review:
```bash
curl -X POST http://localhost:8000/v1/files/upload \
  -F "file=@main.tf" \
  -F "store_in_rag=true"
```

### 3. Documentation Search
Store documentation and query semantically:
```bash
# Add documentation
curl -X POST http://localhost:8000/v1/rag/documents \
  -H "Content-Type: application/json" \
  -d '{"text": "AWS VPC best practices..."}'

# Query
curl -X POST http://localhost:8000/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "VPC security", "top_k": 5}'
```

### 4. RAG-Enhanced Assistance
Combine documentation retrieval with LLM generation:
```bash
curl -X POST http://localhost:8000/v1/rag/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I set up a highly available VPC?",
    "top_k": 3
  }'
```

## 🐳 Docker Support (Future)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🛠️ Troubleshooting

### Ollama Not Running
```bash
# Start Ollama service
ollama serve

# Verify model is loaded
ollama list
```

### Model Not Found
```bash
# Re-import model
ollama create terraform-codellama -f Modelfile

# Verify
ollama list | grep terraform-codellama
```

### ChromaDB Issues
```bash
# Clear ChromaDB data (WARNING: deletes all documents)
rm -rf chroma/

# Restart server to reinitialize
python -m app.main
```

### File Upload Errors
- Check file size (max 10MB)
- Verify file format is supported
- Ensure PyPDF2 and python-docx are installed

## 📈 Performance Optimization

### Model Performance
- Adjust `num_ctx` in Modelfile for context size
- Tune `temperature` for consistency vs creativity
- Use `keep_alive` to keep model in memory

### RAG Performance
- Adjust `chunk_size` and `chunk_overlap` for better retrieval
- Increase `top_k` for more context (but slower)
- Use smaller embedding models for faster queries

## 🔒 Security Considerations

- Configure `cors_origins` in production
- Implement authentication middleware
- Set appropriate `max_request_size` limits
- Use HTTPS in production
- Sanitize user inputs (already implemented)
- Monitor logs for suspicious activity

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📚 Additional Documentation

- **Feature Documentation**: See `docs/FEATURE_ATTACHMENTS.md`
- **Model Setup Guide**: See `docs/MODEL_SETUP.md`
- **Architecture Details**: See `docs/RESTRUCTURE_SUMMARY.md`

## 🆘 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `docs/`
- Review API documentation at `/docs` endpoint

## 🎉 Acknowledgments

- **Meta AI** - CodeLlama base model
- **Ollama** - Model serving infrastructure
- **FastAPI** - Modern Python web framework
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embedding models

---

**Server Status**: http://localhost:8000  
**API Documentation**: http://localhost:8000/docs  
**Repository**: terraform-ai-assistant (ramesh-geo)  
**Branch**: feature/add-attachment
