#!/bin/bash

###############################################################################
# Rollback Script for reconPoint Database Indexes
# Removes all performance indexes added by the migration
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

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_header "reconPoint Index Rollback"

print_warning "WARNING: This will remove all performance indexes"
print_warning "This may impact database query performance"
echo ""
print_info "This script will:"
echo "  1. Drop all performance indexes"
echo "  2. Keep the migration records (safe)"
echo "  3. NOT restore any data (indexes are non-destructive)"
echo ""
print_warning "To fully revert migrations, restore from database backup"
echo ""

read -p "Are you sure you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    print_error "Rollback cancelled by user"
    exit 0
fi

# Find database container
db_container=$(docker ps --format '{{.Names}}' | grep "reconpoint.*db\|reconpoint.*postgres" | head -n 1)

if [ -z "$db_container" ]; then
    print_error "Database container not found"
    print_info "Make sure reconPoint is running: docker-compose up -d"
    exit 1
fi

print_info "Using database container: $db_container"

print_header "Dropping Indexes"

# Execute SQL to drop all indexes
docker exec "$db_container" psql -U postgres -d reconpoint_db << 'EOSQL'
-- Drop startScan app indexes
DROP INDEX IF EXISTS subdomain_name_idx;
DROP INDEX IF EXISTS subdomain_scan_name_idx;
DROP INDEX IF EXISTS subdomain_domain_date_idx;
DROP INDEX IF EXISTS subdomain_status_idx;
DROP INDEX IF EXISTS subdomain_important_idx;
DROP INDEX IF EXISTS vuln_scan_severity_idx;
DROP INDEX IF EXISTS vuln_domain_status_idx;
DROP INDEX IF EXISTS vuln_discovered_idx;
DROP INDEX IF EXISTS vuln_severity_idx;
DROP INDEX IF EXISTS endpoint_scan_status_idx;
DROP INDEX IF EXISTS endpoint_subdomain_idx;
DROP INDEX IF EXISTS endpoint_url_idx;
DROP INDEX IF EXISTS scan_domain_date_idx;
DROP INDEX IF EXISTS scan_status_idx;
DROP INDEX IF EXISTS scan_start_date_idx;

-- Drop targetApp indexes
DROP INDEX IF EXISTS domain_name_idx;
DROP INDEX IF EXISTS domain_project_date_idx;
DROP INDEX IF EXISTS domain_scan_date_idx;
EOSQL

if [ $? -eq 0 ]; then
    print_success "All indexes dropped successfully"
else
    print_error "Failed to drop some indexes"
    exit 1
fi

print_header "Verification"

# Check if indexes still exist
remaining=$(docker exec "$db_container" psql -U postgres -d reconpoint_db -t -c "
    SELECT COUNT(*) FROM pg_indexes WHERE indexname LIKE '%_idx';
" | tr -d ' ')

if [ "$remaining" = "0" ]; then
    print_success "All performance indexes removed"
else
    print_warning "$remaining indexes still exist"
    print_info "Listing remaining indexes:"
    docker exec "$db_container" psql -U postgres -d reconpoint_db -c "
        SELECT indexname FROM pg_indexes WHERE indexname LIKE '%_idx';
    "
fi

print_header "Database Size After Rollback"

docker exec "$db_container" psql -U postgres -d reconpoint_db -c "
    SELECT pg_size_pretty(pg_database_size('reconpoint_db')) as database_size;
"

print_header "Rollback Complete"

print_success "Index rollback completed successfully"
echo ""
print_warning "Note: Migration records are still in place"
print_info "To reapply indexes, run: ./scripts/migrate_database.sh"
echo ""
print_info "If you need to fully revert the migration:"
echo "  1. Restore from database backup"
echo "  2. Or run: python manage.py migrate startScan 0002"
echo "  3. And run: python manage.py migrate targetApp 0001"
