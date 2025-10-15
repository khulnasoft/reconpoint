#!/bin/bash
# reconPoint Enhancements - Quick Test Script
# Run this after Docker services start

echo "🚀 Testing reconPoint Enhancements..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3
    
    echo -n "Testing $name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response" -eq "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $response)"
    else
        echo -e "${RED}❌ FAIL${NC} (Expected $expected_code, got $response)"
    fi
}

# Function to test with JSON response
test_json_endpoint() {
    local name=$1
    local url=$2
    
    echo "Testing $name..."
    response=$(curl -s "$url")
    
    if echo "$response" | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC} - Valid JSON response"
        echo "$response" | jq '.' | head -20
    else
        echo -e "${RED}❌ FAIL${NC} - Invalid JSON response"
        echo "$response"
    fi
    echo ""
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 HEALTH & MONITORING TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_json_endpoint "Health Check" "$BASE_URL/health/"
test_json_endpoint "Metrics" "$BASE_URL/metrics/"
test_endpoint "Liveness Probe" "$BASE_URL/liveness/" 200
test_endpoint "Readiness Probe" "$BASE_URL/readiness/" 200

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔒 SECURITY HEADERS TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking security headers..."
headers=$(curl -sI "$BASE_URL/health/")

check_header() {
    local header=$1
    if echo "$headers" | grep -qi "$header"; then
        echo -e "${GREEN}✅${NC} $header present"
    else
        echo -e "${RED}❌${NC} $header missing"
    fi
}

check_header "X-Content-Type-Options"
check_header "X-Frame-Options"
check_header "X-XSS-Protection"
check_header "Content-Security-Policy"
check_header "Strict-Transport-Security"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚡ RATE LIMITING TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Sending 70 requests to test rate limiting..."
success_count=0
rate_limited_count=0

for i in {1..70}; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/scans/" 2>/dev/null)
    
    if [ "$response" -eq "429" ]; then
        ((rate_limited_count++))
    elif [ "$response" -eq "200" ] || [ "$response" -eq "401" ]; then
        ((success_count++))
    fi
    
    # Show progress every 10 requests
    if [ $((i % 10)) -eq 0 ]; then
        echo "  Progress: $i/70 requests sent..."
    fi
done

echo ""
echo "Results:"
echo "  - Successful requests: $success_count"
echo "  - Rate limited (429): $rate_limited_count"

if [ "$rate_limited_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Rate limiting is working!${NC}"
else
    echo -e "${YELLOW}⚠️  Rate limiting may not be active${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 API VERSIONING TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_endpoint "API v1" "$BASE_URL/api/v1/scans/" 200
test_endpoint "API v2" "$BASE_URL/api/v2/scans/" 200

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 DATA EXPORT TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_endpoint "JSON Export" "$BASE_URL/api/export/subdomains/?format=json" 200
test_endpoint "CSV Export" "$BASE_URL/api/export/subdomains/?format=csv" 200
test_endpoint "XML Export" "$BASE_URL/api/export/subdomains/?format=xml" 200

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "All basic tests completed!"
echo ""
echo "Next steps:"
echo "  1. Review the detailed results above"
echo "  2. Check TESTING_CHECKLIST.md for comprehensive tests"
echo "  3. Review application logs: docker-compose logs -f web"
echo "  4. Access web interface: http://localhost:8000"
echo ""
