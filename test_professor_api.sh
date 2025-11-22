#!/bin/bash

# Test Professor Info API Endpoints
# This script tests the new professor information API endpoints

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         TESTING PROFESSOR INFO API ENDPOINTS                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

BASE_URL="http://localhost:5000"

echo "1️⃣  Testing GET /api/professor/2001540"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$BASE_URL/api/professor/2001540" | python3 -m json.tool
echo ""

echo ""
echo "2️⃣  Testing GET /api/professor/status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$BASE_URL/api/professor/status" | python3 -m json.tool
echo ""

echo ""
echo "3️⃣  Testing GET /api/professor/999999 (non-existent course)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$BASE_URL/api/professor/999999" | python3 -m json.tool
echo ""

echo ""
echo "✅ API tests completed!"
echo ""
