#!/bin/bash

# Hair Salon Docker Management Scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Hair Salon Docker Management Scripts${NC}"
echo "=================================="

# Function to build and start development environment
dev_up() {
    echo -e "${YELLOW}Starting development environment...${NC}"
    docker-compose -f docker-compose.dev.yml up --build -d
    echo -e "${GREEN}Development environment started!${NC}"
    echo "Access your application at: http://localhost:8000"
    echo "Access Swagger docs at: http://localhost:8000"
}

# Function to stop development environment
dev_down() {
    echo -e "${YELLOW}Stopping development environment...${NC}"
    docker-compose -f docker-compose.dev.yml down
    echo -e "${GREEN}Development environment stopped!${NC}"
}

# Function to build and start production environment
prod_up() {
    echo -e "${YELLOW}Starting production environment...${NC}"
    docker-compose up --build -d
    echo -e "${GREEN}Production environment started!${NC}"
    echo "Access your application at: http://localhost:8000"
}

# Function to stop production environment
prod_down() {
    echo -e "${YELLOW}Stopping production environment...${NC}"
    docker-compose down
    echo -e "${GREEN}Production environment stopped!${NC}"
}

# Function to view logs
logs() {
    if [ "$1" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml logs -f
    else
        docker-compose logs -f
    fi
}

# Function to run Django management commands
manage() {
    if [ "$1" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml exec web python manage.py "${@:2}"
    else
        docker-compose exec web python manage.py "${@:2}"
    fi
}

# Function to create superuser
create_superuser() {
    echo -e "${YELLOW}Creating Django superuser...${NC}"
    if [ "$1" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
    else
        docker-compose exec web python manage.py createsuperuser
    fi
}

# Function to reset database
reset_db() {
    echo -e "${RED}WARNING: This will delete all data!${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$1" == "dev" ]; then
            docker-compose -f docker-compose.dev.yml down -v
            docker-compose -f docker-compose.dev.yml up --build -d
        else
            docker-compose down -v
            docker-compose up --build -d
        fi
        echo -e "${GREEN}Database reset complete!${NC}"
    fi
}

# Main menu
case "$1" in
    "dev-up")
        dev_up
        ;;
    "dev-down")
        dev_down
        ;;
    "prod-up")
        prod_up
        ;;
    "prod-down")
        prod_down
        ;;
    "logs")
        logs $2
        ;;
    "manage")
        manage "${@:2}"
        ;;
    "superuser")
        create_superuser $2
        ;;
    "reset-db")
        reset_db $2
        ;;
    *)
        echo "Usage: $0 {dev-up|dev-down|prod-up|prod-down|logs|manage|superuser|reset-db}"
        echo ""
        echo "Examples:"
        echo "  $0 dev-up              # Start development environment"
        echo "  $0 dev-down            # Stop development environment"
        echo "  $0 prod-up             # Start production environment"
        echo "  $0 prod-down           # Stop production environment"
        echo "  $0 logs dev            # View development logs"
        echo "  $0 logs                # View production logs"
        echo "  $0 manage dev migrate  # Run migrations in dev"
        echo "  $0 superuser dev       # Create superuser in dev"
        echo "  $0 reset-db dev        # Reset development database"
        exit 1
        ;;
esac
