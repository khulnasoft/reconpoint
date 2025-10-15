#!/bin/bash

###############################################################################
# Migration Test Script
# Tests migration files without applying them
###############################################################################

set -e

# Colors
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

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/web"

print_header "Migration Test Suite"

# Test 1: Check migration files exist
print_info "Test 1: Checking migration files exist..."

if [ -f "$WEB_DIR/startScan/migrations/0003_add_performance_indexes.py" ]; then
    print_success "startScan migration file exists"
else
    print_error "startScan migration file NOT found"
    exit 1
fi

if [ -f "$WEB_DIR/targetApp/migrations/0002_add_performance_indexes.py" ]; then
    print_success "targetApp migration file exists"
else
    print_error "targetApp migration file NOT found"
    exit 1
fi

# Test 2: Check Python syntax
print_info "Test 2: Validating Python syntax..."

if python3 -m py_compile "$WEB_DIR/startScan/migrations/0003_add_performance_indexes.py" 2>/dev/null; then
    print_success "startScan migration syntax valid"
else
    print_error "startScan migration syntax error"
    exit 1
fi

if python3 -m py_compile "$WEB_DIR/targetApp/migrations/0002_add_performance_indexes.py" 2>/dev/null; then
    print_success "targetApp migration syntax valid"
else
    print_error "targetApp migration syntax error"
    exit 1
fi

# Test 3: Check scripts exist and are executable
print_info "Test 3: Checking automation scripts..."

scripts=(
    "migrate_database.sh"
    "verify_indexes.sh"
    "rollback_indexes.sh"
    "benchmark_performance.py"
)

for script in "${scripts[@]}"; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
        if [ -x "$SCRIPT_DIR/$script" ]; then
            print_success "$script exists and is executable"
        else
            print_warning "$script exists but is not executable"
            chmod +x "$SCRIPT_DIR/$script"
            print_success "Made $script executable"
        fi
    else
        print_error "$script NOT found"
        exit 1
    fi
done

# Test 4: Check documentation exists
print_info "Test 4: Checking documentation..."

docs=(
    "MIGRATION_README.md"
    "MIGRATION_IMPLEMENTATION_SUMMARY.md"
    "MIGRATION_QUICK_REFERENCE.md"
    "DATABASE_MIGRATION_GUIDE.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$PROJECT_ROOT/$doc" ]; then
        print_success "$doc exists"
    else
        print_warning "$doc NOT found"
    fi
done

# Test 5: Verify migration dependencies
print_info "Test 5: Checking migration dependencies..."

# Check startScan dependency
if grep -q "('startScan', '0002_auto_20240911_0145')" "$WEB_DIR/startScan/migrations/0003_add_performance_indexes.py"; then
    print_success "startScan migration dependency correct"
else
    print_warning "startScan migration dependency might be incorrect"
fi

# Check targetApp dependency
if grep -q "('targetApp', '0001_initial')" "$WEB_DIR/targetApp/migrations/0002_add_performance_indexes.py"; then
    print_success "targetApp migration dependency correct"
else
    print_warning "targetApp migration dependency might be incorrect"
fi

# Test 6: Count expected indexes
print_info "Test 6: Counting indexes in migration files..."

startscan_indexes=$(grep -c "migrations.AddIndex" "$WEB_DIR/startScan/migrations/0003_add_performance_indexes.py" || true)
targetapp_indexes=$(grep -c "migrations.AddIndex" "$WEB_DIR/targetApp/migrations/0002_add_performance_indexes.py" || true)

if [ "$startscan_indexes" -eq 15 ]; then
    print_success "startScan has 15 indexes (correct)"
else
    print_warning "startScan has $startscan_indexes indexes (expected 15)"
fi

if [ "$targetapp_indexes" -eq 3 ]; then
    print_success "targetApp has 3 indexes (correct)"
else
    print_warning "targetApp has $targetapp_indexes indexes (expected 3)"
fi

total_indexes=$((startscan_indexes + targetapp_indexes))
print_info "Total indexes: $total_indexes (expected 18)"

# Test 7: Check if Django is accessible (optional)
print_info "Test 7: Checking Django environment..."

if [ -f "$WEB_DIR/manage.py" ]; then
    print_success "Django manage.py found"
    
    # Try to check migrations (if Docker is running)
    if docker ps --format '{{.Names}}' | grep -q "reconpoint.*web"; then
        web_container=$(docker ps --format '{{.Names}}' | grep "reconpoint.*web" | head -n 1)
        print_info "Found web container: $web_container"
        
        print_info "Checking migration status..."
        if docker exec "$web_container" python manage.py showmigrations startScan 2>/dev/null | tail -5; then
            print_success "Can access Django migrations"
        else
            print_warning "Cannot access Django migrations (container might not be ready)"
        fi
    else
        print_warning "Web container not running (start with: docker-compose up -d)"
    fi
else
    print_error "Django manage.py NOT found"
    exit 1
fi

# Test 8: Verify index names
print_info "Test 8: Verifying index naming convention..."

expected_indexes=(
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

missing_indexes=0
for index in "${expected_indexes[@]}"; do
    if grep -q "$index" "$WEB_DIR/startScan/migrations/0003_add_performance_indexes.py" "$WEB_DIR/targetApp/migrations/0002_add_performance_indexes.py" 2>/dev/null; then
        : # Index found, do nothing
    else
        print_warning "Index $index not found in migration files"
        ((missing_indexes++))
    fi
done

if [ $missing_indexes -eq 0 ]; then
    print_success "All 18 expected indexes found in migration files"
else
    print_warning "$missing_indexes indexes missing from migration files"
fi

# Summary
print_header "Test Summary"

print_success "All critical tests passed!"
echo ""
print_info "Migration files are ready for deployment"
print_info "Run './scripts/migrate_database.sh' to apply migrations"
echo ""
print_warning "Recommended: Create a database backup before migration"
print_info "Backup command: docker-compose exec db pg_dump -U postgres reconpoint_db > backup.sql"
