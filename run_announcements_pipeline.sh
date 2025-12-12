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

echo "🚀 Starting D2L Multi-Course Announcements Scraper..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the multi-course announcements scraper
python -m src.scrapers.d2l.announcements_multi_course

# Check if the output file was created
OUTPUT_FILE="src/data/announcements/all_courses_announcements.json"

if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Pipeline completed successfully!"
    echo "📄 Output saved to: $OUTPUT_FILE"
    echo ""
    
    # Display summary
    TOTAL_COURSES=$(python -c "import json; data=json.load(open('$OUTPUT_FILE')); print(len(data))")
    TOTAL_ANNOUNCEMENTS=$(python -c "import json; data=json.load(open('$OUTPUT_FILE')); print(sum(c.get('total_announcements', 0) for c in data))")
    
    echo "📊 Summary:"
    echo "   Total Courses: $TOTAL_COURSES"
    echo "   Total Announcements: $TOTAL_ANNOUNCEMENTS"
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
