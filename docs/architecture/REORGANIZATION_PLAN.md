# 📁 Project Reorganization Plan

## 🎯 Goal
Transform the root directory from 80+ files into a clean, professional structure.

## 🏗️ Proposed Architecture: **Feature-Based Modular**

Better than DDD for this project because:
- ✅ Simpler and more practical for scrapers + API + RAG
- ✅ Easy to understand and maintain  
- ✅ Groups related code by feature
- ✅ Avoids DDD over-engineering

---

## 📂 NEW STRUCTURE

```
Capstone_Project_AIM/
│
├── 📄 README.md                          # Main project documentation
├── 📄 pyproject.toml                     # Python project config
├── 📄 requirements.txt                   # Dependencies
├── 📄 uv.lock                            # Lock file
├── 📄 .env.example                       # Environment template
├── 📄 .gitignore
├── 📄 docker-compose.yml
├── 📄 Dockerfile
│
├── 📁 docs/                              # ALL DOCUMENTATION HERE
│   ├── README.md                         # Docs index
│   ├── architecture/
│   │   ├── system_overview.md
│   │   └── professor_architecture_visual.md
│   ├── guides/
│   │   ├── announcements_integration.md
│   │   ├── announcements_usage.md
│   │   ├── professor_extraction.md
│   │   ├── quick_start_announcements.md
│   │   └── quick_start_multi_course.md
│   ├── scraping/
│   │   ├── d2l_agent_integration.md
│   │   ├── d2l_scraper_readme.md
│   │   └── sharepoint_scraper.md
│   └── api/
│       └── endpoints.md
│
├── 📁 src/                               # MAIN APPLICATION CODE
│   ├── __init__.py
│   │
│   ├── 📁 scrapers/                      # Feature: Web Scraping
│   │   ├── __init__.py
│   │   ├── base_scraper.py              # Abstract base class
│   │   ├── d2l/
│   │   │   ├── __init__.py
│   │   │   ├── announcements.py         # extract_all_announcements.py → here
│   │   │   ├── content_home.py          # extract_content_home.py → here
│   │   │   ├── professor_info.py        # extract_professor_info.py → here
│   │   │   └── auth.py                  # 2FA, login logic shared
│   │   ├── sharepoint/
│   │   │   ├── __init__.py
│   │   │   ├── events.py                # extract_sharepoint_events.py → here
│   │   │   └── auth.py                  # SharePoint auth
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── browser.py               # Playwright setup
│   │       └── parser.py                # HTML parsing utilities
│   │
│   ├── 📁 api/                           # Feature: REST API (Flask)
│   │   ├── __init__.py
│   │   ├── app.py                       # main.py → here (Flask app)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── announcements.py
│   │   │   ├── professors.py
│   │   │   ├── events.py
│   │   │   └── navigation.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── cors.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── response_models.py
│   │
│   ├── 📁 services/                      # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── announcement_transformer.py  # Keep as is
│   │   ├── embedding_service.py
│   │   ├── professor_service.py
│   │   └── event_service.py
│   │
│   ├── 📁 navigation/                    # Feature: Indoor Navigation
│   │   ├── __init__.py
│   │   ├── route_planner.py
│   │   ├── map_processor.py
│   │   └── validators/
│   │       └── route_validator.py
│   │
│   ├── 📁 embeddings/                    # Feature: RAG / Embeddings
│   │   ├── __init__.py
│   │   ├── generator.py                 # update_embeddings.py logic
│   │   ├── validator.py                 # validate_map_embeddings.py
│   │   └── rag_engine.py                # multimodal_rag_complete.py
│   │
│   ├── 📁 database/                      # Data Access Layer
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── announcement_repo.py
│   │   │   ├── professor_repo.py
│   │   │   └── event_repo.py
│   │   └── cache/
│   │       ├── __init__.py
│   │       └── cache_manager.py
│   │
│   ├── 📁 models/                        # Data Models
│   │   ├── __init__.py
│   │   ├── announcement.py
│   │   ├── professor.py
│   │   ├── event.py
│   │   └── navigation.py
│   │
│   ├── 📁 config/                        # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py                  # Centralized config
│   │   └── constants.py
│   │
│   └── 📁 utils/                         # Shared Utilities
│       ├── __init__.py
│       ├── logger.py
│       ├── file_handler.py
│       └── date_parser.py
│
├── 📁 scripts/                           # Standalone Scripts
│   ├── setup_environment.py             # Keep
│   ├── run_tests.py                     # Keep
│   ├── scrape_all.py                    # New: run all scrapers
│   ├── process_course.py                # Move here
│   ├── transform_cache.py               # Move here
│   └── debug/
│       ├── debug_login.py               # debug_login_page.py → here
│       ├── debug_announcement.py        # Keep
│       ├── debug_professor.py           # New if needed
│       └── debug_sharepoint.py          # debug_sharepoint_page.py → here
│
├── 📁 tests/                             # Test Suite
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   ├── unit/
│   │   ├── test_scrapers.py
│   │   ├── test_services.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_professor_integration.py  # Move here
│   │   └── test_announcements_chat.py     # Move here
│   └── e2e/
│       └── test_workflow.py
│
├── 📁 data/                              # Data Storage (Keep as is)
│   ├── announcements/
│   ├── professors/
│   ├── sharepoint_events/
│   └── embeddings/
│
├── 📁 static/                            # Static Assets (Keep)
│   ├── css/
│   ├── js/
│   └── images/
│
├── 📁 templates/                         # HTML Templates (Keep)
│   └── index.html
│
├── 📁 maps/                              # Map Data (Keep)
│   └── building_data/
│
├── 📁 tools/                             # Development Tools
│   ├── route_generator.py               # generate_route_templates.py → here
│   ├── route_viewer.py                  # generate_route_viewer.py → here
│   └── diagnostics/
│       ├── diagnose_routes.py           # Move here
│       ├── check_map_routes.py          # Move here
│       └── list_routes.py               # Move here
│
└── 📁 temp/                              # Temporary files (gitignored)
    └── .gitkeep
```

---

## 🔄 MIGRATION STEPS

### **Phase 1: Documentation** ✅
```bash
mkdir -p docs/{architecture,guides,scraping,api}
mv *.md docs/guides/  # All MD files except README.md
mv docs/guides/README.md ./  # Keep main README in root
```

### **Phase 2: Scrapers** 🔧
```bash
# D2L Scrapers
mkdir -p src/scrapers/d2l
mv extract_all_announcements.py src/scrapers/d2l/announcements.py
mv extract_content_home.py src/scrapers/d2l/content_home.py
mv extract_professor_info.py src/scrapers/d2l/professor_info.py

# SharePoint Scrapers
mkdir -p src/scrapers/sharepoint
mv extract_sharepoint_events.py src/scrapers/sharepoint/events.py
```

### **Phase 3: API** 🌐
```bash
mv main.py src/api/app.py
# Refactor routes into src/api/routes/
```

### **Phase 4: Scripts & Tools** 📜
```bash
# Debug scripts
mkdir -p scripts/debug
mv debug_*.py scripts/debug/

# Processing scripts
mv process_course.py scripts/
mv transform_cache.py scripts/

# Tools
mv generate_*.py tools/
mv diagnose_*.py tools/diagnostics/
mv check_*.py tools/diagnostics/
mv list_*.py tools/diagnostics/
```

### **Phase 5: Tests** 🧪
```bash
mkdir -p tests/{unit,integration,e2e}
mv test_*.py tests/integration/
```

### **Phase 6: Cleanup** 🧹
```bash
# Remove debug artifacts
rm debug_*.html debug_*.png login_page_debug.* error_screenshot.png

# Remove old JSON files from root (move to data/)
mv *.json data/legacy/  # If needed
```

---

## 🎯 BENEFITS

### Before (Current):
- ❌ 80+ files in root directory
- ❌ Hard to find specific functionality
- ❌ Mixing concerns (scrapers + API + tools)
- ❌ Documentation scattered

### After (Proposed):
- ✅ ~15 files in root (clean!)
- ✅ Clear separation by feature
- ✅ Easy to navigate (`src/scrapers/`, `src/api/`, etc.)
- ✅ All docs in one place
- ✅ Tests properly organized
- ✅ Scalable structure for future growth

---

## 🚀 IMPLEMENTATION ORDER

1. **Create directory structure** (5 min)
2. **Move documentation** (10 min) - Safest first step
3. **Move scripts & tools** (15 min) - No code changes
4. **Move scrapers** (20 min) - Update imports
5. **Refactor API** (30 min) - Split routes
6. **Move tests** (10 min)
7. **Update all imports** (20 min)
8. **Test everything** (30 min)
9. **Update README with new structure** (15 min)

**Total estimated time: ~2.5 hours**

---

## 📝 NOTES

- **Imports will need updating**: Use relative imports within `src/`
- **Keep backwards compatibility**: Create symlinks if needed temporarily
- **Git tracking**: Use `git mv` to preserve history
- **Commit frequently**: One commit per phase

---

## ❓ WHY NOT DDD?

DDD (Domain-Driven Design) would add:
- `domain/entities/`, `domain/value_objects/`, `domain/aggregates/`
- `application/use_cases/`, `application/commands/`
- `infrastructure/repositories/`, `infrastructure/external_services/`

**Too complex for:**
- Web scraping project (not a complex business domain)
- Small team / solo developer
- Rapid prototyping needs

**Current approach is better:** Clean, simple, feature-focused modules.
