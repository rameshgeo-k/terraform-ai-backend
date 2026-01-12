#!/bin/bash
# Automated setup script for Terraform AI Assistant
# Run from the server/ directory

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================================================"
echo "  🚀 Terraform AI Assistant - Setup Script"
echo "======================================================================"
echo ""

# Check if running from server directory
if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
    echo -e "${RED}❌ Error: Please run this script from the server/ directory${NC}"
    exit 1
fi

# Check if Modelfile exists
if [ ! -f "Modelfile" ]; then
    echo -e "${RED}❌ Error: Modelfile not found in server/ directory${NC}"
    exit 1
fi

# Check if GGUF model exists in parent directory
if [ ! -f "../CodeLlama-7b-Terraform-Merged-f16.gguf" ]; then
    echo -e "${RED}❌ Error: GGUF model file not found${NC}"
    echo "Expected location: /home/nova/AI/CodeLlama-7b-Terraform-Merged-f16.gguf"
    echo ""
    echo "Please download the model file first:"
    echo "  See MODEL_SETUP.md for instructions"
    exit 1
fi

echo -e "${GREEN}✓ Project files verified${NC}"
echo ""

# Check Ollama installation
echo "📦 Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠  Ollama not found. Installing...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Ollama installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install Ollama${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Ollama is already installed${NC}"
fi

echo ""

# Start Ollama service if not running
echo "🔄 Checking Ollama service..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama service is running${NC}"
else
    echo -e "${RED}❌ Failed to start Ollama service${NC}"
    echo "Please start it manually: ollama serve"
    exit 1
fi

echo ""

# Check Python
echo "🐍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

echo ""

# Create virtual environment
echo "📦 Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠  Virtual environment already exists${NC}"
fi

# Activate virtual environment
source .venv/bin/activate

echo ""

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

echo ""

# Import model to Ollama
echo "🤖 Importing model to Ollama..."
echo "   This may take a few minutes..."

cd ..
ollama create terraform-codellama -f server/Modelfile
cd server

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Model imported successfully${NC}"
else
    echo -e "${RED}❌ Failed to import model${NC}"
    exit 1
fi

echo ""

# Verify model
echo "🔍 Verifying model..."
if ollama list | grep -q "terraform-codellama"; then
    MODEL_SIZE=$(ollama list | grep "terraform-codellama" | awk '{print $2}')
    echo -e "${GREEN}✓ Model verified: terraform-codellama (${MODEL_SIZE})${NC}"
else
    echo -e "${RED}❌ Model not found in Ollama${NC}"
    exit 1
fi

echo ""

# Create logs directory
mkdir -p logs

# Copy environment example if .env doesn't exist
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from template${NC}"
fi

echo ""
echo "======================================================================"
echo -e "  ${GREEN}✅ Setup Complete!${NC}"
echo "======================================================================"
echo ""
echo "📋 Next steps:"
echo ""
echo "  1. Start the server:"
echo "     source .venv/bin/activate"
echo "     python -m app.main"
echo ""
echo "  2. Test the API:"
echo "     curl http://localhost:8000/health"
echo ""
echo "  3. View API documentation:"
echo "     http://localhost:8000/docs"
echo ""
echo "  4. Try a chat completion:"
echo "     curl -X POST http://localhost:8000/v1/chat/completions \\"
echo "       -H \"Content-Type: application/json\" \\"
echo "       -d '{\"messages\":[{\"role\":\"user\",\"content\":\"What is Terraform?\"}]}'"
echo ""
echo "📖 Documentation:"
echo "   • README.md - Project overview"
echo "   • MODEL_SETUP.md - Model setup guide"
echo "   • http://localhost:8000/docs - API docs"
echo ""
echo "======================================================================"
