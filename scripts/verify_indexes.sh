#!/bin/bash

###############################################################################
# Index Verification Script for reconPoint
# Verifies that performance indexes were created successfully
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Find database container
db_container=$(docker ps --format '{{.Names}}' | grep "reconpoint.*db\|reconpoint.*postgres" | head -n 1)

if [ -z "$db_container" ]; then
    print_error "Database container not found"
    print_info "Make sure reconPoint is running: docker-compose up -d"
    exit 1
fi

print_header "Index Verification Report"
print_info "Database container: $db_container"

# Expected indexes
declare -a expected_indexes=(
    "subdomain_name_idx"
    "subdomain_scan_name_idx"
    "subdomain_domain_date_idx"
    "subdomain_status_idx"
    "subdomain_important_idx"
    "vuln_scan_severity_idx"
    "vuln_domain_status_idx"
    "vuln_discovered_idx"
    "vuln_severity_idx"
    "endpoint_scan_status_idx"
    "endpoint_subdomain_idx"
    "endpoint_url_idx"
    "scan_domain_date_idx"
    "scan_status_idx"
    "scan_start_date_idx"
    "domain_name_idx"
    "domain_project_date_idx"
    "domain_scan_date_idx"
)

print_header "Checking Individual Indexes"

missing_count=0
found_count=0

for index in "${expected_indexes[@]}"; do
    result=$(docker exec "$db_container" psql -U postgres -d reconpoint_db -t -c "
        SELECT COUNT(*) FROM pg_indexes WHERE indexname = '$index';
    " 2>/dev/null | tr -d ' ')
    
    if [ "$result" = "1" ]; then
        print_success "$index"
        ((found_count++))
    else
        print_error "$index (MISSING)"
        ((missing_count++))
    fi
done

echo ""
print_info "Found: $found_count/${#expected_indexes[@]} indexes"

if [ $missing_count -gt 0 ]; then
    print_error "$missing_count indexes are missing!"
    echo ""
    print_info "To fix this, run: ./scripts/migrate_database.sh"
    exit 1
fi

print_header "Index Details"

docker exec "$db_container" psql -U postgres -d reconpoint_db -c "
    SELECT 
        schemaname,
        tablename,
        indexname,
        pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
    FROM pg_indexes 
    WHERE indexname LIKE '%_idx' 
    ORDER BY tablename, indexname;
"

print_header "Index Usage Statistics"

docker exec "$db_container" psql -U postgres -d reconpoint_db -c "
    SELECT 
        schemaname,
        tablename,
        indexname,
        idx_scan as scans,
        idx_tup_read as tuples_read,
        idx_tup_fetch as tuples_fetched
    FROM pg_stat_user_indexes
    WHERE indexname LIKE '%_idx'
    ORDER BY idx_scan DESC
    LIMIT 20;
"

print_header "Database Size"

docker exec "$db_container" psql -U postgres -d reconpoint_db -c "
    SELECT pg_size_pretty(pg_database_size('reconpoint_db')) as database_size;
"

print_header "Table Sizes"

docker exec "$db_container" psql -U postgres -d reconpoint_db -c "
    SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
        pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename IN ('startscan_subdomain', 'startscan_vulnerability', 'startscan_endpoint', 'startscan_scanhistory', 'targetapp_domain')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

print_success "Verification complete!"
echo ""
print_info "All indexes are in place and ready to use"
print_info "Monitor index usage over time to ensure they're being utilized"
