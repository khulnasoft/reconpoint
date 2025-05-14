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

# Configuration
BACKUP_DIR="backups"
MAX_BACKUPS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup Nginx configuration
backup_config() {
    local backup_file="${BACKUP_DIR}/nginx_config_${TIMESTAMP}.tar.gz"
    log_info "Creating Nginx configuration backup..."
    
    tar -czf "$backup_file" \
        default.conf \
        conf.d/ \
        html/ \
        ssl/ \
        .htpasswd \
        2>/dev/null || {
        log_error "Failed to create backup"
        return 1
    }
    
    log_info "Backup created: $backup_file"
}

# Rotate old backups
rotate_backups() {
    log_info "Rotating old backups..."
    local backup_count=$(ls -1 "${BACKUP_DIR}/nginx_config_"*.tar.gz 2>/dev/null | wc -l)
    
    if [ "$backup_count" -gt "$MAX_BACKUPS" ]; then
        ls -1t "${BACKUP_DIR}/nginx_config_"*.tar.gz | \
        tail -n $(( backup_count - MAX_BACKUPS )) | \
        xargs rm -f
        log_info "Removed old backups"
    fi
}

# Restore from backup
restore_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_info "Restoring from backup: $backup_file"
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    trap 'rm -rf "$temp_dir"' EXIT
    
    # Extract backup
    tar -xzf "$backup_file" -C "$temp_dir"
    
    # Verify backup contents
    for file in default.conf conf.d html ssl .htpasswd; do
        if [ ! -e "${temp_dir}/${file}" ]; then
            log_error "Invalid backup: missing ${file}"
            return 1
        fi
    done
    
    # Stop Nginx
    if docker ps -q --filter "name=nginx" >/dev/null; then
        log_info "Stopping Nginx..."
        docker stop nginx
        docker rm nginx
    fi
    
    # Restore files
    log_info "Restoring configuration files..."
    cp -r "${temp_dir}"/* .
    
    # Restart Nginx
    log_info "Restarting Nginx..."
    ./deploy-nginx.sh deploy
}

# List available backups
list_backups() {
    log_info "Available backups:"
    ls -lh "${BACKUP_DIR}/nginx_config_"*.tar.gz 2>/dev/null || {
        log_warn "No backups found"
        return 0
    }
}

# Main execution
main() {
    local command="${1:-backup}"
    
    case "$command" in
        "backup")
            backup_config
            rotate_backups
            ;;
        "restore")
            if [ -z "${2:-}" ]; then
                log_error "Please specify backup file to restore"
                exit 1
            fi
            restore_backup "$2"
            ;;
        "list")
            list_backups
            ;;
        *)
            echo "Usage: $0 [backup|restore <file>|list]"
            exit 1
            ;;
    esac
}

# Execute main function with all script arguments
main "$@"

