#!/bin/bash
# Test API integration with AI-only intent classification

echo "========================================"
echo "API INTEGRATION TEST (Phase 1)"
echo "========================================"
echo ""

API_URL="http://localhost:5000/api/chat"

# Test 1: Navigation query
echo "Test 1: Navigation Query"
echo "Query: 'How do I get to room 1003?'"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "How do I get to room 1003?"}' | jq -r '.reply' | head -n 3
echo ""
echo "----------------------------------------"
echo ""

# Test 2: Restaurant query (previously misclassified)
echo "Test 2: Restaurant Query (FIXED!)"
echo "Query: 'I'm hungry, where should I go?'"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "I'\''m hungry, where should I go?"}' | jq -r '.reply' | head -n 3
echo ""
echo "----------------------------------------"
echo ""

# Test 3: Event query
echo "Test 3: Event Query"
echo "Query: 'What events are happening this week?'"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "What events are happening this week?"}' | jq -r '.reply' | head -n 3
echo ""
echo "----------------------------------------"
echo ""

# Test 4: Out of scope query
echo "Test 4: Out of Scope Query"
echo "Query: 'What'\''s the weather today?'"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "What'\''s the weather today?"}' | jq -r '.reply' | head -n 3
echo ""
echo "----------------------------------------"
echo ""

echo "✅ Integration test complete!"
echo ""
echo "NOTE: Make sure the Flask server is running:"
echo "  source .venv/bin/activate && python3 src/api/app.py"
