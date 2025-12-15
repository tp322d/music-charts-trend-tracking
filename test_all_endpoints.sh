#!/bin/bash
# Comprehensive API Endpoint Testing Script

API_URL="http://localhost:8000"
API_V1="${API_URL}/api/v1"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
SKIPPED=0

echo "🧪 Testing All 18 API Endpoints"
echo "=================================="
echo ""

# Helper functions
test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    local expected_status=$5
    local requires_auth=${6:-false}
    
    echo -n "Testing: $name ... "
    
    if [ "$requires_auth" = true ] && [ -z "$ACCESS_TOKEN" ]; then
        echo -e "${YELLOW}SKIPPED (no auth)${NC}"
        SKIPPED=$((SKIPPED + 1))
        return
    fi
    
    if [ "$requires_auth" = true ]; then
        headers=(-H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json")
    else
        headers=(-H "Content-Type: application/json")
    fi
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" "${headers[@]}")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$url" "${headers[@]}")
    elif [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -w "\n%{http_code}" -X POST "$url" "${headers[@]}" -d "$data")
        else
            response=$(curl -s -w "\n%{http_code}" -X POST "$url" "${headers[@]}")
        fi
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT "$url" "${headers[@]}" -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ] || [ "$http_code" = "200" ] || [ "$http_code" = "201" ] || [ "$http_code" = "204" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "  Response: $(echo "$body" | head -c 200)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test 1: Root endpoint
test_endpoint "GET /" "GET" "${API_URL}/" "" "200" false

# Test 2: Health check
test_endpoint "GET /health" "GET" "${API_URL}/health" "" "200" false

echo ""
echo "--- Authentication Endpoints ---"

# Test 3: Register user
REGISTER_DATA='{"username":"testuser_'$(date +%s)'","email":"test'$(date +%s)'@example.com","password":"testpass123","role":"viewer"}'
REGISTER_RESPONSE=$(curl -s -X POST "${API_V1}/auth/register" -H "Content-Type: application/json" -d "$REGISTER_DATA")
if echo "$REGISTER_RESPONSE" | grep -q "username"; then
    echo -e "Testing: POST /auth/register ... ${GREEN}✓ PASSED${NC}"
    PASSED=$((PASSED + 1))
    USERNAME=$(echo "$REGISTER_RESPONSE" | grep -o '"username":"[^"]*' | cut -d'"' -f4)
else
    echo -e "Testing: POST /auth/register ... ${RED}✗ FAILED${NC}"
    FAILED=$((FAILED + 1))
    echo "  Response: $REGISTER_RESPONSE"
    USERNAME="testuser"
fi

# Test 4: Login
LOGIN_DATA='{"username":"'$USERNAME'","password":"testpass123"}'
LOGIN_RESPONSE=$(curl -s -X POST "${API_V1}/auth/token" -H "Content-Type: application/json" -d "$LOGIN_DATA")
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "Testing: POST /auth/token ... ${GREEN}✓ PASSED${NC}"
    PASSED=$((PASSED + 1))
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)
else
    echo -e "Testing: POST /auth/token ... ${RED}✗ FAILED${NC}"
    FAILED=$((FAILED + 1))
    echo "  Response: $LOGIN_RESPONSE"
    ACCESS_TOKEN=""
fi

# Test 5: Get current user (requires auth)
test_endpoint "GET /auth/me" "GET" "${API_V1}/auth/me" "" "200" true

# Test 6: Refresh token
if [ -n "$REFRESH_TOKEN" ]; then
    REFRESH_DATA="{\"refresh_token\":\"$REFRESH_TOKEN\"}"
    test_endpoint "POST /auth/refresh" "POST" "${API_V1}/auth/refresh" "$REFRESH_DATA" "200" false
fi

echo ""
echo "--- Chart Endpoints ---"

# Test 7: Create chart entry (requires Editor/Admin - will need to create admin user)
# First create an admin user
ADMIN_REGISTER='{"username":"admin_'$(date +%s)'","email":"admin'$(date +%s)'@example.com","password":"admin12345","role":"admin"}'
ADMIN_RESPONSE=$(curl -s -X POST "${API_V1}/auth/register" -H "Content-Type: application/json" -d "$ADMIN_REGISTER")
if echo "$ADMIN_RESPONSE" | grep -q "username"; then
    ADMIN_USERNAME=$(echo "$ADMIN_RESPONSE" | grep -o '"username":"[^"]*' | cut -d'"' -f4)
    ADMIN_LOGIN='{"username":"'$ADMIN_USERNAME'","password":"admin12345"}'
    ADMIN_TOKEN_RESPONSE=$(curl -s -X POST "${API_V1}/auth/token" -H "Content-Type: application/json" -d "$ADMIN_LOGIN")
    if echo "$ADMIN_TOKEN_RESPONSE" | grep -q "access_token"; then
        ADMIN_TOKEN=$(echo "$ADMIN_TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        ACCESS_TOKEN="$ADMIN_TOKEN"  # Use admin token for chart operations
    fi
fi

# Create a test chart entry
CHART_ENTRY='{"date":"2024-01-15","rank":1,"song":"Test Song","artist":"Test Artist","source":"Spotify","country":"US","streams":1000000}'
CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_V1}/charts" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$CHART_ENTRY")

HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "201" ]; then
    echo -e "Testing: POST /charts ... ${GREEN}✓ PASSED${NC} (HTTP $HTTP_CODE)"
    PASSED=$((PASSED + 1))
    ENTRY_ID=$(echo "$CREATE_RESPONSE" | sed '$d' | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
else
    echo -e "Testing: POST /charts ... ${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    FAILED=$((FAILED + 1))
    ENTRY_ID=""
fi

# Test 8: Get charts
test_endpoint "GET /charts" "GET" "${API_V1}/charts?limit=10" "" "200" true

# Test 9: Get top charts
test_endpoint "GET /charts/top" "GET" "${API_V1}/charts/top?date=2024-01-15&limit=10" "" "200" true

# Test 10: Get artist history
test_endpoint "GET /charts/artist/{name}" "GET" "${API_V1}/charts/artist/Test%20Artist" "" "200" true

# Test 11: Get specific entry
if [ -n "$ENTRY_ID" ]; then
    test_endpoint "GET /charts/{id}" "GET" "${API_V1}/charts/$ENTRY_ID" "" "200" true
fi

# Test 12: Update entry
if [ -n "$ENTRY_ID" ]; then
    UPDATE_DATA='{"rank":2,"streams":1500000}'
    test_endpoint "PUT /charts/{id}" "PUT" "${API_V1}/charts/$ENTRY_ID" "$UPDATE_DATA" "200" true
fi

# Test 13: Batch create (will skip if no data)
BATCH_DATA='{"entries":[{"date":"2024-01-16","rank":1,"song":"Song 1","artist":"Artist 1","source":"Spotify","country":"US"},{"date":"2024-01-16","rank":2,"song":"Song 2","artist":"Artist 2","source":"Spotify","country":"US"}],"validate_duplicates":false}'
test_endpoint "POST /charts/batch" "POST" "${API_V1}/charts/batch" "$BATCH_DATA" "201" true

echo ""
echo "--- Trend Endpoints ---"

# Test 14: Top artists
test_endpoint "GET /trends/top-artists" "GET" "${API_V1}/trends/top-artists?days=30" "" "200" true

# Test 15: Rising songs
test_endpoint "GET /trends/rising" "GET" "${API_V1}/trends/rising?period=7" "" "200" true

# Test 16: Comparison (requires dimension parameter)
test_endpoint "GET /trends/comparison" "GET" "${API_V1}/trends/comparison?dimension=source" "" "200" true

echo ""
echo "--- Data Sync Endpoints (may fail without API keys) ---"

# Test 17: Fetch iTunes (requires Editor/Admin)
test_endpoint "POST /sync/fetch/itunes" "POST" "${API_V1}/sync/fetch/itunes?country=us&limit=10" "" "201" true

# Test 18: Delete entry (requires Admin, cleanup)
if [ -n "$ENTRY_ID" ]; then
    DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "${API_V1}/charts/$ENTRY_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    DELETE_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)
    if [ "$DELETE_CODE" = "204" ]; then
        echo -e "Testing: DELETE /charts/{id} ... ${GREEN}✓ PASSED${NC} (HTTP $DELETE_CODE)"
        PASSED=$((PASSED + 1))
    else
        echo -e "Testing: DELETE /charts/{id} ... ${RED}✗ FAILED${NC} (HTTP $DELETE_CODE)"
        FAILED=$((FAILED + 1))
    fi
fi

# Summary
echo ""
echo "=================================="
echo "📊 Test Summary"
echo "=================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Skipped: $SKIPPED${NC}"
echo "Total: $((PASSED + FAILED + SKIPPED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

