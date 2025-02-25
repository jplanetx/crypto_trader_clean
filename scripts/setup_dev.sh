#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up development environment for CryptoTrader Clean...${NC}\n"

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python $required_version or higher is required${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -e ".[dev,test]"

# Create logs directory
mkdir -p logs

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
fi

# Setup git hooks
if [ -d ".git" ]; then
    echo -e "${YELLOW}Setting up git hooks...${NC}"
    python scripts/setup_dev.py
fi

echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "\nNext steps:"
echo -e "1. Update config/config.json with your settings"
echo -e "2. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "3. Run tests: ${YELLOW}pytest tests/${NC}"
echo -e "4. Try the example: ${YELLOW}python examples/basic_trading.py${NC}"
