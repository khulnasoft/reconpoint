#!/bin/bash

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check required files
check_required_files() {
    local required_files=(
        "default.conf"
        "conf.d/monitoring.conf"
        "html/404.html"
        "html/50x.html"
        "html/robots.txt"
    )

    log_info "Checking required files..."
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Missing required file: $file"
            exit 1
        fi
    done
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    mkdir -p ssl
    mkdir -p html
    mkdir -p conf.d
}

# Generate self-signed SSL certificate for development
generate_ssl_cert() {
    if [[ ! -f "ssl/fullchain.pem" ]] || [[ ! -f "ssl/privkey.pem" ]]; then
        log_info "Generating self-signed SSL certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/privkey.pem \
            -out ssl/fullchain.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    else
        log_info "SSL certificates already exist"
    fi
}

# Create basic auth for monitoring
create_basic_auth() {
    local auth_file=".htpasswd"
    if [[ ! -f "$auth_file" ]]; then
        log_info "Creating basic auth file..."
        echo "admin:$(openssl passwd -apr1 secure_password)" > "$auth_file"
    fi
}

# Test Nginx configuration
test_config() {
    log_info "Testing Nginx configuration..."
    docker run --rm \
        -v "$(pwd):/etc/nginx:ro" \
        nginx:alpine \
        nginx -t
}

# Deploy Nginx configuration
deploy_nginx() {
    log_info "Deploying Nginx configuration..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi

    # Create Docker network if it doesn't exist
    if ! docker network inspect web >/dev/null 2>&1; then
        log_info "Creating Docker network: web"
        docker network create web
    fi

    # Stop existing Nginx container if running
    if docker ps -q --filter "name=nginx" >/dev/null; then
        log_info "Stopping existing Nginx container..."
        docker stop nginx
        docker rm nginx
    fi

    # Start new Nginx container
    log_info "Starting Nginx container..."
    docker run -d \
        --name nginx \
        --network web \
        --restart unless-stopped \
        -p 80:80 \
        -p 443:443 \
        -v "$(pwd)/default.conf:/etc/nginx/nginx.conf:ro" \
        -v "$(pwd)/conf.d:/etc/nginx/conf.d:ro" \
        -v "$(pwd)/html:/usr/share/nginx/html:ro" \
        -v "$(pwd)/ssl:/etc/nginx/ssl:ro" \
        -v "$(pwd)/.htpasswd:/etc/nginx/.htpasswd:ro" \
        nginx:alpine

    log_info "Nginx deployment complete"
}

# Check Nginx status
check_status() {
    log_info "Checking Nginx status..."
    if docker ps -q --filter "name=nginx" >/dev/null; then
        log_info "Nginx is running"
        docker logs nginx
    else
        log_error "Nginx is not running"
        exit 1
    fi
}

# Main execution
main() {
    local command="${1:-deploy}"

    case "$command" in
        "deploy")
            check_required_files
            create_directories
            generate_ssl_cert
            create_basic_auth
            test_config
            deploy_nginx
            check_status
            ;;
        "test")
            test_config
            ;;
        "status")
            check_status
            ;;
        "ssl")
            generate_ssl_cert
            ;;
        *)
            echo "Usage: $0 [deploy|test|status|ssl]"
            exit 1
            ;;
    esac
}

# Execute main function with all script arguments
main "$@"

