# Ollama Integration Guide

This guide explains how to integrate and use Ollama (local LLM) with InfraPilot.

## Overview

Ollama support has been added to InfraPilot, allowing you to run local AI models instead of (or alongside) cloud-based models like OpenAI, Anthropic, or AWS Bedrock.

## Prerequisites

1. **Install Ollama**: Visit [ollama.ai](https://ollama.ai) and install Ollama for your OS
2. **Start Ollama service**: Run `ollama serve` (or it may start automatically)
3. **Pull a model**: Download a model, e.g., `ollama pull llama3.2`

## Configuration

### 1. Environment Variables

Add these to your `.env` file:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 2. Port Configuration

To avoid port conflicts with your existing Ollama chat on port 8000:

```env
# Server Configuration
API_PORT=8000  # Change this if needed (e.g., 8001)
```

Then run your backend with:
```bash
uvicorn app.main:app --port 8001  # Use the configured port
```

## Adding Ollama Models to Database

### Option 1: Using the Helper Script

```bash
# Navigate to backend directory
cd /var/www/projects/infrapilot/backend

# Activate virtual environment
source .venv/bin/activate

# List available Ollama models
python scripts/add_ollama_model.py --list

# Add a model (not active by default)
python scripts/add_ollama_model.py --model llama3.2 --name "Llama 3.2"

# Add and set as active model
python scripts/add_ollama_model.py \
  --model llama3.2 \
  --name "Llama 3.2 Chat" \
  --type chat \
  --active

# Add with custom parameters
python scripts/add_ollama_model.py \
  --model codellama \
  --name "CodeLlama Terraform" \
  --type terraform \
  --temperature 0.3 \
  --max-tokens 8192 \
  --active
```

### Option 2: Via Admin Panel

1. Log in to the admin panel at `http://localhost:3000/admin`
2. Go to "AI Models" section
3. Click "Add Model"
4. Fill in the form:
   - **Name**: `Ollama Chat`
   - **Provider**: `ollama`
   - **Model Identifier**: `llama3.2` (or any installed Ollama model)
   - **Model Type**: `chat` or `terraform` or `both`
   - **API Endpoint**: `http://localhost:11434`
   - **Parameters**:
     ```json
     {
       "base_url": "http://localhost:11434",
       "temperature": 0.7,
       "max_tokens": 4096
     }
     ```
   - **Is Active**: Check to make it the active model

## Supported Ollama Models

Popular models you can use:

- **llama3.2** - Latest Llama model (recommended)
- **llama3.1** - Previous Llama version
- **mistral** - Mistral AI model
- **codellama** - Code-optimized model
- **phi3** - Microsoft's small model
- **gemma** - Google's Gemma model

Pull any model with: `ollama pull <model-name>`

## Architecture

### Model Factory Support

The `ModelFactory` now supports 4 providers:
1. **OpenAI** - Cloud GPT models
2. **Anthropic** - Cloud Claude models
3. **Bedrock** - AWS Bedrock models
4. **Ollama** - Local models ✨ NEW

### How It Works

1. Model configuration stored in `model_configs` database table
2. `ModelFactory.create_from_config()` detects provider and creates appropriate LangChain chat model
3. Chat service uses the active model for streaming responses
4. All models use the same LangChain interface - switching is seamless!

## Troubleshooting

### Port Conflicts

If you get "Address already in use" error:

```bash
# Check what's using port 8000
lsof -i :8000

# Option 1: Change InfraPilot port
# Edit .env: API_PORT=8001

# Option 2: Stop your Ollama chat and use InfraPilot's integrated version
```

### Ollama Not Responding

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Or restart the service (macOS/Linux)
brew services restart ollama  # macOS
systemctl restart ollama      # Linux
```

### Model Not Found

```bash
# List installed models
ollama list

# Pull the model you need
ollama pull llama3.2
```

### Connection Refused

If you get connection errors:

1. Verify Ollama is running: `ollama list`
2. Check the base URL in your config matches Ollama's address
3. Default is `http://localhost:11434` (Ollama default)
4. If Ollama is on a different host/port, update `OLLAMA_BASE_URL` in `.env`

## Performance Tips

1. **GPU**: Ollama automatically uses GPU if available (much faster)
2. **Model Size**: Smaller models (7B) are faster but less capable than larger ones (70B)
3. **Context Length**: Adjust `max_tokens` based on your needs (higher = more memory)
4. **Temperature**: Lower (0.1-0.3) for deterministic, higher (0.7-1.0) for creative responses

## Switching Between Providers

You can have multiple models configured and switch between them:

```bash
# Add Ollama model (inactive)
python scripts/add_ollama_model.py --model llama3.2 --name "Llama Local"

# When you want to use it, set it as active via admin panel or script
# You can keep Bedrock/OpenAI models configured but inactive
```

## Benefits of Ollama

✅ **Privacy**: All data stays local  
✅ **Cost**: No API fees  
✅ **Speed**: Low latency (if you have good hardware)  
✅ **Offline**: Works without internet  
✅ **Customization**: Use fine-tuned models  

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Configure your `.env` file
3. Add Ollama model to database
4. Restart your backend server
5. Test the chat interface!
