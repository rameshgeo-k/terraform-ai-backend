# Terraform AI Assistant API

Production-ready FastAPI application with CodeLlama-7b and RAG capabilities.

## 🏗️ Project Structure

```
server/
├── app/
│   ├── __init__.py           # Application package
│   ├── main.py               # FastAPI application entry point
│   ├── api/                  # API layer
│   │   └── v1/               # API version 1
│   │       ├── router.py     # Main API router
│   │       └── endpoints/    # Endpoint modules
│   │           ├── health.py # Health check
│   │           ├── chat.py   # Chat completion
│   │           └── rag.py    # RAG operations
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Configuration management
│   │   └── logging.py        # Logging setup
│   ├── schemas/              # Pydantic schemas
│   │   └── requests.py       # Request/Response models
│   ├── services/             # Business logic
│   │   ├── ollama.py         # Ollama service
│   │   └── rag.py            # RAG service
│   └── utils/                # Utility functions
│       └── helpers.py        # Helper functions
├── config/                   # Configuration files
│   └── server_config.yaml    # Server settings
├── tests/                    # Test suite
├── logs/                     # Application logs
├── chroma/                   # Vector database
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## ✨ Features

- **OpenAI-Compatible API**: Drop-in replacement for OpenAI's chat API
- **Streaming Support**: Real-time token streaming for chat responses
- **RAG Integration**: Semantic search with ChromaDB
- **Production-Ready**: Structured logging, error handling, validation
- **Type Safety**: Full Pydantic validation
- **API Versioning**: Clean v1 API structure
- **Dependency Injection**: FastAPI dependencies for services
- **Configuration Management**: YAML + environment variables

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Ollama (will be installed by setup script if needed)
- CodeLlama-7b-Terraform-Merged-f16.gguf model file

### Automated Setup (Recommended)

```bash
# 1. Ensure GGUF model is in parent directory
# /home/nova/AI/CodeLlama-7b-Terraform-Merged-f16.gguf

# 2. Run setup script
cd /home/nova/AI/server
./setup.sh
```

The setup script will:
- Install Ollama (if not already installed)
- Create Python virtual environment
- Install dependencies
- Import model to Ollama
- Verify everything is working

### Manual Installation

1. **Clone and navigate**:
   ```bash
   cd /home/nova/AI/server
   ```

2. **Download model** (see `MODEL_SETUP.md`):
   ```bash
   # Place GGUF file in parent directory
   # /home/nova/AI/CodeLlama-7b-Terraform-Merged-f16.gguf
   ```

3. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Import model to Ollama**:
   ```bash
   cd ..
   ollama create terraform-codellama -f server/Modelfile
   cd server
   ```

6. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

7. **Run the server**:
   ```bash
   python -m app.main
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## 📋 API Endpoints

### Health Check

```bash
GET /health
```

Returns service status:
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "rag_initialized": true
}
```

### Chat Completion

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

### RAG Operations

**Add Document**:
```bash
POST /v1/rag/documents
{
  "text": "Terraform best practices...",
  "metadata": {"category": "terraform"}
}
```

**Query Documents**:
```bash
POST /v1/rag/query
{
  "query": "VPC configuration",
  "top_k": 3
}
```

**RAG-Enhanced Chat**:
```bash
POST /v1/rag/chat
{
  "query": "How do I configure a VPC?",
  "top_k": 3,
  "temperature": 0.7
}
```

## ⚙️ Configuration

### YAML Configuration (`config/server_config.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  
model:
  ollama_base_url: "http://localhost:11434"
  model_name: "terraform-codellama"
  
inference:
  default_max_tokens: 512
  default_temperature: 0.7
  
rag:
  chroma_persist_directory: "./chroma"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```

### Environment Variables

All settings can be overridden with environment variables. See `.env.example`.

## 🧪 Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

## 📊 Logging

Logs are stored in `logs/`:
- `requests.log` - All API requests
- `errors.log` - Error-level logs

JSON structured logging enabled by default.

## 🔧 Development

### Install development dependencies:

```bash
pip install -r requirements.txt
```

### Run with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Organization Best Practices

- **Schemas** (`app/schemas/`): Pydantic models for validation
- **Services** (`app/services/`): Business logic (Ollama, RAG)
- **Endpoints** (`app/api/v1/endpoints/`): Route handlers
- **Core** (`app/core/`): Configuration, logging, utilities
- **Utils** (`app/utils/`): Helper functions

## 🐳 Docker (Coming Soon)

```bash
docker build -t terraform-ai-assistant .
docker run -p 8000:8000 terraform-ai-assistant
```

## 📝 License

MIT

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📚 Documentation

- FastAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
