#!/bin/bash
# Script to start a simple HTTP server for route visualization

echo "🌐 Starting local server for route visualization..."
echo ""
echo "📂 Server directory: tools/"
echo ""
echo "🔗 Open in your browser:"
echo "   http://localhost:8000/visualize_routes.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python3 -m http.server 8000
