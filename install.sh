#!/usr/bin/env bash
set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
  ____                   RAG   
 / __ \____  ___  ____  / __ \ 
/ / / / __ \/ _ \/ __ \/ /_/ / 
\ \_/ / /_/ /  __/ / / / _, _/  
 \____/ .___/\___/_/ /_/_/ |_|   
     /_/                        
EOF
echo -e "${NC}"
echo -e "${GREEN}Welcome to the OpenRAG Installer!${NC}\n"

# 1. Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v git >/dev/null 2>&1 || { echo -e "${RED}Error: git is required but not installed. Aborting.${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: docker is required but not installed. Aborting.${NC}"; exit 1; }
echo -e "${GREEN}Prerequisites met!${NC}\n"

# 2. Clone repository
if [ -d "OpenRAG" ]; then
    echo -e "${YELLOW}OpenRAG directory already exists. Entering directory...${NC}"
    cd OpenRAG
else
    echo -e "${YELLOW}Cloning OpenRAG repository...${NC}"
    git clone https://github.com/ardamoustafa1/OpenRAG.git
    cd OpenRAG
fi

# 3. Setup environment variables
echo -e "\n${YELLOW}Setting up environment variables...${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}.env file already exists. Skipping environment setup.${NC}"
else
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env from .env.example${NC}"
        
        # Generate secure random hex keys using openssl or python
        if command -v openssl >/dev/null 2>&1; then
            SECRET_KEY=$(openssl rand -hex 32)
            POSTGRES_PW=$(openssl rand -hex 16)
            ADMIN_PW=$(openssl rand -hex 12)
        else
            SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
            POSTGRES_PW=$(python3 -c "import secrets; print(secrets.token_hex(16))")
            ADMIN_PW=$(python3 -c "import secrets; print(secrets.token_hex(12))")
        fi
        
        # Inject secure keys into .env
        sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i.bak "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PW/" .env
        echo "INITIAL_ADMIN_PASSWORD=$ADMIN_PW" >> .env
        rm -f .env.bak
        
        echo -e "${GREEN}Automatically generated secure SECRET_KEY, POSTGRES_PASSWORD, and INITIAL_ADMIN_PASSWORD.${NC}"
    else
        echo -e "${RED}Error: .env.example not found.${NC}"
        exit 1
    fi
fi

# 4. Start services
echo -e "\n${YELLOW}Starting OpenRAG stack... (This may take a few minutes to download images)${NC}"
# Use make if available, otherwise fallback to docker compose
if command -v make >/dev/null 2>&1 && grep -q "^up:" Makefile 2>/dev/null; then
    make up
else
    docker compose up -d
fi

echo -e "\n${YELLOW}Waiting for database to be ready...${NC}"
# Wait for postgres container to report healthy
until docker compose ps postgres | grep -q "healthy"; do
    printf "."
    sleep 2
done
echo -e "\n${GREEN}Database is ready!${NC}"

echo -e "\n${YELLOW}Running database migrations...${NC}"
docker compose exec -T backend alembic upgrade head

echo -e "\n${GREEN}==============================================${NC}"
echo -e "${GREEN}OpenRAG successfully deployed!${NC}"
echo -e "${GREEN}==============================================${NC}"
echo -e "Access your application at:"
echo -e "  Frontend UI : ${BLUE}http://localhost:3000${NC}"
echo -e "  Traefik     : ${BLUE}http://localhost:8080${NC}"
echo -e ""
echo -e "Default Super Admin Account:"
echo -e "  Email    : ${YELLOW}admin@openrag.local${NC}"
echo -e "  Password : ${YELLOW}${ADMIN_PW:-admin123}${NC}"
echo -e "  *(Please change this immediately after logging in)*"
echo -e "\nEnjoy private, enterprise-grade AI!"
