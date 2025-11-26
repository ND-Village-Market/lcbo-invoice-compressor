#!/bin/bash
# LCBO Invoice Processor - Setup Script

set -e

echo "=========================================="
echo "LCBO Invoice Processor - Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.7+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check Node.js
echo -e "${BLUE}Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 14+"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"

# Setup backend
echo ""
echo -e "${BLUE}Setting up backend...${NC}"
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv backend/venv
fi
source backend/venv/bin/activate
cd backend
pip install -q -r requirements.txt
cd ..
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Setup frontend
echo ""
echo -e "${BLUE}Setting up frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install --silent
fi
cd ..
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

echo ""
echo -e "${GREEN}=========================================="
echo "Setup complete!"
echo "==========================================${NC}"
echo ""
echo "To start the application, run:"
echo "  ./start.sh"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
