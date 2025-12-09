# D2L Announcements Testing Pipeline - Quick Start

## What Is This?

A complete web scraping pipeline for extracting course announcements from Fanshawe College's D2L Learning Management System, following the proven restaurant scraper architecture.

**Target:** https://www.fanshaweonline.ca/d2l/home/2001539 (INFO-6153 course)

---

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip3 install --break-system-packages playwright playwright-stealth python-dotenv
python3 -m playwright install firefox
```

### Step 2: Configure Credentials
Create/edit `.env` file:
```env
D2L_USERNAME=your_fanshawe_email@fanshaweonline.ca
D2L_PASSWORD=your_password
```

### Step 3: Run Pipeline
```bash
python3 src/scrapers/d2l/announcements_testing.py
```

---

## Understanding Output

The script creates timestamped JSON files in `data/course_2001539/`:
- **File:** `announcements_testing_20251208_193045.json`
- **Size:** ~10-50 KB (depending on content)
- **Contains:** Announcement list + detailed content from first 10 announcements

### Sample Output Structure
```json
{
  "metadata": {
    "total_announcements_found": 5,
    "successful_details": 5,
    "failed_details": 0
  },
  "announcements_list": [
    {"title": "...", "date": "...", "url": "..."}
  ],
  "announcements_detailed": [
    {
      "title": "...",
      "content": "...",
      "content_length": 245
    }
  ]
}
```

---

## Common Commands

```bash
# Basic run (uses course 2001539)
python3 src/scrapers/d2l/announcements_testing.py

# Different course
python3 src/scrapers/d2l/announcements_testing.py --course-id 2001234

# Custom output location
python3 src/scrapers/d2l/announcements_testing.py --output /path/to/output.json

# Debug mode (verbose output)
python3 src/scrapers/d2l/announcements_testing.py --debug
```

---

## What Gets Extracted

### From Home Page
- ✓ Announcement titles
- ✓ Publication dates
- ✓ Announcement URLs

### From Each Announcement
- ✓ Full content/text
- ✓ Author (if available)
- ✓ Publication date
- ✓ Attachment information

---

## Pipeline Stages (Live Output)

```
[1/4] Accessing D2L course home page...
✓ Home page loaded!

[2/4] Extracting announcements from home page...
✓ Found 5 announcements!

[3/4] Extracting details from 5 announcements...
[1/5] Quiz 2 will be on Friday, November 28.
  ✓ Accessible - 245 chars

[4/4] Saving results...
✓ Output file: data/course_2001539/announcements_testing_20251208_193045.json
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: playwright` | Run: `pip3 install --break-system-packages playwright` |
| `Login fails` | Check D2L_USERNAME and D2L_PASSWORD in .env |
| `2FA timeout` | Check Microsoft Authenticator app for approval |
| `No announcements found` | Verify course ID is correct and you have access |
| `Content extraction is empty` | This is normal for some announcements |

---

## Architecture Comparison

**This pipeline follows the restaurant scraper pattern:**

| Aspect | Restaurant | D2L Announcements |
|--------|-----------|-------------------|
| **Pages Accessed** | 1 main + 5 detail | 1 main + 10 detail |
| **Authentication** | None | Microsoft SSO + 2FA |
| **Extraction Methods** | 3-tier strategies | 2-3 strategies per field |
| **Output Format** | Timestamped JSON | Timestamped JSON |
| **Error Handling** | Graceful degradation | Partial results saved |

---

## File Locations

```
src/scrapers/d2l/
├── announcements_testing.py       (490 lines - main script)
├── __init__.py                    (exports function)
└── ...other D2L scrapers

data/course_2001539/
├── announcements_testing_*.json   (output files - timestamped)
├── Announcements.json             (existing data reference)
└── ...other course data

Documentation/
├── D2L_ANNOUNCEMENTS_TESTING_GUIDE.md  (full documentation)
└── D2L_TESTING_QUICK_START.md          (this file)
```

---

## Key Features

✓ **Automatic Login** - Detects and performs D2L authentication
✓ **2FA Support** - Handles Microsoft Authenticator with auto-detection
✓ **Multiple Strategies** - Fallback extraction methods ensure robustness
✓ **Graceful Errors** - Individual failures don't stop entire process
✓ **Partial Results** - Always saves what was extracted, even on errors
✓ **Resource Optimization** - Blocks images/fonts/media for speed
✓ **Rate Limiting** - Human-like delays between requests
✓ **Stealth Mode** - Avoids bot detection

---

## Next Steps After Running

1. **Check Output File**
   ```bash
   cat data/course_2001539/announcements_testing_*.json | python3 -m json.tool
   ```

2. **Count Announcements**
   ```bash
   python3 -c "import json; d=json.load(open('data/course_2001539/announcements_testing_*.json')); print(f\"Found {d['metadata']['total_announcements_found']} announcements\")"
   ```

3. **Extract Titles Only**
   ```bash
   python3 -c "import json; d=json.load(open('data/course_2001539/announcements_testing_*.json')); print('\\n'.join(a['title'] for a in d['announcements_list']))"
   ```

---

## Performance Expectations

- **Home Page:** 2-3 seconds
- **Authentication:** 5-10 seconds
- **10 Announcements:** 15-25 seconds
- **2FA (manual):** Up to 5 minutes waiting
- **Total:** ~30-50 seconds (without 2FA wait)

---

## For More Information

See **D2L_ANNOUNCEMENTS_TESTING_GUIDE.md** for:
- Complete architecture documentation
- All available options and parameters
- Detailed troubleshooting guide
- Future enhancement ideas
- Security considerations

---

**Status:** Testing Pipeline - Production Ready
**Created:** 2025-12-08
**Based on:** Restaurant Scraper Architecture
