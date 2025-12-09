#!/bin/bash
# Script to run the D2L Announcements pipeline
# This script extracts announcements from D2L and saves them to src/data/announcements/

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    D2L ANNOUNCEMENTS PIPELINE                                ║"
echo "║                  Fanshawe Navigator - Capstone Project                       ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "📦 Activating .venv..."
    source .venv/bin/activate
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please create a .env file with your D2L credentials:"
    echo ""
    echo "   D2L_USERNAME=your_email@fanshaweonline.ca"
    echo "   D2L_PASSWORD=your_password"
    echo ""
    exit 1
fi

# Check if Playwright browsers are installed
if ! python -c "import playwright" &> /dev/null; then
    echo "❌ Error: Playwright not installed!"
    echo "📦 Install it with: pip install playwright"
    exit 1
fi

echo "✓ Virtual environment: Active"
echo "✓ Environment file: Found"
echo "✓ Playwright: Installed"
echo ""

echo "🚀 Starting D2L Announcements Scraper..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the announcements scraper
python -m src.scrapers.d2l.announcements

# Check if the output file was created
OUTPUT_FILE="src/data/announcements/all_announcements.json"

if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Pipeline completed successfully!"
    echo "📄 Output saved to: $OUTPUT_FILE"
    echo ""
    
    # Display summary
    TOTAL=$(python -c "import json; data=json.load(open('$OUTPUT_FILE')); print(data.get('total_announcements', 0))")
    COURSE=$(python -c "import json; data=json.load(open('$OUTPUT_FILE')); print(data.get('course', 'Unknown'))")
    
    echo "📊 Summary:"
    echo "   Course: $COURSE"
    echo "   Total Announcements: $TOTAL"
    echo ""
    echo "💬 The chatbot can now access these announcements!"
    echo "   Ask: 'What are the recent announcements?' or 'Show me D2L updates'"
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Pipeline failed!"
    echo "📄 Output file not created: $OUTPUT_FILE"
    exit 1
fi
