#!/bin/bash

###############################################################################
# Database Migration Script for reconPoint
# Implements performance indexes as per DATABASE_MIGRATION_GUIDE.md
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/web"

# Timestamp for backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$PROJECT_ROOT/backups"

###############################################################################
# Helper Functions
###############################################################################

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

###############################################################################
# Pre-Migration Checks
###############################################################################

pre_migration_checks() {
    print_header "Pre-Migration Checks"
    
    # Check if we're in the correct directory
    if [ ! -f "$WEB_DIR/manage.py" ]; then
        print_error "manage.py not found in $WEB_DIR"
        exit 1
    fi
    print_success "Found Django project"
    
    # Check if Docker is running (if using Docker)
    if command -v docker &> /dev/null; then
        if docker ps &> /dev/null; then
            print_success "Docker is running"
        else
            print_warning "Docker is not running or not accessible"
        fi
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    print_success "Backup directory ready: $BACKUP_DIR"
}

###############################################################################
# Database Backup
###############################################################################

backup_database() {
    print_header "Database Backup"
    
    local backup_file="$BACKUP_DIR/reconpoint_backup_$TIMESTAMP.sql"
    
    print_info "Creating database backup..."
    
    # Check if running in Docker
    if docker ps --format '{{.Names}}' | grep -q "reconpoint.*db\|reconpoint.*postgres"; then
        local db_container=$(docker ps --format '{{.Names}}' | grep "reconpoint.*db\|reconpoint.*postgres" | head -n 1)
        print_info "Using Docker container: $db_container"
        
        docker exec "$db_container" pg_dump -U postgres reconpoint_db > "$backup_file" 2>/dev/null || {
            print_warning "Could not create backup via Docker. Continuing without backup."
            return 0
        }
    else
        print_warning "Database container not found. Skipping backup."
        print_warning "Please ensure you have a backup before proceeding!"
        read -p "Continue without backup? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            print_error "Migration cancelled by user"
            exit 1
        fi
        return 0
    fi
    
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        print_success "Backup created: $backup_file"
        print_info "Backup size: $(du -h "$backup_file" | cut -f1)"
    else
        print_warning "Backup file is empty or not created"
    fi
}

###############################################################################
# Check Database Size
###############################################################################

check_database_size() {
    print_header "Database Size Check"
    
    if docker ps --format '{{.Names}}' | grep -q "reconpoint.*db\|reconpoint.*postgres"; then
        local db_container=$(docker ps --format '{{.Names}}' | grep "reconpoint.*db\|reconpoint.*postgres" | head -n 1)
        
        print_info "Current database size:"
        docker exec "$db_container" psql -U postgres -d reconpoint_db -c "SELECT pg_size_pretty(pg_database_size('reconpoint_db'));" 2>/dev/null || {
            print_warning "Could not check database size"
        }
    else
        print_warning "Database container not found. Skipping size check."
    fi
}

###############################################################################
# Show Migration Plan
###############################################################################

show_migration_plan() {
    print_header "Migration Plan"
    
    cd "$WEB_DIR"
    
    print_info "Checking for pending migrations..."
    python manage.py migrate --plan || {
        print_error "Failed to check migration plan"
        exit 1
    }
}

###############################################################################
# Run Migrations
###############################################################################

run_migrations() {
    print_header "Running Migrations"
    
    cd "$WEB_DIR"
    
    print_info "Applying migrations..."
    
    # Run migrations with output
    python manage.py migrate --verbosity 2 || {
        print_error "Migration failed!"
        print_error "Please check the error messages above"
        exit 1
    }
    
    print_success "Migrations completed successfully"
}

###############################################################################
# Verify Indexes
###############################################################################

verify_indexes() {
    print_header "Verifying Indexes"
    
    if docker ps --format '{{.Names}}' | grep -q "reconpoint.*db\|reconpoint.*postgres"; then
        local db_container=$(docker ps --format '{{.Names}}' | grep "reconpoint.*db\|reconpoint.*postgres" | head -n 1)
        
        print_info "Checking created indexes..."
        
        docker exec "$db_container" psql -U postgres -d reconpoint_db -c "
            SELECT 
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
            FROM pg_indexes 
            WHERE indexname LIKE '%_idx' 
            ORDER BY tablename, indexname;
        " 2>/dev/null || {
            print_warning "Could not verify indexes"
            return 0
        }
        
        print_success "Index verification complete"
    else
        print_warning "Database container not found. Skipping index verification."
    fi
}

###############################################################################
# Post-Migration Checks
###############################################################################

post_migration_checks() {
    print_header "Post-Migration Checks"
    
    cd "$WEB_DIR"
    
    # Check for any pending migrations
    print_info "Checking for remaining migrations..."
    if python manage.py showmigrations | grep -q "\[ \]"; then
        print_warning "There are still pending migrations"
    else
        print_success "All migrations applied"
    fi
    
    # Run Django checks
    print_info "Running Django system checks..."
    python manage.py check || {
        print_warning "Django checks found issues"
    }
}

###############################################################################
# Generate Rollback Script
###############################################################################

generate_rollback_script() {
    print_header "Generating Rollback Script"
    
    local rollback_file="$BACKUP_DIR/rollback_$TIMESTAMP.sh"
    
    cat > "$rollback_file" << 'EOF'
#!/bin/bash

# Rollback script for database migration
# Generated automatically

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}WARNING: This will rollback the database migration${NC}"
echo -e "${YELLOW}This will drop all performance indexes${NC}"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${RED}Rollback cancelled${NC}"
    exit 1
fi

# Find database container
db_container=$(docker ps --format '{{.Names}}' | grep "reconpoint.*db\|reconpoint.*postgres" | head -n 1)

if [ -z "$db_container" ]; then
    echo -e "${RED}Database container not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Dropping indexes...${NC}"

docker exec "$db_container" psql -U postgres -d reconpoint_db << 'EOSQL'
-- Drop startScan indexes
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

echo -e "${GREEN}Indexes dropped successfully${NC}"
echo -e "${YELLOW}Note: This does not revert the migration records${NC}"
echo -e "${YELLOW}To fully revert, restore from backup${NC}"
EOF

    chmod +x "$rollback_file"
    print_success "Rollback script created: $rollback_file"
}

###############################################################################
# Main Execution
###############################################################################

main() {
    print_header "reconPoint Database Migration"
    print_info "Adding performance indexes to database"
    print_info "Timestamp: $TIMESTAMP"
    
    # Confirm before proceeding
    echo ""
    print_warning "This script will:"
    echo "  1. Create a database backup"
    echo "  2. Apply performance index migrations"
    echo "  3. Verify the indexes were created"
    echo ""
    read -p "Do you want to proceed? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_error "Migration cancelled by user"
        exit 0
    fi
    
    # Execute migration steps
    pre_migration_checks
    backup_database
    check_database_size
    show_migration_plan
    run_migrations
    verify_indexes
    post_migration_checks
    generate_rollback_script
    
    # Final summary
    print_header "Migration Complete"
    print_success "Database migration completed successfully!"
    print_info "Backup location: $BACKUP_DIR"
    print_info "Rollback script: $BACKUP_DIR/rollback_$TIMESTAMP.sh"
    
    echo ""
    print_info "Next steps:"
    echo "  1. Monitor application performance"
    echo "  2. Check application logs for errors"
    echo "  3. Run performance benchmarks"
    echo "  4. See DATABASE_MIGRATION_GUIDE.md for monitoring queries"
    echo ""
}

# Run main function
main "$@"
