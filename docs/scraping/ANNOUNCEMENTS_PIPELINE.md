# D2L Announcements Pipeline

## 📋 Overview

The D2L Announcements Pipeline is an automated system that extracts course announcements from Fanshawe's Brightspace/D2L platform and makes them available to the chatbot. The pipeline uses Playwright for browser automation and stores data in a centralized location accessible by both the scraper and chatbot.

## 🏗️ Architecture

### Data Flow
```
D2L Website → Playwright Scraper → src/data/announcements/all_announcements.json → Chatbot
```

### Components
1. **Scraper**: `src/scrapers/d2l/announcements.py`
2. **Path Configuration**: `src/config/paths.py`
3. **Chatbot Handler**: `src/api/app.py` (handle_announcement_query)
4. **Pipeline Script**: `run_announcements_pipeline.sh`

### Centralized Path Management
All components use `src/config/paths.py` for consistent file paths:
```python
from src.config.paths import ANNOUNCEMENTS_FILE
# Always points to: src/data/announcements/all_announcements.json
```

## 🚀 Quick Start

### Prerequisites
1. Python virtual environment activated
2. Playwright installed with Firefox browser
3. D2L credentials in `.env` file

### Running the Pipeline

**Automated Method (Recommended):**
```bash
./run_announcements_pipeline.sh
```

**Manual Method:**
```bash
source .venv/bin/activate
python -m src.scrapers.d2l.announcements
```

## 📦 Setup Instructions

### 1. Environment Configuration

Create or update `.env` file:
```bash
D2L_USERNAME=your_email@fanshaweonline.ca
D2L_PASSWORD=your_password
```

### 2. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (first time only)
python -m playwright install firefox
```

### 3. Verify Configuration

Test the path configuration:
```bash
python -c "from src.config.paths import ANNOUNCEMENTS_FILE; print(f'Path: {ANNOUNCEMENTS_FILE}'); print(f'Exists: {ANNOUNCEMENTS_FILE.exists()}')"
```

## 🔧 Pipeline Script Features

The `run_announcements_pipeline.sh` script provides:

- ✅ **Automatic Environment Check**: Verifies virtual environment is activated
- ✅ **Credential Validation**: Checks for .env file existence
- ✅ **Dependency Verification**: Ensures Playwright is installed
- ✅ **Progress Indicators**: Shows clear status messages
- ✅ **Error Handling**: Exits gracefully with helpful error messages
- ✅ **Summary Report**: Displays announcement count and course info
- ✅ **Success Validation**: Confirms output file was created

### Output Example

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    D2L ANNOUNCEMENTS PIPELINE                                ║
║                  Fanshawe Navigator - Capstone Project                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

✓ Virtual environment: Active
✓ Environment file: Found
✓ Playwright: Installed

🚀 Starting D2L Announcements Scraper...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Scraper output...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Pipeline completed successfully!
📄 Output saved to: src/data/announcements/all_announcements.json

📊 Summary:
   Course: INFO-6156-(01)-25F
   Total Announcements: 5

💬 The chatbot can now access these announcements!
   Ask: 'What are the recent announcements?' or 'Show me D2L updates'
```

## 📄 Data Structure

### Output File Location
```
src/data/announcements/all_announcements.json
```

### JSON Schema
```json
{
  "total_announcements": 5,
  "successful": 5,
  "failed": 0,
  "course": "INFO-6156-(01)-25F",
  "extracted_at": "2025-12-08T18:36:31.458370",
  "home_page": {
    "url": "https://www.fanshaweonline.ca/d2l/home",
    "content": "Page content...",
    "content_length": 204
  },
  "announcements": [
    {
      "index": 1,
      "title": "Sprint 4 Presentation - reg",
      "date": "Dec 1, 2025 9:20 PM",
      "url": "https://www.fanshaweonline.ca/d2l/le/news/2001542/2270052/view?ou=2001542",
      "content": "Dear all, Please note...",
      "content_length": 373
    }
  ]
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `total_announcements` | int | Total number of announcements extracted |
| `successful` | int | Number of successfully extracted announcements |
| `failed` | int | Number of failed extraction attempts |
| `course` | string | Course identifier (e.g., INFO-6156-(01)-25F) |
| `extracted_at` | string | ISO timestamp of extraction |
| `home_page.url` | string | D2L home page URL |
| `home_page.content` | string | Home page HTML content |
| `home_page.content_length` | int | Length of home page content |
| `announcements` | array | List of announcement objects |
| `announcements[].index` | int | Sequential index (1-based) |
| `announcements[].title` | string | Announcement title |
| `announcements[].date` | string | Publication date/time |
| `announcements[].url` | string | Direct link to announcement |
| `announcements[].content` | string | Full announcement text |
| `announcements[].content_length` | int | Length of announcement content |

## 🤖 Chatbot Integration

### How the Chatbot Uses Announcements

The chatbot automatically reads from `src/data/announcements/all_announcements.json` when handling announcement queries.

### Example Interactions

**Query 1: General Announcements**
```
User: "What are the recent announcements?"
Bot: 📢 Recent D2L Announcements
     Course: INFO-6156-(01)-25F
     Total: 5 announcements
     
     1. Sprint 4 Presentation - reg (Dec 1, 2025)
        Dear all, Please note...
     
     2. Reminder: Capstone Class & Agentic AI Workshop (Nov 18, 2025)
        Please note that we will be meeting...
```

**Query 2: Specific Topic**
```
User: "Any announcements about presentations?"
Bot: Yes! Here's what I found about presentations:
     
     - Sprint 4 Presentation - reg (Dec 1, 2025)
       Sprint 4 presentations will begin tomorrow...
```

**Query 3: Date-Based**
```
User: "What were the November announcements?"
Bot: Here are the announcements from November 2025:
     
     1. Reminder: Capstone Class & Agentic AI Workshop (Nov 18)
     2. Building Agentic AI using IBM Tools (Nov 13)
     3. Gentle Reminder - Sprint 2 (Nov 4)
```

### Intent Classification

The chatbot identifies announcement queries using these patterns:
- Keywords: "announcement", "announcements", "D2L", "news", "updates"
- Questions: "what's new?", "any updates?", "show me announcements"
- Specific: "course announcements", "class updates", "D2L news"

### Handler Location

**File**: `src/api/app.py`
**Function**: `handle_announcement_query(user_message, entities)`
**Lines**: ~1043-1087

```python
def handle_announcement_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles announcement-related queries"""
    announcements_path = ANNOUNCEMENTS_FILE  # Uses centralized path
    if not announcements_path.exists():
        return {'reply': 'Announcement information is currently unavailable...'}
    # ... processes and returns announcements
```

## 🔄 Updating Announcements

### Manual Update
Run the pipeline script whenever you want fresh announcements:
```bash
./run_announcements_pipeline.sh
```

### Recommended Frequency
- **Daily**: For active courses with frequent updates
- **Weekly**: For general course monitoring
- **On-Demand**: Before important deadlines or events

### Automation Options (Future Enhancement)
The pipeline could be automated using:
- **Cron Job**: Schedule regular updates
  ```bash
  # Run daily at 8 AM
  0 8 * * * cd /path/to/project && ./run_announcements_pipeline.sh
  ```
- **GitHub Actions**: Cloud-based scheduled execution
- **Systemd Timer**: System-level scheduling on Linux

## 🐛 Troubleshooting

### Issue: Pipeline Fails with "Virtual environment not activated"
**Solution:**
```bash
source .venv/bin/activate
./run_announcements_pipeline.sh
```

### Issue: "Playwright not installed"
**Solution:**
```bash
pip install playwright
python -m playwright install firefox
```

### Issue: "2FA Required" during scraping
**Expected Behavior**: The scraper will display the verification code in terminal
**Action**: Enter the code when prompted by Microsoft SSO

### Issue: Chatbot says "Announcements unavailable"
**Check:**
1. File exists: `ls -la src/data/announcements/all_announcements.json`
2. File has content: `wc -l src/data/announcements/all_announcements.json`
3. Run pipeline: `./run_announcements_pipeline.sh`

### Issue: Permission denied on script
**Solution:**
```bash
chmod +x run_announcements_pipeline.sh
```

## 📊 Monitoring & Validation

### Check Pipeline Status
```bash
# View last run timestamp
python -c "import json; data=json.load(open('src/data/announcements/all_announcements.json')); print(f\"Last updated: {data['extracted_at']}\")"
```

### Validate Data
```bash
# Check announcement count
python -c "import json; data=json.load(open('src/data/announcements/all_announcements.json')); print(f\"Total: {data['total_announcements']} | Success: {data['successful']} | Failed: {data['failed']}\")"
```

### API Endpoint
Check status via REST API:
```bash
curl http://localhost:8081/api/announcements/status
```

Response:
```json
{
  "status": "available",
  "file_exists": true,
  "total_announcements": 5,
  "course": "INFO-6156-(01)-25F"
}
```

## 🔐 Security Considerations

### Credential Management
- ✅ Store credentials in `.env` file (gitignored)
- ✅ Never commit `.env` to version control
- ✅ Use environment variables for CI/CD
- ❌ Never hardcode credentials in source files

### Authentication Flow
1. Scraper reads credentials from `.env`
2. Playwright handles Microsoft SSO login
3. 2FA codes displayed in terminal (if required)
4. Session ends after scraping (no persistent login)

## 📝 Related Documentation

- **Main README**: `README.md` - Full system documentation
- **D2L Scraper Guide**: `docs/scraping/D2L_SCRAPER_README.md` - Detailed scraper documentation
- **API Documentation**: `src/api/app.py` - Chatbot handler implementation
- **Path Configuration**: `src/config/paths.py` - Centralized path definitions

## 🔄 Version History

### v1.1 (December 2025)
- ✅ Centralized path configuration in `src/config/paths.py`
- ✅ Pipeline script with automated checks
- ✅ Standardized save location: `src/data/announcements/`
- ✅ Enhanced error handling and validation
- ✅ Documentation updates

### v1.0 (November 2025)
- Initial announcements scraper implementation
- Basic D2L authentication and extraction
- JSON output format defined

## 🤝 Contributing

When modifying the announcements pipeline:

1. **Always use centralized paths**: Import from `src.config.paths`
2. **Test both scraper and chatbot**: Ensure compatibility
3. **Update documentation**: Keep this file current
4. **Validate output format**: Maintain JSON schema consistency
5. **Handle errors gracefully**: Add informative error messages

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review related documentation
3. Test with `./run_announcements_pipeline.sh --help` (if implemented)
4. Contact the development team
