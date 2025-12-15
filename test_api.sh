#!/bin/bash
# Quick API Test Script

API_URL="http://localhost:8000"
USERNAME="admin"
PASSWORD="admin123"

echo "🧪 Testing Music Charts API"
echo "============================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Health Check
echo "1. Testing health endpoint..."
if curl -s "$API_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

# Test 2: Register User
echo ""
echo "2. Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"email\":\"${USERNAME}@example.com\",\"password\":\"$PASSWORD\",\"role\":\"admin\"}")

if echo "$REGISTER_RESPONSE" | grep -q "username"; then
    echo -e "${GREEN}✅ User registered${NC}"
elif echo "$REGISTER_RESPONSE" | grep -q "already registered"; then
    echo -e "${YELLOW}⚠️  User already exists (this is OK)${NC}"
else
    echo -e "${RED}❌ Registration failed: $REGISTER_RESPONSE${NC}"
    exit 1
fi

# Test 3: Login
echo ""
echo "3. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Login failed: $LOGIN_RESPONSE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Login successful${NC}"
echo "   Token: ${TOKEN:0:50}..."

# Test 4: Fetch Charts
echo ""
echo "4. Fetching charts..."
CHARTS_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/charts?limit=5" \
  -H "Authorization: Bearer $TOKEN")

if echo "$CHARTS_RESPONSE" | grep -q "\["; then
    echo -e "${GREEN}✅ Charts endpoint working${NC}"
    CHART_COUNT=$(echo "$CHARTS_RESPONSE" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "   Found $CHART_COUNT charts"
else
    echo -e "${YELLOW}⚠️  No charts found (this is OK if no data imported yet)${NC}"
fi

# Test 5: Fetch Real Data (iTunes)
echo ""
echo "5. Fetching real data from iTunes..."
SYNC_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/sync/fetch/itunes?country=us&limit=10" \
  -H "Authorization: Bearer $TOKEN")

if echo "$SYNC_RESPONSE" | grep -q "fetched"; then
    echo -e "${GREEN}✅ Data sync successful${NC}"
    IMPORTED=$(echo "$SYNC_RESPONSE" | grep -o '"imported":[0-9]*' | cut -d':' -f2)
    echo "   Imported: $IMPORTED entries"
else
    echo -e "${YELLOW}⚠️  Sync response: $SYNC_RESPONSE${NC}"
fi

echo ""
echo -e "${GREEN}✅ All tests completed!${NC}"
echo ""
echo "🌐 Access the API documentation at: $API_URL/docs"
echo "📊 Access the dashboard at: http://localhost:8501"

