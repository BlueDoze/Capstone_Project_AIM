#!/bin/bash
# Quick test script for BUILDING_INFO intent

echo "🧪 Running BUILDING_INFO Intent Tests"
echo "======================================"
echo ""

# Activate virtual environment
source .venv/bin/activate

echo "1️⃣  Testing Intent Classification & Handler..."
python test_building_info.py

echo ""
echo "2️⃣  Testing Intent Distinction (NAVIGATION vs BUILDING_INFO)..."
python test_intent_distinction.py

echo ""
echo "✅ All tests completed!"
echo ""
echo "To test the API endpoint:"
echo "1. Start the server: ./devserver.sh"
echo "2. Run: python test_building_info_api.py"
