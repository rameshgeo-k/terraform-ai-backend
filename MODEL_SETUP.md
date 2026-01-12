# Model Setup Instructions

## Overview

This project uses a custom-trained Terraform CodeLlama model running via Ollama.

## Model Files

### ✅ Included in Git
- `Modelfile` - Ollama configuration for the model
- `MODEL_SETUP.md` - This file

### ❌ NOT Included in Git (too large)
- `CodeLlama-7b-Terraform-Merged-f16.gguf` (12.5 GB)

## Obtaining the Model

### Option 1: Download Pre-trained Model (Recommended)
If you have access to the model file, place it in `/home/nova/AI/`:

```bash
# Download from your storage location
wget https://your-storage-url/CodeLlama-7b-Terraform-Merged-f16.gguf

# Or use cloud storage
# aws s3 cp s3://your-bucket/CodeLlama-7b-Terraform-Merged-f16.gguf .
# gcloud storage cp gs://your-bucket/CodeLlama-7b-Terraform-Merged-f16.gguf .
```

### Option 2: Build from Source
If you need to recreate the model:

1. **Download Base Model**
   ```bash
   # CodeLlama-7b-Instruct-hf from HuggingFace
   git clone https://huggingface.co/codellama/CodeLlama-7b-Instruct-hf
   ```

2. **Download LoRA Adapter**
   ```bash
   # Terraform-trained LoRA adapter
   git clone https://huggingface.co/your-username/terraform-cloud-codellama-7b
   ```

3. **Merge Model + LoRA**
   ```bash
   python merge_lora.py
   ```

4. **Convert to GGUF**
   ```bash
   python convert_to_gguf.py
   ```

## Setting Up Ollama

### 1. Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Import the Model
```bash
cd /home/nova/AI
ollama create terraform-codellama -f Modelfile
```

### 3. Verify Installation
```bash
ollama list | grep terraform-codellama
```

### 4. Test the Model
```bash
ollama run terraform-codellama "What is Terraform?"
```

## Model Details

- **Base Model**: CodeLlama-7b-Instruct-hf (Meta)
- **Fine-tuning**: Terraform Cloud LoRA adapter
- **Format**: GGUF (f16 precision)
- **Size**: 12.5 GB
- **Context Window**: 4096 tokens
- **Backend**: Ollama

## Storage Recommendations

### For Git LFS (if needed)
```bash
# Install git-lfs
git lfs install

# Track large files
git lfs track "*.gguf"

# Add and commit
git add .gitattributes
git commit -m "Track GGUF files with Git LFS"
```

### For Cloud Storage
Store the GGUF file in:
- **AWS S3**: `s3://your-bucket/models/`
- **Google Cloud Storage**: `gs://your-bucket/models/`
- **Azure Blob**: `https://account.blob.core.windows.net/models/`
- **Hugging Face Hub**: Upload as a model repository

### For Team Sharing
Create a download script:

```bash
#!/bin/bash
# download_model.sh

MODEL_URL="https://your-storage/CodeLlama-7b-Terraform-Merged-f16.gguf"
MODEL_PATH="/home/nova/AI/CodeLlama-7b-Terraform-Merged-f16.gguf"

if [ ! -f "$MODEL_PATH" ]; then
    echo "Downloading model..."
    wget -O "$MODEL_PATH" "$MODEL_URL"
    echo "Model downloaded successfully"
else
    echo "Model already exists"
fi

# Import to Ollama
cd /home/nova/AI
ollama create terraform-codellama -f Modelfile
```

## Verification

After setup, verify the server can access the model:

```bash
cd /home/nova/AI/server
source .venv/bin/activate
python -m app.main

# In another terminal:
curl http://localhost:8000/health
# Should show: {"status":"healthy","ollama_connected":true,...}
```

## Troubleshooting

### Model Not Found
```bash
# Check Ollama models
ollama list

# Re-import if needed
ollama create terraform-codellama -f Modelfile
```

### Path Issues
Make sure the GGUF file is in `/home/nova/AI/` and the `Modelfile` has the correct relative path:
```
FROM ./CodeLlama-7b-Terraform-Merged-f16.gguf
```

### Ollama Not Running
```bash
# Start Ollama service
ollama serve

# Or check status
systemctl status ollama
```
