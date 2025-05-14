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
LOG_DIR="/var/log/nginx"
DASHBOARD_DIR="/usr/share/nginx/html/dashboard"
ANALYSIS_INTERVAL=300  # 5 minutes
TOP_IPS=10
TOP_URLS=10
ERROR_THRESHOLD=10

# Create metrics directory
mkdir -p "${DASHBOARD_DIR}/metrics"

# Analyze access logs
analyze_access_logs() {
    local access_log="${LOG_DIR}/access.log"
    local metrics_file="${DASHBOARD_DIR}/metrics/access_metrics.json"
    
    log_info "Analyzing access logs..."
    
    # Calculate metrics
    local total_requests=$(wc -l < "$access_log")
    local unique_ips=$(awk '{print $1}' "$access_log" | sort -u | wc -l)
    local error_count=$(grep ' [45][0-9][0-9] ' "$access_log" | wc -l)
    
    # Get top IPs
    local top_ips=$(awk '{print $1}' "$access_log" | sort | uniq -c | sort -rn | head -n $TOP_IPS | \
        awk '{printf "{\"ip\":\"%s\",\"count\":%d},",$2,$1}' | sed 's/,$//')
    
    # Get top URLs
    local top_urls=$(awk '{print $7}' "$access_log" | sort | uniq -c | sort -rn | head -n $TOP_URLS | \
        awk '{printf "{\"url\":\"%s\",\"count\":%d},",$2,$1}' | sed 's/,$//')
    
    # Calculate response time statistics
    local avg_response_time=$(awk '{sum+=$NF} END {printf "%.3f", sum/NR}' "$access_log")
    
    # Create JSON metrics
    cat > "$metrics_file" <<EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "total_requests": $total_requests,
    "unique_ips": $unique_ips,
    "error_count": $error_count,
    "average_response_time": $avg_response_time,
    "top_ips": [$top_ips],
    "top_urls": [$top_urls]
}
EOF
}

# Analyze error logs
analyze_error_logs() {
    local error_log="${LOG_DIR}/error.log"
    local metrics_file="${DASHBOARD_DIR}/metrics/error_metrics.json"
    
    log_info "Analyzing error logs..."
    
    # Get recent errors
    local recent_errors=$(tail -n 50 "$error_log" | \
        awk '{printf "{\"timestamp\":\"%s\",\"level\":\"%s\",\"message\":\"%s\"},",$1,$2,substr($0,index($0,$3))}' | \
        sed 's/,$//')
    
    # Calculate error statistics
    local error_count=$(wc -l < "$error_log")
    local critical_errors=$(grep -c "critical" "$error_log")
    local warning_errors=$(grep -c "warn" "$error_log")
    
    # Create JSON metrics
    cat > "$metrics_file" <<EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "total_errors": $error_count,
    "critical_errors": $critical_errors,
    "warning_errors": $warning_errors,
    "recent_errors": [$recent_errors]
}
EOF

    # Check for critical conditions
    if [ "$critical_errors" -gt "$ERROR_THRESHOLD" ]; then
        notify_critical_errors "$critical_errors"
    fi
}

# Create system metrics
collect_system_metrics() {
    local metrics_file="${DASHBOARD_DIR}/metrics/system_metrics.json"
    
    log_info "Collecting system metrics..."
    
    # Get system metrics
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
    local memory_usage=$(free | grep Mem | awk '{print $3/$2 * 100}')
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    
    # Create JSON metrics
    cat > "$metrics_file" <<EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "cpu_usage": $cpu_usage,
    "memory_usage": $memory_usage,
    "disk_usage": $disk_usage
}
EOF
}

# Notify about critical errors
notify_critical_errors() {
    local count=$1
    local notification_file="${DASHBOARD_DIR}/notifications.json"
    
    log_warn "Critical error threshold exceeded: $count errors"
    
    # Add notification
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"timestamp\":\"$timestamp\",\"type\":\"critical\",\"message\":\"Critical error threshold exceeded: $count errors\"}" >> "$notification_file"
}

# Main execution loop
main() {
    while true; do
        analyze_access_logs
        analyze_error_logs
        collect_system_metrics
        sleep $ANALYSIS_INTERVAL
    done
}

# Execute main function
main

