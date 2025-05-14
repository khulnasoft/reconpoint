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
SSL_DIR="ssl"
EXPIRY_WARNING_DAYS=30
CHECK_INTERVAL=86400  # 24 hours in seconds

# Check SSL certificate expiration
check_ssl_expiry() {
    local cert_file="${SSL_DIR}/fullchain.pem"
    if [[ ! -f "$cert_file" ]]; then
        log_error "Certificate file not found: $cert_file"
        return 1
    fi

    # Get expiration date
    local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
    local expiry_epoch=$(date -j -f "%b %d %T %Y %Z" "$expiry_date" +%s)
    local current_epoch=$(date +%s)
    local days_remaining=$(( ($expiry_epoch - $current_epoch) / 86400 ))

    # Create JSON response
    local json_response=$(cat <<EOF
{
    "status": "$([ $days_remaining -gt $EXPIRY_WARNING_DAYS ] && echo "valid" || echo "warning")",
    "days_remaining": $days_remaining,
    "expiry_date": "$(date -r $expiry_epoch "+%Y-%m-%d")",
    "issuer": "$(openssl x509 -issuer -noout -in "$cert_file" | cut -d= -f2-)"
}
EOF
)

    echo "$json_response" > "/usr/share/nginx/html/dashboard/ssl-status.json"

    # Send notification if expiring soon
    if [ $days_remaining -le $EXPIRY_WARNING_DAYS ]; then
        log_warn "SSL Certificate expires in $days_remaining days"
        notify_expiry "$days_remaining"
    else
        log_info "SSL Certificate valid for $days_remaining days"
    fi
}

# Notify about expiring certificate
notify_expiry() {
    local days=$1
    local notification_file="/usr/share/nginx/html/dashboard/notifications.json"
    
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    local message="SSL Certificate expires in $days days"
    
    # Append to notifications file
    local json_notification=$(cat <<EOF
{
    "timestamp": "$timestamp",
    "type": "warning",
    "message": "$message"
}
EOF
)

    echo "$json_notification" >> "$notification_file"
}

# Main execution
main() {
    while true; do
        check_ssl_expiry
        sleep $CHECK_INTERVAL
    done
}

# Execute main function
main

