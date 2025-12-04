# Career Services Integration - Implementation Guide

## Overview

The Career Services integration adds a new intent category (`CAREER_SERVICES`) to the Fanshawe Navigator chatbot, enabling users to get information about career development resources, job search support, and professional development opportunities.

## Implementation Summary

### Date Implemented
December 4, 2025

### Components Added

1. **Data File**: `data/career_services.json`
   - Structured career services information
   - Links to Career Services portal (course 906769)
   - Resource categories: mentorship, workshops, events
   - Service descriptions and contact information

2. **Intent Classification**: Updated `classify_user_intent()` in `src/api/app.py`
   - New `CAREER_SERVICES` intent category
   - Keywords: career, job, resume, cv, interview, co-op, internship, mentorship, etc.
   - Hybrid classification: keyword matching + Gemini AI

3. **Handler Function**: `handle_career_services_query()` in `src/api/app.py`
   - Loads data from `career_services.json`
   - Formats context with resources and links
   - Generates AI-powered responses using Gemini
   - Returns formatted HTML with clickable links

4. **Routing**: Added to both `/chat` and `/api/chat` endpoints
   - Routes `CAREER_SERVICES` intent to handler
   - Integrated alongside NAVIGATION, EVENTS, RESTAURANTS, ANNOUNCEMENTS

5. **System Prompt**: `career_services_prompt` in `src/api/app.py`
   - Guides AI responses for career-related queries
   - Emphasizes providing direct links and actionable advice

## Files Modified

### `src/api/app.py`
- Added `career_services_prompt` (lines ~235-260)
- Added career keywords to `classify_user_intent()` (lines ~718-722)
- Updated keyword scoring logic (lines ~730-732)
- Added `CAREER_SERVICES` to keyword matching (lines ~740-742)
- Updated Gemini classification prompt (lines ~747-753)
- Created `handle_career_services_query()` function (lines ~945-1020)
- Updated fallback message (lines ~1027-1030)
- Added routing in `/api/chat` endpoint (lines ~1196-1199)
- Added routing in `/chat` endpoint (lines ~1384-1387)

### Files Created
- `data/career_services.json` - Career services data structure
- `test_career_services.py` - Test script for validation

## Data Structure

### `data/career_services.json`

```json
{
  "service_name": "Fanshawe Career Services",
  "description": "Comprehensive career development support...",
  "main_portal": {
    "name": "Career Services Online Resources",
    "url": "https://www.fanshaweonline.ca/d2l/home/906769",
    "description": "Access all Career Services resources..."
  },
  "resources": [
    {
      "name": "Industry Mentorship Opportunities",
      "url": "...",
      "category": "mentorship",
      "description": "..."
    }
  ],
  "topics": {
    "resume_help": {...},
    "interview_prep": {...},
    "job_search": {...}
  }
}
```

## Usage Examples

### User Queries
- "How can I get help with my resume?"
- "I need career counseling"
- "Where can I find co-op opportunities?"
- "Tell me about career services"
- "I need help with job interviews"

### System Response
The chatbot will:
1. Detect `CAREER_SERVICES` intent
2. Load career services data
3. Generate contextualized response with:
   - Direct link to Career Services portal
   - Relevant resource links
   - Description of available services
   - Actionable next steps

## Testing

### Run Test Script
```bash
# Start the server
python3 src/api/app.py

# In another terminal, run tests
python3 test_career_services.py
```

### Manual Testing
```bash
# Test via curl
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need help with my resume"}'
```

## Integration Points

### With Existing System
- Follows same pattern as EVENTS, RESTAURANTS, ANNOUNCEMENTS handlers
- Uses existing Gemini AI model for response generation
- Integrates with both React frontend (`/api/chat`) and original interface (`/chat`)
- Respects existing error handling and logging patterns

### Fallback Behavior
- Updated out-of-scope message includes Career Services
- If data file missing, provides fallback URL: www.fanshawec.ca/student-life-services/career-services

## Architecture Flow

```
User Query: "I need career help"
    ↓
classify_user_intent()
    ↓
Intent: CAREER_SERVICES (confidence: 0.8)
    ↓
handle_career_services_query()
    ↓
Load: data/career_services.json
    ↓
Format: career_context (portal + resources + topics)
    ↓
Gemini AI: Generate response with career_services_prompt
    ↓
Return: Formatted response with links
```

## Maintenance

### Updating Career Services Data
1. Edit `data/career_services.json`
2. No code changes needed
3. Server restart not required (loads on each request)

### Adding New Resources
```json
{
  "name": "New Resource Name",
  "url": "https://...",
  "category": "events|workshops|mentorship",
  "description": "What this resource offers"
}
```

### Adding New Topics
```json
"new_topic": {
  "keywords": ["keyword1", "keyword2"],
  "response": "Description of this service"
}
```

## Future Enhancements

1. **Automated Updates**: Create scraper to auto-update from course_906769
2. **Event Integration**: Link Career Services events to campus_events.json
3. **Appointment Booking**: Add ability to book career counseling appointments
4. **Resource Tracking**: Track which resources users access most
5. **Personalization**: Tailor responses based on user's program/year

## Source Data

Career Services data extracted from:
- **D2L Course**: 906769 (Career Services Online Resources)
- **Main Portal**: https://www.fanshaweonline.ca/d2l/home/906769
- **Extracted**: December 3, 2025

## Support

For issues or questions:
- Check logs: Look for "💼 Career Services query handled" messages
- Verify data file: Ensure `data/career_services.json` exists and is valid JSON
- Test endpoint: Use `test_career_services.py` script
- Fallback URL: www.fanshawec.ca/student-life-services/career-services

---

**Status**: ✅ Fully Implemented and Tested
**Version**: 1.0
**Last Updated**: December 4, 2025
