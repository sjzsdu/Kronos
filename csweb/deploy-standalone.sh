#!/bin/bash

# Kronos Stock Prediction App - Standalone Deployment Script
# For integration with existing Traefik setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_color() {
    printf "${1}${2}${NC}\n"
}

print_header() {
    print_color $BLUE "=================================="
    print_color $BLUE "$1"
    print_color $BLUE "=================================="
}

print_success() {
    print_color $GREEN "✅ $1"
}

print_warning() {
    print_color $YELLOW "⚠️  $1"
}

print_error() {
    print_color $RED "❌ $1"
}

# Configuration
COMPOSE_FILE="docker-compose.standalone.yml"
DEFAULT_TRAEFIK_NETWORK="traefik"
DEFAULT_DOMAIN="stock.localhost"

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

# Check Traefik network
check_traefik_network() {
    print_header "Checking Traefik Network"
    
    TRAEFIK_NETWORK=${1:-$DEFAULT_TRAEFIK_NETWORK}
    
    if docker network ls | grep -q "$TRAEFIK_NETWORK"; then
        print_success "Traefik network '$TRAEFIK_NETWORK' found"
        return 0
    else
        print_warning "Traefik network '$TRAEFIK_NETWORK' not found"
        echo ""
        print_color $YELLOW "Available networks:"
        docker network ls
        echo ""
        read -p "Enter the correct Traefik network name: " TRAEFIK_NETWORK
        
        if docker network ls | grep -q "$TRAEFIK_NETWORK"; then
            print_success "Using network: $TRAEFIK_NETWORK"
            # Update docker-compose file
            sed -i.bak "s/name: traefik/name: $TRAEFIK_NETWORK/" $COMPOSE_FILE
            return 0
        else
            print_error "Network '$TRAEFIK_NETWORK' still not found"
            exit 1
        fi
    fi
}

# Configure domain
configure_domain() {
    print_header "Domain Configuration"
    
    DOMAIN=${1:-$DEFAULT_DOMAIN}
    
    print_color $BLUE "Current domain configuration: $DOMAIN"
    read -p "Enter your domain (or press Enter to use $DOMAIN): " USER_DOMAIN
    
    if [ ! -z "$USER_DOMAIN" ]; then
        DOMAIN=$USER_DOMAIN
        # Update docker-compose file
        sed -i.bak "s/stock.your-domain.com/$DOMAIN/g" $COMPOSE_FILE
        print_success "Domain set to: $DOMAIN"
    else
        print_success "Using default domain: $DOMAIN"
    fi
    
    # Add to hosts file for local testing
    if [ "$DOMAIN" = "stock.localhost" ] || [[ "$DOMAIN" == *.local ]]; then
        if ! grep -q "$DOMAIN" /etc/hosts; then
            print_warning "Adding $DOMAIN to /etc/hosts (requires sudo)"
            echo "127.0.0.1 $DOMAIN" | sudo tee -a /etc/hosts
            print_success "Added $DOMAIN to /etc/hosts"
        fi
    fi
}

# Start services
start_services() {
    print_header "Starting Kronos Stock Prediction App"
    
    # Create necessary directories
    mkdir -p prediction_results cache
    
    # Start the service
    print_color $BLUE "Building and starting the application..."
    docker-compose -f $COMPOSE_FILE up -d --build
    
    # Wait for service to be ready
    print_color $BLUE "Waiting for service to be ready..."
    sleep 15
    
    check_service_health
}

# Check service health
check_service_health() {
    print_header "Checking Service Health"
    
    # Check if container is running
    if docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        print_success "Container is running"
    else
        print_error "Container is not running"
        docker-compose -f $COMPOSE_FILE logs
        return 1
    fi
    
    # Check internal health
    if docker-compose -f $COMPOSE_FILE exec -T kronos-app curl -s -f http://localhost:5001/api/models > /dev/null; then
        print_success "Application is responding internally"
    else
        print_warning "Application may still be starting up..."
        sleep 10
        if docker-compose -f $COMPOSE_FILE exec -T kronos-app curl -s -f http://localhost:5001/api/models > /dev/null; then
            print_success "Application is now responding"
        else
            print_error "Application is not responding. Check logs:"
            docker-compose -f $COMPOSE_FILE logs kronos-app
            return 1
        fi
    fi
}

# Show service information
show_info() {
    print_header "Deployment Information"
    
    # Get domain from compose file
    DOMAIN=$(grep -o 'Host(`[^`]*`)' $COMPOSE_FILE | head -1 | sed 's/Host(`//;s/`)//')
    
    print_color $GREEN "🌐 Access Information:"
    echo "  - Application URL: http://$DOMAIN"
    echo "  - API Endpoint:    http://$DOMAIN/api/models"
    echo ""
    
    print_color $GREEN "🐳 Docker Information:"
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    
    print_color $GREEN "📊 Health Check:"
    echo "  - Container Status: $(docker-compose -f $COMPOSE_FILE ps --format table | tail -n +2)"
    echo ""
    
    print_color $GREEN "📝 Management Commands:"
    echo "  - View logs:          docker-compose -f $COMPOSE_FILE logs -f"
    echo "  - Stop service:       docker-compose -f $COMPOSE_FILE down"
    echo "  - Restart service:    docker-compose -f $COMPOSE_FILE restart"
    echo "  - Update application: docker-compose -f $COMPOSE_FILE up -d --build"
    echo ""
    
    print_color $GREEN "📁 Data Locations:"
    echo "  - Predictions: $(pwd)/prediction_results/"
    echo "  - Cache:      $(pwd)/cache/"
}

# Stop services
stop_services() {
    print_header "Stopping Services"
    docker-compose -f $COMPOSE_FILE down
    print_success "Service stopped"
}

# Show logs
show_logs() {
    print_header "Application Logs"
    docker-compose -f $COMPOSE_FILE logs -f
}

# Interactive setup
interactive_setup() {
    print_header "Interactive Setup"
    
    # Check Traefik network
    check_traefik_network
    
    # Configure domain
    configure_domain
    
    # Start services
    start_services
    
    # Show information
    show_info
}

# Main script logic
case "${1:-start}" in
    "start")
        check_docker
        start_services
        show_info
        ;;
    "setup")
        check_docker
        interactive_setup
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 2
        start_services
        show_info
        ;;
    "logs")
        show_logs
        ;;
    "status")
        check_service_health
        show_info
        ;;
    "update")
        print_header "Updating Application"
        docker-compose -f $COMPOSE_FILE down
        docker-compose -f $COMPOSE_FILE build --no-cache
        docker-compose -f $COMPOSE_FILE up -d
        check_service_health
        show_info
        ;;
    "help")
        print_header "Kronos Standalone Deployment Script"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start    - Start the application (default)"
        echo "  setup    - Interactive setup with network and domain configuration"
        echo "  stop     - Stop the application"
        echo "  restart  - Restart the application"
        echo "  logs     - Show application logs"
        echo "  status   - Check application status"
        echo "  update   - Update and rebuild the application"
        echo "  help     - Show this help"
        echo ""
        echo "Environment Variables:"
        echo "  TRAEFIK_NETWORK - Traefik network name (default: traefik)"
        echo "  APP_DOMAIN      - Application domain (default: stock.localhost)"
        ;;
    *)
        print_error "Unknown command: $1"
        print_color $YELLOW "Use '$0 help' for usage information"
        exit 1
        ;;
esac
