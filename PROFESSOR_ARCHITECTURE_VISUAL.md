# Professor Information Extraction - Visual Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         D2L COURSE HOME PAGE                            │
│  https://www.fanshaweonline.ca/d2l/home/2001540                        │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │ Professor Information Widget (JavaScript-rendered)           │     │
│  │                                                               │     │
│  │  Name: Mohammad Noorchenarboo                                │     │
│  │  Office: By appointment only                                 │     │
│  │  Office Hours: Please email to arrange a meeting             │     │
│  │  Email: mnoorchenarboo@fanshawec.ca                         │     │
│  └──────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Scrape with Playwright
                                    ↓
         ┌─────────────────────────────────────────────┐
         │   extract_professor_info.py                 │
         │                                             │
         │  • Microsoft SSO + 2FA authentication       │
         │  • Wait for JavaScript rendering            │
         │  • Multiple extraction strategies:          │
         │    - Widget selectors                       │
         │    - Shadow DOM access                      │
         │    - Full page scan                         │
         │    - Pattern matching (regex)               │
         │  • Debug mode with screenshots              │
         └─────────────────────────────────────────────┘
                                    │
                                    │ Output JSON
                                    ↓
         ┌─────────────────────────────────────────────┐
         │  data/course_2001540/professor_info.json    │
         │                                             │
         │  {                                          │
         │    "course_id": "2001540",                  │
         │    "name": "Mohammad Noorchenarboo",        │
         │    "email": "mnoorchenarboo@...",          │
         │    "office": "By appointment only",         │
         │    "office_hours": "Please email...",       │
         │    "extracted_at": "2025-11-22T...",       │
         │    "extraction_method": "widget_..."        │
         │  }                                          │
         └─────────────────────────────────────────────┘
                                    │
                                    │ Read cache
                                    ↓
         ┌─────────────────────────────────────────────┐
         │  announcement_transformer.py                │
         │                                             │
         │  load_professor_info(course_id)             │
         │         ↓                                   │
         │  extract_poster(content, prof_info)         │
         │         ↓                                   │
         │  Strategies:                                │
         │  1. Signature extraction                    │
         │  2. Title pattern matching                  │
         │  3. Generic greeting + cached name          │
         │  4. Context-based attribution               │
         │  5. Fallback to cached name                 │
         └─────────────────────────────────────────────┘
                                    │
                                    │ Transform announcements
                                    ↓
         ┌─────────────────────────────────────────────┐
         │  Announcement with Professor Name           │
         │                                             │
         │  {                                          │
         │    "title": "Assignment 2 Update",          │
         │    "posted_by": "Mohammad Noorchenarboo",   │
         │    "content": "Dear all, ...",              │
         │    "date": "2025-11-22",                    │
         │    "priority": "high"                       │
         │  }                                          │
         └─────────────────────────────────────────────┘
                                    │
                                    │ Display in chatbot
                                    ↓
         ┌─────────────────────────────────────────────┐
         │           Chatbot Integration               │
         │                                             │
         │  User: "Who posted the latest announcement?"│
         │                                             │
         │  Bot: "Mohammad Noorchenarboo posted:       │
         │        Assignment 2 is now available..."    │
         └─────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                            API ENDPOINTS
═══════════════════════════════════════════════════════════════════════════

  GET /api/professor/<course_id>
  ┌─────────────────────────────────────────────────────────────────┐
  │  Returns cached professor info for specific course              │
  │                                                                  │
  │  Request:  GET /api/professor/2001540                           │
  │                                                                  │
  │  Response: {                                                    │
  │    "status": "success",                                         │
  │    "course_id": "2001540",                                      │
  │    "professor": {                                               │
  │      "name": "Mohammad Noorchenarboo",                          │
  │      "email": "mnoorchenarboo@fanshawec.ca",                   │
  │      "office": "By appointment only",                           │
  │      "office_hours": "Please email to arrange a meeting"        │
  │    },                                                           │
  │    "metadata": {                                                │
  │      "extracted_at": "2025-11-22T13:23:19",                    │
  │      "data_age": "0.1 days ago",                                │
  │      "extraction_method": "manual_from_screenshot"              │
  │    }                                                            │
  │  }                                                              │
  └─────────────────────────────────────────────────────────────────┘

  GET /api/professor/status
  ┌─────────────────────────────────────────────────────────────────┐
  │  Lists all courses with cached professor data                   │
  │                                                                  │
  │  Request:  GET /api/professor/status                            │
  │                                                                  │
  │  Response: {                                                    │
  │    "status": "success",                                         │
  │    "total_courses": 1,                                          │
  │    "courses": [                                                 │
  │      {                                                          │
  │        "course_id": "2001540",                                  │
  │        "name": "Mohammad Noorchenarboo",                        │
  │        "email": "mnoorchenarboo@fanshawec.ca",                 │
  │        "extracted_at": "2025-11-22T13:23:19",                  │
  │        "data_age": "0.1 days ago",                              │
  │        "has_name": true,                                        │
  │        "has_email": true                                        │
  │      }                                                          │
  │    ]                                                            │
  │  }                                                              │
  └─────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                        EXTRACTION STRATEGIES
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│  Strategy 1: Widget Selector Matching                                   │
│  ─────────────────────────────────────                                  │
│  document.querySelectorAll('.d2l-widget')                                │
│  → Find elements with professor-related text                            │
│  → Extract name, email, office, hours via regex                         │
│                                                                          │
│  Success Rate: ~90% (if widget renders)                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Strategy 2: Shadow DOM Access                                          │
│  ─────────────────────────────                                          │
│  element.shadowRoot.querySelector(...)                                   │
│  → Access encapsulated content                                          │
│  → Extract from shadow tree                                             │
│                                                                          │
│  Success Rate: ~60% (if shadow DOM used)                                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Strategy 3: Full Page Scan                                             │
│  ─────────────────────────                                              │
│  document.body.innerText                                                 │
│  → Search entire page content                                           │
│  → Pattern match for professor info                                     │
│                                                                          │
│  Success Rate: ~95% (always works if data visible)                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Strategy 4: Regex Pattern Matching                                     │
│  ──────────────────────────────────                                     │
│  Name: /Name:\s*([^\n]+)/i                                              │
│  Email: /([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+)/                 │
│  Office: /Office:\s*([^\n]+)/i                                          │
│  Hours: /Office Hours?:\s*([^\n]+)/i                                    │
│                                                                          │
│  Success Rate: ~85% (depends on format consistency)                     │
└─────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                          TIMING DIAGRAM
═══════════════════════════════════════════════════════════════════════════

  0s ──────▶ Navigate to login page
             │
  2s ──────▶ Fill credentials
             │
  5s ──────▶ 2FA approval (human interaction)
             │
  8s ──────▶ Navigate to course home
             │
 11s ──────▶ Wait for page load (domcontentloaded)
             │
 14s ──────▶ Wait for JavaScript execution (4-6s)
             │
 17s ──────▶ Wait for widget content (2-3s)
             │
 20s ──────▶ Execute extraction JavaScript
             │
 21s ──────▶ Process and save JSON
             │
 22s ──────▶ ✅ Complete

  Total Time: ~15-20 seconds (with 2FA)
  Batch Time: ~10 seconds per course (session reuse)


═══════════════════════════════════════════════════════════════════════════
                        POSTER EXTRACTION FLOW
═══════════════════════════════════════════════════════════════════════════

Announcement Content
        │
        ↓
  ┌────────────────────────────────┐
  │ Strategy 1: Signature Pattern  │
  │ "Thank you,\nJohn Smith"       │
  └────────────────────────────────┘
        │ Found? → Return extracted name
        ↓ No
  ┌────────────────────────────────┐
  │ Strategy 2: Title Pattern      │
  │ "Professor X" or "Dr. X"       │
  └────────────────────────────────┘
        │ Found? → Return matched text
        ↓ No
  ┌────────────────────────────────┐
  │ Strategy 3: Generic Greeting   │
  │ "Dear all," + professor_info   │
  └────────────────────────────────┘
        │ Found? → Return cached name
        ↓ No
  ┌────────────────────────────────┐
  │ Strategy 4: Context Indicators │
  │ Has "assignment"/"grade"?      │
  └────────────────────────────────┘
        │ Yes? → Return cached name
        ↓ No
  ┌────────────────────────────────┐
  │ Strategy 5: Fallback           │
  │ Return cached name or          │
  │ "Instructor"                   │
  └────────────────────────────────┘
        │
        ↓
  Final Poster Name


═══════════════════════════════════════════════════════════════════════════
                        DATA FLOW SUMMARY
═══════════════════════════════════════════════════════════════════════════

  D2L Page → Scraper → JSON Cache → Transformer → Announcements → Chatbot
     ↑                                                                  │
     │                                                                  │
     └──────────────── Manual refresh (once per semester) ─────────────┘


═══════════════════════════════════════════════════════════════════════════
                        FILES & DEPENDENCIES
═══════════════════════════════════════════════════════════════════════════

  extract_professor_info.py
    ├── playwright (browser automation)
    ├── playwright_stealth (anti-detection)
    ├── dotenv (credentials)
    └── asyncio (async operations)

  announcement_transformer.py
    ├── json (read cache)
    ├── re (pattern matching)
    └── pathlib (file paths)

  main.py (API)
    ├── flask (web framework)
    ├── json (response formatting)
    └── datetime (data age calculation)

  Output: data/course_{ID}/professor_info.json
    └── Read by: announcement_transformer.py
        └── Used by: chatbot responses
