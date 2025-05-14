#!/bin/bash

# Strict mode settings
set -euo pipefail
IFS=$'\n\t'

# Color codes for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handler
handle_error() {
    local line_no=$1
    local error_code=$2
    log_error "Error occurred in script at line: ${line_no}, error code: ${error_code}"
    exit ${error_code}
}

# Set up error handling
trap 'handle_error ${LINENO} $?' ERR

# Environment validation
validate_environment() {
    local required_vars=("DB_HOST" "DB_PORT" "DB_NAME" "DB_USER" "DB_PASSWORD")
    local missing_vars=0

    if [ "$DATABASE" = "postgres" ]; then
        for var in "${required_vars[@]}"; do
            if [ -z "${!var:-}" ]; then
                log_error "Required environment variable $var is not set"
                missing_vars=$((missing_vars + 1))
            fi
        done

        if [ $missing_vars -gt 0 ]; then
            log_error "Missing required environment variables. Exiting."
            exit 1
        fi
    fi
}

# Database connection check
wait_for_db() {
    local retries=30
    local wait_time=2

    if [ "$DATABASE" = "postgres" ]; then
        log_info "Waiting for PostgreSQL to become available..."
        
        while [ $retries -gt 0 ]; do
            if nc -z "$DB_HOST" "${DB_PORT:-5432}"; then
                log_info "PostgreSQL is available"
                return 0
            fi
            
            retries=$((retries - 1))
            if [ $retries -eq 0 ]; then
                log_error "Timeout waiting for PostgreSQL to become available"
                exit 1
            fi
            
            log_warn "Waiting for PostgreSQL... ${retries} attempts remaining"
            sleep $wait_time
        done
    fi
}

# Initialize application
initialize_app() {
    log_info "Running database migrations..."
    if ! python3 manage.py migrate --noinput; then
        log_error "Failed to apply database migrations"
        exit 1
    fi
    
    # Collect static files if needed
    if [ "${DJANGO_COLLECT_STATIC:-false}" = "true" ]; then
        log_info "Collecting static files..."
        if ! python3 manage.py collectstatic --noinput; then
            log_warn "Failed to collect static files"
        fi
    fi

    # Create cache table if needed
    if [ "${DJANGO_CREATE_CACHE_TABLE:-false}" = "true" ]; then
        log_info "Creating cache table..."
        if ! python3 manage.py createcachetable; then
            log_warn "Failed to create cache table"
        fi
    fi
}

# Start Celery worker
start_celery_worker() {
    log_info "Starting Celery worker..."
    celery -A reconpoint worker \
        --loglevel="${CELERY_LOG_LEVEL:-info}" \
        ${CELERY_EXTRA_ARGS:-}
}

# Main execution
main() {
    log_info "Starting entrypoint script..."
    
    # Validate environment variables
    validate_environment
    
    # Wait for database
    wait_for_db
    
    # Initialize application
    initialize_app
    
    # Handle Celery worker
    if [ "${CELERY_WORKER:-false}" = "true" ]; then
        start_celery_worker
        exit 0
    fi
    
    log_info "Executing command: $*"
    exec "$@"
}

# Execute main function with all script arguments
main "$@"
