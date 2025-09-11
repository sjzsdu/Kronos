#!/bin/bash

# Kronos Stock Prediction App - Traefik Deployment Script
# Author: Assistant
# Date: 2025-09-11

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Setup hosts file
setup_hosts() {
    print_header "Setting up local DNS"
    
    if ! grep -q "kronos.localhost" /etc/hosts; then
        print_warning "Adding kronos.localhost to /etc/hosts (requires sudo)"
        echo "127.0.0.1 kronos.localhost" | sudo tee -a /etc/hosts
        print_success "Added kronos.localhost to /etc/hosts"
    else
        print_success "kronos.localhost already in /etc/hosts"
    fi
    
    if ! grep -q "stock-prediction.local" /etc/hosts; then
        print_warning "Adding stock-prediction.local to /etc/hosts (requires sudo)"
        echo "127.0.0.1 stock-prediction.local" | sudo tee -a /etc/hosts
        print_success "Added stock-prediction.local to /etc/hosts"
    else
        print_success "stock-prediction.local already in /etc/hosts"
    fi
}

# Build and start services
start_services() {
    print_header "Starting Kronos Stock Prediction with Traefik"
    
    # Create necessary directories
    mkdir -p prediction_results cache
    
    # Build and start services
    print_color $BLUE "Building and starting services..."
    docker-compose up -d --build
    
    # Wait for services to be ready
    print_color $BLUE "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_service_health
}

# Check service health
check_service_health() {
    print_header "Checking Service Health"
    
    # Check Traefik
    if curl -s -f http://localhost:8080/api/overview > /dev/null; then
        print_success "Traefik dashboard is accessible at http://localhost:8080"
    else
        print_error "Traefik dashboard is not accessible"
    fi
    
    # Check application
    if curl -s -f http://kronos.localhost/api/models > /dev/null; then
        print_success "Kronos app is accessible at http://kronos.localhost"
    else
        print_warning "Kronos app may still be starting up..."
        print_color $YELLOW "Waiting 20 more seconds..."
        sleep 20
        
        if curl -s -f http://kronos.localhost/api/models > /dev/null; then
            print_success "Kronos app is now accessible at http://kronos.localhost"
        else
            print_error "Kronos app is not responding. Check logs with: docker-compose logs kronos-app"
        fi
    fi
}

# Show service information
show_info() {
    print_header "Service Information"
    
    print_color $GREEN "🌐 Access URLs:"
    echo "  - Stock Prediction App: http://kronos.localhost"
    echo "  - Alternative URL:       http://stock-prediction.local"
    echo "  - Traefik Dashboard:     http://localhost:8080"
    echo ""
    
    print_color $GREEN "🐳 Docker Services:"
    docker-compose ps
    echo ""
    
    print_color $GREEN "📝 Useful Commands:"
    echo "  - View logs:           docker-compose logs -f"
    echo "  - Stop services:       docker-compose down"
    echo "  - Restart services:    docker-compose restart"
    echo "  - Update app:          docker-compose up -d --build kronos-app"
    echo ""
    
    print_color $GREEN "📁 Data Directories:"
    echo "  - Predictions:         ./prediction_results/"
    echo "  - Cache:              ./cache/"
}

# Stop services
stop_services() {
    print_header "Stopping Services"
    docker-compose down
    print_success "Services stopped"
}

# Show logs
show_logs() {
    print_header "Service Logs"
    docker-compose logs -f
}

# Main script logic
case "${1:-start}" in
    "start")
        check_docker
        setup_hosts
        start_services
        show_info
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
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
    "help")
        print_header "Kronos Traefik Deployment Script"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start    - Start services (default)"
        echo "  stop     - Stop services"
        echo "  restart  - Restart services"
        echo "  logs     - Show service logs"
        echo "  status   - Check service status"
        echo "  help     - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        print_color $YELLOW "Use '$0 help' for usage information"
        exit 1
        ;;
esac
