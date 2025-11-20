#!/bin/bash
# Quick command to open the route viewer in default browser

VIEWER="tools/route_viewer_standalone.html"

echo "🗺️  Opening Route Viewer..."
echo ""

if [ -f "$VIEWER" ]; then
    # Try to open with xdg-open (Linux)
    if command -v xdg-open > /dev/null; then
        xdg-open "$VIEWER"
        echo "✅ Opened in browser!"
    # Try gnome-open
    elif command -v gnome-open > /dev/null; then
        gnome-open "$VIEWER"
        echo "✅ Opened in browser!"
    # Try firefox directly
    elif command -v firefox > /dev/null; then
        firefox "$VIEWER" &
        echo "✅ Opened in Firefox!"
    # Try google-chrome
    elif command -v google-chrome > /dev/null; then
        google-chrome "$VIEWER" &
        echo "✅ Opened in Chrome!"
    else
        echo "⚠️  Could not auto-open browser."
        echo ""
        echo "Please open this file manually:"
        echo "   file://$(pwd)/$VIEWER"
    fi
else
    echo "❌ Error: $VIEWER not found"
    echo ""
    echo "Run this first:"
    echo "   python3 generate_route_viewer.py"
fi
