#!/bin/bash

###############################################################################
# Implementation Script for COMPREHENSIVE_GUIDE.md
# Implements database migration and key enhancements
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

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_header "reconPoint Implementation - COMPREHENSIVE_GUIDE.md"

echo "This script will implement the database migration and enhancements."
echo ""
print_warning "Prerequisites:"
echo "  - Docker and Docker Compose installed"
echo "  - Sufficient disk space (~20% free)"
echo "  - Backup recommended for production"
echo ""

read -p "Do you want to proceed? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    print_error "Implementation cancelled"
    exit 0
fi

# Step 1: Check Docker
print_header "Step 1: Checking Docker"

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi
print_success "Docker is installed"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi
print_success "Docker Compose is installed"

# Step 2: Start Services
print_header "Step 2: Starting Docker Services"

cd "$PROJECT_ROOT"

print_info "Starting services..."
docker-compose up -d

sleep 5

print_info "Checking service status..."
docker-compose ps

# Wait for database to be ready
print_info "Waiting for database to be ready..."
for i in {1..30}; do
    if docker-compose exec -T db pg_isready -U postgres &> /dev/null; then
        print_success "Database is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Database failed to start"
        exit 1
    fi
    sleep 2
done

# Step 3: Validate Migration Files
print_header "Step 3: Validating Migration Files"

if [ -f "$SCRIPT_DIR/test_migrations.sh" ]; then
    print_info "Running migration tests..."
    bash "$SCRIPT_DIR/test_migrations.sh"
else
    print_warning "test_migrations.sh not found, skipping validation"
fi

# Step 4: Run Database Migration
print_header "Step 4: Running Database Migration"

if [ -f "$SCRIPT_DIR/migrate_database.sh" ]; then
    print_info "Running automated migration..."
    bash "$SCRIPT_DIR/migrate_database.sh"
else
    print_warning "migrate_database.sh not found"
    print_info "Running manual migration..."
    
    # Manual migration
    docker-compose exec web python manage.py migrate startScan
    docker-compose exec web python manage.py migrate targetApp
    
    print_success "Manual migration completed"
fi

# Step 5: Verify Installation
print_header "Step 5: Verifying Installation"

if [ -f "$SCRIPT_DIR/verify_indexes.sh" ]; then
    print_info "Verifying indexes..."
    bash "$SCRIPT_DIR/verify_indexes.sh"
else
    print_warning "verify_indexes.sh not found"
    
    # Manual verification
    print_info "Checking migrations..."
    docker-compose exec web python manage.py showmigrations
fi

# Step 6: Performance Benchmark (Optional)
print_header "Step 6: Performance Benchmark (Optional)"

read -p "Do you want to run performance benchmarks? (yes/no): " run_benchmark
if [ "$run_benchmark" = "yes" ]; then
    if [ -f "$SCRIPT_DIR/benchmark_performance.py" ]; then
        print_info "Running performance benchmarks..."
        python3 "$SCRIPT_DIR/benchmark_performance.py"
    else
        print_warning "benchmark_performance.py not found"
    fi
else
    print_info "Skipping performance benchmarks"
fi

# Step 7: Health Check
print_header "Step 7: Health Check"

print_info "Checking application health..."

# Try to access the application
if curl -f http://localhost:8000 &> /dev/null; then
    print_success "Application is accessible at http://localhost:8000"
else
    print_warning "Application may not be fully started yet"
    print_info "Check logs with: docker-compose logs -f web"
fi

# Final Summary
print_header "Implementation Complete"

print_success "Database migration completed successfully!"
echo ""
print_info "Next steps:"
echo "  1. Access application: http://localhost:8000"
echo "  2. Check logs: docker-compose logs -f web"
echo "  3. Monitor performance over the next week"
echo "  4. Review IMPLEMENTATION_PLAN.md for post-implementation tasks"
echo ""
print_info "Rollback available if needed:"
echo "  - Quick: ./scripts/rollback_indexes.sh"
echo "  - Full: Restore from backup"
echo ""
print_success "Implementation successful! 🎉"
