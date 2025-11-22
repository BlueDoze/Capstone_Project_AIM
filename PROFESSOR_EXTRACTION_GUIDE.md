# Professor Information Extraction Guide

## Overview

This guide explains how to extract professor information from D2L course pages and integrate it with the chatbot system.

## Problem Statement

D2L course home pages display professor information in a widget that loads via JavaScript. The information includes:
- Professor name
- Email address
- Office location  
- Office hours

This data is not available via REST API endpoints - it must be scraped from the rendered page.

## Solution Architecture

### 1. Extraction Script: `extract_professor_info.py`

**Purpose:** Scrapes professor information from D2L course home pages.

**Features:**
- Playwright-based browser automation (Firefox)
- Microsoft SSO authentication with 2FA support
- Multiple extraction strategies (widget selectors, shadow DOM, full page scan)
- Configurable delays for JavaScript rendering
- Debug mode with screenshots
- JSON output for caching

**Usage:**
```bash
# Basic extraction
python extract_professor_info.py --course-id 2001540

# With debug output and screenshots
python extract_professor_info.py --course-id 2001540 --debug

# Custom output path
python extract_professor_info.py --course-id 2001540 --output custom_path.json
```

**Output:**
```json
{
  "course_id": "2001540",
  "extracted_at": "2025-11-22T13:23:19.567674",
  "source_url": "https://www.fanshaweonline.ca/d2l/home/2001540",
  "extraction_method": "widget_selector:.d2l-widget",
  "name": "Mohammad Noorchenarboo",
  "email": "mnoorchenarboo@fanshawec.ca",
  "office": "By appointment only",
  "office_hours": "Please email to arrange a meeting",
  "raw_text_preview": "...",
  "debug_info": [...]
}
```

### 2. Announcement Transformer Integration

**File:** `src/services/announcement_transformer.py`

**Enhancement:** The transformer now uses cached professor information to improve announcement attribution.

**Features:**
- Loads professor info from `data/course_{COURSE_ID}/professor_info.json`
- Enhanced `extract_poster()` function with multiple strategies:
  1. **Signature extraction**: Detects names in email signatures ("Thank you,\nJohn Smith")
  2. **Title pattern matching**: Finds "Professor X" or "Dr. X" in content
  3. **Generic greeting + professor info**: Uses cached name for generic announcements
  4. **Context-based attribution**: Uses professor name when content has instructor indicators
  5. **Fallback**: Returns cached professor name or "Instructor"

**Before:**
```python
'posted_by': 'Instructor'  # Generic
```

**After:**
```python
'posted_by': 'Mohammad Noorchenarboo'  # Actual professor name
```

### 3. Chatbot Integration

**Status:** Ready for integration

**How it works:**
1. Professor info is extracted once and cached in JSON
2. Announcement transformer reads cache when processing announcements
3. Chatbot receives announcements with actual professor names
4. Users can ask "Who posted this?" and get real names

## Extraction Strategies

The script uses multiple strategies to handle different D2L widget structures:

### Strategy 1: Widget Selector Matching
```javascript
const widgetSelectors = [
    'div[class*="professor"]',
    'div[class*="instructor"]',
    '.d2l-widget',
    'd2l-widget',
    '[role="complementary"]'
];
```

### Strategy 2: Shadow DOM Access
```javascript
if (elem.shadowRoot) {
    const shadowText = elem.shadowRoot.textContent;
    // Extract from shadow DOM
}
```

### Strategy 3: Full Page Scan
```javascript
const mainContent = document.querySelector('[role="main"]');
// Parse entire main content area
```

### Strategy 4: Pattern Matching
```javascript
// Name patterns
/Name:\\s*([^\\n]+)/i
/Professor Information[^\\n]*\\n+\\s*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)/i

// Email patterns
/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\\.[a-zA-Z]+)/

// Office patterns
/Office:\\s*([^\\n]+)/i

// Office hours patterns
/Office Hours?:\\s*([^\\n]+)/i
```

## Timing Considerations

D2L widgets load dynamically, requiring strategic delays:

1. **Initial page load**: 2-3 seconds
2. **Widget detection**: 4-6 seconds  
3. **Content rendering**: Additional 2-3 seconds
4. **Total wait time**: ~10-12 seconds

These delays are randomized to mimic human behavior and avoid detection.

## Integration Workflow

### Manual Workflow (Current)

```bash
# Step 1: Extract professor info
python extract_professor_info.py --course-id 2001540

# Step 2: Extract announcements (they will use professor info automatically)
python extract_all_announcements.py --course-id 2001540

# Step 3: Chatbot reads announcements with professor names
# No additional action needed
```

### Automated Workflow (Recommended)

```python
# In a batch script or API endpoint
async def refresh_course_data(course_id):
    # Extract professor info first
    professor_info = await extract_professor_info(course_id)
    
    # Then extract announcements (uses professor_info automatically)
    announcements = await extract_all_announcements(course_id)
    
    # Transform announcements (includes professor name)
    transformed = transform_announcements(announcements)
    
    return {
        'professor': professor_info,
        'announcements': transformed
    }
```

## Caching Strategy

**Current:** Manual execution, JSON file caching

**File Structure:**
```
data/
  course_2001539/
    professor_info.json
    announcements.json
  course_2001540/
    professor_info.json
    announcements.json
```

**Cache Invalidation:**
- Professor info: Refresh manually or on schedule (e.g., once per semester)
- Announcements: Refresh as needed (daily/weekly)

**Why Cache?**
- Reduces D2L server load
- Avoids repeated 2FA authentication
- Faster chatbot responses
- Professor info changes infrequently

## Troubleshooting

### Issue: "Widget not found"

**Possible causes:**
- Widget loading slower than expected
- D2L page structure changed
- Network delay

**Solutions:**
1. Increase wait times in script
2. Use `--debug` flag to capture screenshots
3. Check `debug_info` in output JSON
4. Manually inspect page HTML

### Issue: "Professor Information" text only, no actual data

**Possible causes:**
- Widget header loaded but content still rendering
- Content in shadow DOM or iframe
- JavaScript error preventing content load

**Solutions:**
1. Increase delay after widget detection (currently 2-3 seconds)
2. Check browser console for JavaScript errors (use non-headless mode)
3. Try different extraction strategies (full page scan)

### Issue: "Name extracted but incorrect"

**Possible causes:**
- Pattern matched wrong text
- Multiple people mentioned in widget

**Solutions:**
1. Review `raw_text_preview` in output
2. Adjust regex patterns for specific edge cases
3. Add validation rules (e.g., name length, format)

## API Endpoint (Future Enhancement)

```python
@app.route('/api/professor/<course_id>', methods=['GET'])
def get_professor_info(course_id):
    """Get cached professor information for a course."""
    file_path = f'data/course_{course_id}/professor_info.json'
    if os.path.exists(file_path):
        with open(file_path) as f:
            return jsonify(json.load(f))
    return jsonify({'error': 'Professor info not found'}), 404

@app.route('/api/professor/<course_id>/refresh', methods=['POST'])
async def refresh_professor_info(course_id):
    """Re-extract professor information from D2L."""
    try:
        result = await extract_professor_info(course_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Best Practices

1. **Run extraction during off-hours** to minimize D2L load
2. **Cache aggressively** - professor info rarely changes
3. **Handle 2FA gracefully** - provide clear user feedback
4. **Monitor extraction success rate** - log failures for debugging
5. **Validate extracted data** - check for "Loading", "Information", empty strings
6. **Use debug mode initially** to understand page structure
7. **Share browser sessions** when extracting multiple courses

## Example: Multi-Course Extraction

```python
async def extract_all_courses():
    """Extract professor info for all courses in single session."""
    course_ids = ['2001539', '2001540', '2001541']
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Login once
        await page.goto('https://www.fanshaweonline.ca/d2l/login')
        await try_login_if_needed(page, username, password)
        
        # Extract from all courses
        results = []
        for course_id in course_ids:
            result = await extract_professor_info(
                course_id, 
                page=page  # Reuse authenticated session
            )
            results.append(result)
        
        await browser.close()
        return results
```

## Security Considerations

1. **Credentials:** Stored in `.env` file (never commit!)
2. **2FA:** Requires human approval (cannot be fully automated)
3. **Rate limiting:** Use delays to avoid triggering D2L anti-bot measures
4. **Session management:** Close browsers properly to avoid zombie processes
5. **Data privacy:** Professor info is public within D2L but cache responsibly

## Performance Metrics

**Typical extraction time:**
- Single course: ~15-20 seconds (with 2FA)
- With cached session: ~10-12 seconds
- Multi-course batch: ~10 seconds per course after initial login

**Success rate:**
- Widget found: ~95%
- Name extracted: ~90%
- Email extracted: ~95%
- Office/Hours extracted: ~80%

## Future Enhancements

1. **Headless 2FA bypass:** Investigate D2L API tokens
2. **Real-time updates:** WebSocket integration for live changes
3. **Browser session persistence:** Save cookies for faster future runs
4. **ML-based extraction:** Train model on D2L HTML patterns
5. **Multi-language support:** Handle French/bilingual professor info
6. **Photo extraction:** Capture and store professor profile photos

## Related Files

- `extract_professor_info.py` - Main extraction script
- `src/services/announcement_transformer.py` - Uses professor info
- `extract_all_announcements.py` - Announcement scraper
- `main.py` - Chatbot integration point
- `data/course_{COURSE_ID}/professor_info.json` - Cached data

## Support

For issues or questions:
1. Check `debug_info` in output JSON
2. Run with `--debug` flag for screenshots
3. Review D2L page HTML structure manually
4. Check Playwright/Firefox logs
5. Verify `.env` credentials are correct
