#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear

echo -e "${BLUE}"
echo "════════════════════════════════════════════════════════════"
echo "  Literate Lamp - Setup Python Virtual Environment"
echo "════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    clear
    echo -e "${RED}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                     ERROR                                 ║"
    echo "║              Python 3 NOT FOUND on System                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    echo "Please install Python 3:"
    echo -e "  ${BLUE}Ubuntu/Debian:${NC} sudo apt-get install python3 python3-venv"
    echo -e "  ${BLUE}macOS:${NC} brew install python3"
    echo -e "  ${BLUE}Fedora:${NC} sudo dnf install python3"
    echo
    exit 1
fi

echo -e "${GREEN}✓ Python found:${NC}"
python3 --version
echo

# Check if venv already exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    echo "  Activating existing venv..."
    source venv/bin/activate
else
    echo -e "${YELLOW}⏳ Creating virtual environment...${NC}"
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo -e "${RED} Failed to create virtual environment${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo
    echo -e "${YELLOW}⏳ Activating virtual environment...${NC}"
    source venv/bin/activate
fi

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo

echo -e "${YELLOW}⏳ Upgrading pip...${NC}"
python -m pip install --upgrade pip --quiet 2>/dev/null || true
echo -e "${GREEN}✓ Pip upgraded${NC}"
echo

echo -e "${YELLOW}⏳ Installing Python dependencies from backend/requirements.txt...${NC}"
pip install -r backend/requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED} Failed to install Python dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    clear
    echo -e "${YELLOW}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                      WARNING                              ║"
    echo "║              Node.js NOT FOUND on System                  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    echo "Please install Node.js:"
    echo -e "  ${BLUE}Ubuntu/Debian:${NC} sudo apt-get install nodejs npm"
    echo -e "  ${BLUE}macOS:${NC} brew install node"
    echo -e "  ${BLUE}Fedora:${NC} sudo dnf install nodejs"
    echo -e "  ${BLUE}Or download:${NC} https://nodejs.org/"
    echo
    exit 1
fi

echo -e "${GREEN}✓ Node.js found:${NC}"
node --version
echo

echo -e "${YELLOW}⏳ Installing frontend dependencies...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
    
    if [ $? -ne 0 ]; then
        echo -e "${RED} Failed to install frontend dependencies${NC}"
        cd ..
        exit 1
    fi
else
    echo -e "${GREEN}✓ node_modules already exists, skipping npm install${NC}"
fi

cd ..

echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
echo

clear
echo -e "${BLUE}"
echo "════════════════════════════════════════════════════════════"
echo "  ✓ SETUP COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo
echo "Next steps:"
echo "  1. Edit .env file and add your API keys"
echo "  2. Run './start.sh' to start the application"
echo
echo "Documentation: Open README.md"
echo
