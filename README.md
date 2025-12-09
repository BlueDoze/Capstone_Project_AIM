# 🏢 Fanshawe Navigator - AI Campus Navigation System

A sophisticated **Multimodal RAG (Retrieval-Augmented Generation)** system that provides intelligent navigation assistance for Fanshawe College campus. This AI-powered application combines visual understanding, interactive maps, natural language processing, and web scraping to deliver precise, context-aware campus information with real-time map visualization.

## 🎯 Project Overview

This system leverages **Google's Gemini AI models**, **Vertex AI**, **Leaflet.js mapping**, and **Playwright web scraping** to create an intelligent campus assistant that can:

- 📍 **Interactive Map Navigation**: Visual route display on real campus floor plans with clickable rooms
- 🗺️ **Dual Navigation Modes**: Chat-to-Map and Map-to-Chat interaction
- 🤖 **AI-Powered Responses**: Use multimodal AI to understand both text queries and visual context
- 🔍 **Smart Search**: Find relevant information using advanced embedding-based similarity search
- 📱 **Web Interface**: Clean, responsive chat interface with integrated mapping
- 🔄 **Auto-Updates**: Automatically processes new images and updates embeddings
- 📐 **Precise Positioning**: Accurate room center calculations with manual override capability
- 📢 **D2L Integration**: Scrapes and displays course announcements from Brightspace
- 🎓 **Professor Information**: Extracts and displays professor contact details and office hours
- 📅 **SharePoint Events**: Automatically scrapes campus events from SharePoint Modern Events
- 🍽️ **Campus Services**: Information about events, restaurants, and campus facilities
- 🎯 **Intent Classification**: Intelligent routing of queries to appropriate handlers

## 🏗️ Project Organization (NEW - Nov 2024)

This project has been recently reorganized into a clean, modular **Feature-Based Architecture** for improved maintainability and scalability. See [REORGANIZATION_SUMMARY.md](docs/architecture/REORGANIZATION_SUMMARY.md) for complete details.

### **Directory Structure**

```
Capstone_Project_AIM/
├── 📁 docs/                        # All documentation (organized by category)
│   ├── architecture/               # Architecture decisions and diagrams
│   ├── guides/                     # User guides and tutorials
│   ├── scraping/                   # Scraper documentation
│   └── api/                        # API documentation (future)
├── 📁 src/                         # All source code (modular organization)
│   ├── api/                        # Flask application (app.py)
│   ├── scrapers/                   # Data extraction modules
│   │   ├── d2l/                   # D2L/Brightspace scrapers
│   │   ├── sharepoint/            # SharePoint scrapers
│   │   └── utils/                 # Shared scraping utilities
│   ├── models/                     # ML models and embeddings
│   ├── services/                   # Business logic
│   ├── config/                     # Configuration management
│   └── utils/                      # General utilities
├── 📁 scripts/                     # Utility scripts (organized by purpose)
│   ├── debug/                      # Debugging tools
│   ├── processing/                 # Data processing scripts
│   ├── generation/                 # Code/data generation
│   └── diagnostics/                # System diagnostics
├── 📁 tests/                       # All tests (organized by type)
├── 📁 data/                        # Data files and databases
├── 📁 config/                      # Configuration files
├── run_app.py                      # Main application entry point
├── devserver.sh                    # Development server launcher
└── requirements.txt                # Python dependencies
```

### **Key Improvements**
- ✅ Clean root directory (80+ files reduced to essentials)
- ✅ Feature-based module organization
- ✅ Backward compatibility maintained via wrapper scripts
- ✅ Git history preserved for all files
- ✅ Comprehensive documentation structure

## 📊 System Diagrams

### **1. Functional Diagram - User Interaction Flow**

This diagram shows how users interact with the system and what responses they receive:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

    USER                    SYSTEM                         OUTPUT
     │                        │                              │
     ├─ "Navigate to 1003"   │                              │
     │─────────────────────► │ Intent: NAVIGATION           │
     │                        │ Parse: Room 1003             │
     │                        │ Find: Path M1_6 → M1_8      │
     │                        │◄─────────────────────────────┤
     │◄─────────────────────  │ Map: Show route + markers    │
     │ AI Response + Map      │ Chat: Walking directions     │
     │                        │                              │
     ├─ "Campus events today" │                             │
     │─────────────────────► │ Intent: EVENTS               │
     │                        │ Query: campus_events.json    │
     │                        │ Filter: Today's date         │
     │                        │◄─────────────────────────────┤
     │◄─────────────────────  │ Chat: Event list (formatted) │
     │ Event List             │                              │
     │                        │                              │
     ├─ "Where to eat lunch?" │                             │
     │─────────────────────► │ Intent: RESTAURANTS          │
     │                        │ Query: restaurants.json      │
     │                        │ AI: Generate recommendations │
     │                        │◄─────────────────────────────┤
     │◄─────────────────────  │ Chat: Restaurant options     │
     │ Restaurant Info        │                              │
     │                        │                              │
     ├─ "D2L announcements"  │                              │
     │─────────────────────► │ Intent: ANNOUNCEMENTS        │
     │                        │ Query: d2l_announcements.json│
     │                        │ AI: Format & summarize       │
     │                        │◄─────────────────────────────┤
     │◄─────────────────────  │ Chat: Announcement list      │
     │ Announcements          │                              │
     │                        │                              │
     ├─ Click Room_1003      │                              │
     │─────────────────────► │ Mode: Navigation              │
     │                        │ Place: Green marker          │
     │◄─────────────────────  │ Status: "Select destination" │
     │                        │                              │
     ├─ Click Room_1018      │                              │
     │─────────────────────► │ Calculate: Shortest path     │
     │                        │ Display: Route visualization │
     │                        │ Generate: AI directions      │
     │                        │◄─────────────────────────────┤
     │◄─────────────────────  │ Map: Path + markers          │
     │ Route + Directions     │ Chat: Step-by-step guide     │
```

---

### **2. Logical Diagram - Data Flow & Processing**

This diagram illustrates how data flows through different processing layers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LOGICAL DATA FLOW ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: INPUT PROCESSING                                               │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  User Input          │
                    │  • Text query        │
                    │  • Map clicks        │
                    │  • Room selection    │
                    └──────────┬───────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: INTENT CLASSIFICATION                                          │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────┴───────────┐
                    │  Keyword Analysis    │
                    │  (Fast pre-filter)   │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │  Gemini AI           │
                    │  Intent Classifier   │
                    └──────────┬───────────┘
                               │
        ┌──────────┬───────────┼───────────┬───────────┐
        ▼          ▼           ▼           ▼           ▼
   NAVIGATION   EVENTS    RESTAURANTS  ANNOUNCEMENTS  OUT_OF_SCOPE
        │          │           │           │           │
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: DATA RETRIEVAL                                                 │
└─────────────────────────────────────────────────────────────────────────┘
        │          │           │           │           │
        ▼          ▼           ▼           ▼           ▼
   ┌────────┐  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐
   │ Room   │  │ Events  │ │Restaurant│ │  D2L     │ │Gemini  │
   │Resolver│  │ JSON DB │ │  JSON DB │ │  Scraper │ │Fallback│
   │        │  │         │ │          │ │  Cache   │ │        │
   │• Alias │  │• Filter │ │• Query   │ │• Refresh │ │• RAG   │
   │• Node  │  │• Sort   │ │• Match   │ │• Parse   │ │Search  │
   │  Map   │  │• Format │ │• Rank    │ │• Format  │ │        │
   └────┬───┘  └────┬────┘ └────┬─────┘ └────┬─────┘ └───┬────┘
        │          │           │           │           │
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: AI PROCESSING                                                  │
└─────────────────────────────────────────────────────────────────────────┘
        │          │           │           │           │
        └──────────┴───────────┴───────────┴───────────┘
                               │
                    ┌──────────┴───────────┐
                    │  RAG Image Search    │
                    │  • Text embeddings   │
                    │  • Image embeddings  │
                    │  • Cosine similarity │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │  Gemini 2.5 Pro      │
                    │  • Context assembly  │
                    │  • Response gen      │
                    │  • Markdown format   │
                    └──────────┬───────────┘
                               │
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: MAP PROCESSING (if navigation)                                 │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────┴───────────┐
                    │  Navigation Graph    │
                    │  • Load SVG nodes    │
                    │  • Build adjacency   │
                    │  • Room centers      │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │  Dijkstra Algorithm  │
                    │  • Shortest path     │
                    │  • Distance calc     │
                    │  • Node sequence     │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │  Coordinate Transform│
                    │  • SVG → Normalized  │
                    │  • → Geographic      │
                    │  • → Rotated (21.3°) │
                    └──────────┬───────────┘
                               │
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 6: OUTPUT ASSEMBLY                                                │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────┴───────────┐
                    │  Response Builder    │
                    │  • HTML formatting   │
                    │  • Map actions       │
                    │  • Marker coords     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  JSON Response       │
                    │  {                   │
                    │    reply: "...",     │
                    │    mapAction: {...}  │
                    │  }                   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Frontend Rendering  │
                    │  • Display chat      │
                    │  • Draw route        │
                    │  • Place markers     │
                    │  • Auto-zoom map     │
                    └──────────────────────┘
```

---

### **3. Architectural Diagram - Component Structure**

This diagram shows the physical organization of system components:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      COMPONENT ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND LAYER (Browser)                                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────┐         ┌──────────────────────────────────┐  │
│  │  Chat UI           │◄────────┤  Map Controller                  │  │
│  │  (static/          │  Events │  (static/map-controller.js)      │  │
│  │   script.js)       │         │                                  │  │
│  │                    │         │  • Leaflet.js (interactive map)  │  │
│  │  • Message input   │         │  • SVG overlay (floor plans)     │  │
│  │  • Response display│         │  • Navigation graph builder      │  │
│  │  • HTML rendering  │         │  • Dijkstra pathfinding          │  │
│  │  • Map interaction │         │  • Coordinate transformation     │  │
│  │    triggers        │         │  • Room click handlers           │  │
│  └────────────────────┘         │  • Marker placement              │  │
│           │                     │  • Route visualization           │  │
│           │                     └──────────────────────────────────┘  │
│           │                              │                            │
└───────────┼──────────────────────────────┼────────────────────────────┘
            │                              │
            │         HTTP/REST            │
            ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ APPLICATION LAYER (Flask Server - main.py)                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Route Handlers                                                   │  │
│  ├─────────────────────────────────────────────────────────────────┤  │
│  │  /chat              │ Main chatbot endpoint (intent classifier) │  │
│  │  /api/navigation/*  │ Navigation API (parse, rooms, centers)    │  │
│  │  /api/announcements*│ D2L announcement management               │  │
│  │  /images/*          │ Image embedding management                │  │
│  │  /system/status     │ System health & diagnostics               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│           │                              │                             │
│  ┌────────┴────────┐          ┌─────────┴──────────┐                  │
│  │ Intent Router   │          │ Response Assembler │                  │
│  │ • Keyword match │          │ • HTML formatting  │                  │
│  │ • Gemini classify│         │ • Map actions      │                  │
│  └────────┬────────┘          └─────────┬──────────┘                  │
│           │                              │                             │
│  ┌────────┴──────────────────────────────┴────────┐                   │
│  │ Query Handlers                                  │                   │
│  ├─────────────────────────────────────────────────┤                   │
│  │ • handle_navigation_query()                     │                   │
│  │ • handle_event_query()                          │                   │
│  │ • handle_restaurant_query()                     │                   │
│  │ • handle_announcement_query()                   │                   │
│  │ • handle_out_of_scope_query()                   │                   │
│  └─────────────────────────────────────────────────┘                   │
│           │                              │                             │
└───────────┼──────────────────────────────┼─────────────────────────────┘
            │                              │
            ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ SERVICE LAYER (src/services/)                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐      ┌────────────────────────────────┐     │
│  │ D2L Scraper          │      │ Advanced Image Manager         │     │
│  │ (d2l_scraper.py)     │      │ (main.py)                      │     │
│  │                      │      │                                │     │
│  │ • Playwright browser │      │ • Embedding generation         │     │
│  │ • Microsoft SSO auth │      │ • Auto file monitoring         │     │
│  │ • 2FA handling       │      │ • Cache management (pickle)    │     │
│  │ • Course navigation  │      │ • Image similarity search      │     │
│  │ • Event extraction   │      │ • Watchdog integration         │     │
│  └──────────────────────┘      └────────────────────────────────┘     │
│           │                              │                             │
│  ┌────────┴────────┐          ┌─────────┴──────────┐                  │
│  │ Announcement    │          │ Room Resolver       │                  │
│  │ Transformer     │          │ • Alias lookup      │                  │
│  │ • Raw → JSON    │          │ • roomToNode map    │                  │
│  │ • Formatting    │          │ • Coordinate calc   │                  │
│  └─────────────────┘          └────────────────────┘                   │
│                                                                         │
└─────────────────────────────────────────┬───────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ AI/ML LAYER                                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Google Gemini Models (src/models/gemini_models.py)             │   │
│  ├────────────────────────────────────────────────────────────────┤   │
│  │  • gemini-2.5-pro (latest)    → Intent classification          │   │
│  │  • gemini-2.0-flash           → Fast responses                 │   │
│  │  • Multimodal understanding   → Image + text analysis          │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Vertex AI Embeddings (src/models/embedding_models.py)          │   │
│  ├────────────────────────────────────────────────────────────────┤   │
│  │  • textembedding-gecko        → Text vectorization             │   │
│  │  • multimodalembedding        → Image vectorization            │   │
│  │  • Sentence Transformer       → Semantic search                │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ RAG System (multimodal_rag_complete.py)                        │   │
│  ├────────────────────────────────────────────────────────────────┤   │
│  │  • Image processing pipeline                                   │   │
│  │  • Embedding generation & caching                              │   │
│  │  • Cosine similarity search                                    │   │
│  │  • Context retrieval & assembly                                │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────┬───────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ DATA LAYER                                                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐   │
│  │ Configuration    │  │ JSON Databases   │  │ Cache Storage     │   │
│  ├──────────────────┤  ├──────────────────┤  ├───────────────────┤   │
│  │ building_m_      │  │ campus_events    │  │ image_metadata_   │   │
│  │  rooms.json      │  │  .json           │  │  cache.pkl        │   │
│  │                  │  │                  │  │                   │   │
│  │ • Room aliases   │  │ campus_          │  │ • Embeddings      │   │
│  │ • Node mappings  │  │  restaurants     │  │ • Descriptions    │   │
│  │ • Coordinates    │  │  .json           │  │ • Metadata        │   │
│  │ • Descriptions   │  │                  │  │                   │   │
│  │                  │  │ d2l_             │  │                   │   │
│  │                  │  │  announcements   │  │                   │   │
│  │                  │  │  .json           │  │                   │   │
│  └──────────────────┘  └──────────────────┘  └───────────────────┘   │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐   │
│  │ Floor Plans      │  │ Navigation Data  │  │ Image Assets      │   │
│  ├──────────────────┤  ├──────────────────┤  ├───────────────────┤   │
│  │ M1_official.svg  │  │ floorPlansScript │  │ images/           │   │
│  │ M2.svg           │  │  .js             │  │  M1.jpeg          │   │
│  │ M3.svg           │  │                  │  │  M2.jpeg          │   │
│  │                  │  │ • Graph nodes    │  │  M3.jpeg          │   │
│  │ campus.geojson   │  │ • Connections    │  │                   │   │
│  │                  │  │ • Distances      │  │ (for RAG search)  │   │
│  └──────────────────┘  └──────────────────┘  └───────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ EXTERNAL SERVICES                                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐      ┌─────────────────────────────────┐    │
│  │ Google Cloud         │      │ D2L/Brightspace                 │    │
│  │ • Gemini API         │      │ • fanshaweonline.ca             │    │
│  │ • Vertex AI          │      │ • Microsoft SSO                 │    │
│  │ • Embeddings API     │      │ • Course pages                  │    │
│  └──────────────────────┘      └─────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### **Data Flow Architecture**

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW                                  │
└─────────────────────────────────────────────────────────────────────┘

  USER INPUT                                                    OUTPUT
     │                                                             ▲
     │                                                             │
     ▼                                                             │
┌─────────┐      ┌──────────────┐      ┌────────────┐     ┌──────────┐
│ Chat UI │─────►│ Flask Server │─────►│ Gemini API │────►│ Response │
│         │      │              │      │            │     │          │
│ Map     │      │ Parse Request│      │ Generate   │     │ • Text   │
│ Clicks  │      │              │      │ Response   │     │ • Route  │
└─────────┘      └──────────────┘      └────────────┘     │ • Markers│
     │                  │                     │            └──────────┘
     │                  │                     │                  ▲
     │                  ▼                     │                  │
     │         ┌─────────────────┐            │                  │
     │         │ Room Resolution │            │                  │
     │         │ • Aliases       │            │                  │
     │         │ • Node mapping  │            │                  │
     │         └─────────────────┘            │                  │
     │                  │                     │                  │
     │                  ▼                     │                  │
     │         ┌─────────────────┐            │                  │
     │         │ Image Context   │◄───────────┘                  │
     │         │ • RAG retrieval │                               │
     │         │ • Visual info   │                               │
     │         └─────────────────┘                               │
     │                  │                                        │
     │                  ▼                                        │
     │         ┌─────────────────┐                               │
     │         │ Map Controller  │                               │
     └────────►│ • Path calc     │───────────────────────────────┘
               │ • Coordinates   │
               │ • Visualization │
               └─────────────────┘
```

## 🚀 Key Features

### 🗺️ **Dual-Mode Interactive Navigation**

#### **Mode 1: Chat → Map** (AI-Initiated Navigation)
```
User: "Navigate from Room 1003 to Room 1018"
  ↓
Gemini parses request → Resolves room names → Finds nodes
  ↓
System sends: { startNode: "M1_6", endNode: "M1_8" }
  ↓
Map displays route with markers at room centers
```

#### **Mode 2: Map → Chat** (User-Initiated Navigation)
```
User clicks: "Start Navigation" button
  ↓
User clicks: Room_1003 on map → Green marker at room center
  ↓
User clicks: Room_1018 on map → Red marker at room center
  ↓
System calculates path → Displays route → Sends to chat
  ↓
AI generates walking directions based on visual path
```

### 📐 **Coordinate System & Accuracy**

#### **Smart Coordinate Resolution**
- **Priority 1**: Manual room centers from `config/building_m_rooms.json`
- **Priority 2**: Automatic calculation from SVG polygon bounding box
- **Priority 3**: Corridor node position (navigation fallback)

#### **Coordinate Transformation Pipeline**
```
SVG Coordinates (pixels)
        ↓
Normalized (0-1 range)
        ↓
Geographic (Lat/Lng)
        ↓
Rotated (21.3° building alignment)
        ↓
Map Display Position
```

### 🧠 **Multimodal AI Processing**
- **Gemini 2.0 Flash**: Advanced multimodal understanding
- **Text Embeddings**: Semantic search capabilities
- **Image Embeddings**: Visual similarity matching
- **Contextual Analysis**: Combines visual and textual information

### 🔄 **Intelligent Image Management**
- **Auto-Processing**: Automatically processes new images
- **Embedding Generation**: Creates vector representations for search
- **Cache System**: Efficient storage and retrieval
- **File Monitoring**: Real-time detection of new images

### 💬 **Interactive Chat Interface**
- **Real-time Chat**: Instant responses to navigation queries
- **HTML Rendering**: Rich formatting for directions
- **Responsive Design**: Works on desktop and mobile
- **Error Handling**: Graceful error recovery

### 🎯 **Navigation Intelligence**
- **Step-by-step Directions**: Detailed walking instructions
- **Room Identification**: Precise location descriptions
- **Context Awareness**: Uses building layout knowledge
- **Multi-modal Queries**: Understands both text and visual context

## 📋 Prerequisites

Before setting up the project, ensure you have:

- **Python 3.11+** installed ([Download Python](https://www.python.org/downloads/))
- **Google Cloud Account** with Vertex AI enabled ([Sign up](https://cloud.google.com/))
- **Gemini API Key** from Google AI Studio ([Get API Key](https://aistudio.google.com/apikey))
- **Git** for version control ([Download Git](https://git-scm.com/downloads))
- **Modern web browser** (Chrome, Firefox, Edge, or Safari)
- **Text editor or IDE** (VS Code, PyCharm, or similar)

### **Optional (for D2L scraping)**
- **D2L/Brightspace account** with valid credentials
- **Playwright browsers** (auto-installed with setup)

## 🛠️ Installation & Setup

### 1. **Clone the Repository**
```bash
git clone <repository-url>
cd Capstone_Project_AIM
```

### 2. **Create Virtual Environment**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Environment Configuration**

Create a `.env` file in the project root:

```bash
# Google AI/Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Google Cloud Configuration (for RAG system)
GOOGLE_CLOUD_PROJECT_ID=your_project_id_here
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

### 5. **Google Cloud Setup**

#### Enable Required APIs:
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

#### Authenticate:
```bash
gcloud auth application-default login
```

### 6. **Image Setup**

Place your building floor plan images in the `images/` directory:
```bash
images/
├── M1.jpeg    # Main floor plan
├── M2.jpeg    # Additional views
└── M3.jpeg    # Detailed sections
```

## 🚀 Running the Complete Solution

This section provides step-by-step instructions to run the entire Fanshawe Navigator system after the recent reorganization.

---

### **Method 1: Quick Start (Recommended for First-Time Users)**

This is the easiest way to get everything running:

```bash
# Step 1: Navigate to project directory
cd /path/to/Capstone_Project_AIM

# Step 2: Activate virtual environment
source .venv/bin/activate              # Linux/Mac
# OR
.venv\Scripts\activate                 # Windows

# Step 3: Verify environment setup
python -c "import google.generativeai; print('✅ Dependencies OK')"

# Step 4: Run the application using the new wrapper
python run_app.py
```

**Expected Output:**
```
🚀 Starting Fanshawe Navigator...
✅ Environment variables loaded
✅ RAG system initialized
✅ Image embeddings loaded (3 images)
✅ Configuration loaded
🌐 Server running on http://localhost:8081
📱 Open your browser and navigate to http://localhost:8081
Press Ctrl+C to stop
```

**Access the Application:**
- Open your web browser
- Navigate to: **http://localhost:8081**
- You should see the chat interface with an integrated map

---

### **Method 2: Using the Development Script**

For repeated development sessions, use the convenience script:

```bash
# Step 1: Make the script executable (first time only)
chmod +x devserver.sh

# Step 2: Run the development server
./devserver.sh
```

This script automatically:
- Activates the virtual environment
- Checks for required dependencies
- Starts the Flask server using `run_app.py`
- Displays startup information

---

### **Method 3: Docker Deployment**

For production or isolated environments:

```bash
# Step 1: Build the Docker image
docker-compose build

# Step 2: Start the container
docker-compose up

# Step 3: Access at http://localhost:8081
```

**To stop:**
```bash
docker-compose down
```

---

### **Method 4: Production Mode**

For deployment to a server:

```bash
# Step 1: Set production environment
export FLASK_ENV=production
export FLASK_DEBUG=0

# Step 2: Install production server (gunicorn)
pip install gunicorn

# Step 3: Run with gunicorn using the new app location
gunicorn -w 4 -b 0.0.0.0:8081 'src.api.app:app'
```

**Explanation:**
- `-w 4`: Use 4 worker processes
- `-b 0.0.0.0:8081`: Bind to all interfaces on port 8081
- `'src.api.app:app'`: Application entry point (new location after reorganization)

---

### **Verification Steps**

After starting the application, verify it's working correctly:

#### **1. Check System Status**
```bash
curl http://localhost:8081/system/status
```

**Expected Response:**
```json
{
  "status": "healthy",
  "rag_system": {
    "initialized": true,
    "total_images": 3,
    "cache_available": true
  },
  "gemini_api": "connected",
  "timestamp": "2025-11-20T12:00:00"
}
```

#### **2. Test Navigation API**
```bash
curl -X POST http://localhost:8081/api/navigation/parse \
  -H "Content-Type: application/json" \
  -d '{"message": "Navigate from Room 1003 to Room 1018"}'
```

#### **3. Test Chat Endpoint**
```bash
curl -X POST http://localhost:8081/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Where is the main office?"}'
```

#### **4. Check Image Status**
```bash
curl http://localhost:8081/images/status
```

---

### **Stopping the Application**

**For local development:**
- Press `Ctrl+C` in the terminal running the server

**For Docker:**
```bash
docker-compose down
```

**For background processes:**
```bash
# Find the process
ps aux | grep main.py

# Kill the process
kill <PID>
```

---

## 🔧 Running Individual Components

This section explains how to run specific parts of the system independently for development or testing after the reorganization.

---

### **Component 1: D2L Scraper (Announcements)**

The D2L scraper extracts course announcements from Brightspace/D2L.

#### **Setup D2L Credentials**

First, add your credentials to `.env`:
```bash
D2L_USERNAME=your_email@fanshaweonline.ca
D2L_PASSWORD=your_password
```

#### **Run the Announcements Pipeline**

**Option 1: Using the Pipeline Script (Recommended)**
```bash
# Automated script that checks dependencies and runs the pipeline
./run_announcements_pipeline.sh
```

This script will:
- ✅ Check and activate virtual environment
- ✅ Verify .env file exists with credentials
- ✅ Ensure Playwright is installed
- ✅ Run the announcements scraper
- ✅ Save output to `src/data/announcements/all_announcements.json`
- ✅ Display summary with total announcements count

**Option 2: Manual Execution**
```bash
# Step 1: Activate virtual environment
source .venv/bin/activate

# Step 2: Install Playwright browsers (first time only)
python -m playwright install firefox

# Step 3: Run the scraper directly
python -m src.scrapers.d2l.announcements
```

#### **Expected Behavior:**
1. Opens Firefox browser (visible, not headless)
2. Navigates to D2L login page
3. Prompts for Microsoft SSO authentication
4. **If 2FA is required**: Displays verification code in terminal
5. Navigates to course pages
6. Extracts the 5 most recent announcements
7. **Saves to**: `src/data/announcements/all_announcements.json` (centralized path)

#### **Output Structure:**
```json
{
  "total_announcements": 5,
  "successful": 5,
  "failed": 0,
  "course": "INFO-6156-(01)-25F",
  "extracted_at": "2025-12-08T18:36:31.458370",
  "announcements": [
    {
      "index": 1,
      "title": "Sprint 4 Presentation - reg",
      "date": "Dec 1, 2025 9:20 PM",
      "url": "https://www.fanshaweonline.ca/d2l/le/news/...",
      "content": "Announcement content here...",
      "content_length": 373
    }
  ]
}
```

#### **Chatbot Integration:**
After running the pipeline, the chatbot automatically reads from the same location:
```
User: "What are the recent D2L announcements?"
Bot: [Lists announcements from src/data/announcements/all_announcements.json]
```

**Configuration:** All paths are centralized in `src/config/paths.py` to ensure consistency between the pipeline and chatbot.

---

### **Component 2: SharePoint Events Scraper (NEW)**

The SharePoint scraper extracts campus events from Fanshawe's SharePoint Modern Events page.

#### **Run the SharePoint Scraper**

```bash
# Step 1: Activate virtual environment
source .venv/bin/activate

# Step 2: Run the scraper using the wrapper script
python extract_sharepoint_events.py

# Or run directly from new location:
python -m src.scrapers.sharepoint.events

# With date range (optional):
python extract_sharepoint_events.py --start-date 2024-11-01 --end-date 2024-12-31
```

**Expected Behavior:**
1. Opens Firefox browser with Playwright
2. Handles Microsoft SSO authentication
3. Supports 2FA verification if required
4. Navigates to SharePoint Events page
5. Extracts event details (title, date, location, description)
6. Saves to `data/sharepoint_events/events_YYYYMMDD_HHMMSS.json`

**Output Structure:**
```json
{
  "metadata": {
    "source": "SharePoint Modern Events",
    "scraped_at": "2024-11-22T14:47:16",
    "total_events": 15,
    "date_range": "2024-11-01 to 2024-12-31"
  },
  "events": [
    {
      "title": "Open House - November 29",
      "date": "Nov 29, 2024",
      "location": "Campus",
      "description": "Join us for our Open House..."
    }
  ]
}
```

---

### **Component 3: Professor Information Scraper (NEW)**

Extracts professor contact information and office hours from D2L course pages.

#### **Run the Professor Scraper**

```bash
# Step 1: Activate virtual environment
source .venv/bin/activate

# Step 2: Run the scraper using the wrapper script
python extract_professor_info.py

# Or run directly from new location:
python -m src.scrapers.d2l.professor_info

# For a specific course:
python extract_professor_info.py --course-id 2001540
```

**Expected Behavior:**
1. Authenticates with D2L
2. Navigates to course homepage
3. Extracts professor information from content sections
4. Saves to `data/course_XXXXXX/professor_info.json`

**Output File Structure:**
```json
[
  {
    "course": "Course Name",
    "title": "Announcement Title",
    "content": "Full announcement text...",
    "date": "2025-11-20",
    "url": "https://..."
  }
]
```

#### **Transform Announcements**

Convert raw scraper output to processed format:

```bash
# This runs automatically via API, but you can test manually:
python -m src.services.announcement_transformer
```

**Or via API:**
```bash
curl -X POST http://localhost:8081/api/announcements/refresh
```

---

### **Component 4: RAG System (Image Embeddings)**

The RAG system processes floor plan images and creates searchable embeddings.

#### **Update Image Embeddings**

```bash
# Step 1: Activate virtual environment
source .venv/bin/activate

# Step 2: Run the embedding update script
python update_embeddings.py
```

**What this does:**
- Scans `images/` folder for floor plan images
- Generates image embeddings using Vertex AI
- Creates text descriptions using Gemini Vision
- Generates text embeddings for descriptions
- Caches everything to `image_metadata_cache.pkl`

**Expected Output:**
```
🚀 EMBEDDING UPDATE SCRIPT
==================================================
📦 Importing RAG system...
✅ Multimodal RAG system available
🔄 Initializing RAG models...
✅ Embedding models loaded

📊 INITIAL STATUS:
- Initialized: True
- Total Images: 3
- RAG Available: True

🔄 METHOD 1: Direct Update
Processing images...
  ✅ M1.jpeg
  ✅ M2.jpeg
  ✅ M3.jpeg
✅ Direct update successful

🎉 SCRIPT COMPLETED SUCCESSFULLY!
```

#### **Clear Image Cache**

```bash
# Via API
curl -X POST http://localhost:8081/images/clear-cache

# Via Python
python -c "from main import image_manager; image_manager.clear_cache()"
```

#### **Monitor Images (Auto-Update)**

Enable automatic embedding updates when images change:

```bash
# Start auto-monitoring (via API while server is running)
curl -X POST http://localhost:8081/images/auto-monitor/start

# Check status
curl http://localhost:8081/images/auto-monitor/status

# Stop monitoring
curl -X POST http://localhost:8081/images/auto-monitor/stop
```

---

### **Component 5: Navigation System**

Test the navigation and pathfinding system independently.

#### **Test Room Resolution**

```bash
# Test with the updated import path
python << 'EOF'
import sys
sys.path.insert(0, '.')
from src.api.app import resolve_room_name

print(resolve_room_name('1003'))           # Should return 'Room_1003'
print(resolve_room_name('bathroom men'))   # Should return 'Bathroom-Men'
EOF
```

#### **Test Navigation Parsing**

```bash
python << 'EOF'
import sys
sys.path.insert(0, '.')
from src.api.app import parse_navigation_request

result = parse_navigation_request('Navigate from Room 1003 to Room 1018')
print(f"Is Navigation: {result['is_navigation']}")
print(f"Start: {result['start']} → Node: {result['startNode']}")
print(f"End: {result['end']} → Node: {result['endNode']}")
EOF
```

#### **Test Map API Endpoints**

```bash
# Get all rooms
curl http://localhost:8081/api/navigation/rooms

# Get room centers (manual overrides)
curl http://localhost:8081/api/navigation/room-centers

# Parse navigation request
curl -X POST http://localhost:8081/api/navigation/parse \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I get to the main office from room 1003?"
  }'

# Navigation from map clicks
curl -X POST http://localhost:8081/api/navigation/from-clicks \
  -H "Content-Type: application/json" \
  -d '{
    "startRoom": "Room_1003",
    "endRoom": "Room_1018"
  }'
```

---

### **Component 6: Gemini AI Integration**

Test the Gemini AI models independently.

#### **Test Intent Classification**

```bash
python << 'EOF'
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.5-pro')

queries = [
    "Navigate to room 1003",
    "What events are happening today?",
    "Where can I eat lunch?",
    "Show me D2L announcements"
]

for query in queries:
    response = model.generate_content(f"Classify this query intent: {query}")
    print(f"Query: {query}")
    print(f"Intent: {response.text}\n")
EOF
```

#### **Test Image Understanding**

```bash
python << 'EOF'
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.0-flash')
image = Image.open('images/M1.jpeg')

response = model.generate_content([
    "Describe this floor plan in detail. Identify rooms, corridors, and landmarks.",
    image
])

print(response.text)
EOF
```

---

### **Component 7: Map Visualization**

The map component runs entirely in the browser, but you can test it independently.

#### **Open Map Testing Tool**

```bash
# Start a simple HTTP server
python -m http.server 8000

# Navigate to:
# http://localhost:8000/tools/find_room_centers.html
```

This tool allows you to:
- Click on rooms to see their SVG coordinates
- Visualize room centers
- Test coordinate transformations
- Export room center configurations

#### **Test Map Controller (Browser Console)**

Open the application at `http://localhost:8081` and open browser DevTools (F12):

```javascript
// Check navigation state
console.log(navigationState);

// Check graph data
console.log(currentGraphData);

// Test coordinate conversion
const testCoords = svgCoordsToLatLng(250, 600, currentSvgMap, currentCorners);
console.log('Converted coordinates:', testCoords);

// Find shortest path
const path = findShortestPath(currentGraphData.graph, "M1_6", "M1_8");
console.log('Path:', path);

// Get room center
const center = getRoomCenterFromSVG("Room_1003", currentSvgMap, currentCorners);
console.log('Room center:', center);
```

---

### **Component 8: Event and Restaurant Queries**

Test the JSON database query system.

#### **Query Events**

```bash
python << 'EOF'
import json
from datetime import datetime

# Load events database
with open('data/campus_events.json', 'r') as f:
    events = json.load(f)

# Filter today's events
today = datetime.now().strftime('%Y-%m-%d')
today_events = [e for e in events if e.get('date') == today]

print(f"Events today ({today}):")
for event in today_events:
    print(f"  - {event['name']} at {event['time']} in {event['location']}")
EOF
```

#### **Query Restaurants**

```bash
python << 'EOF'
import json

# Load restaurants database
with open('data/campus_restaurants.json', 'r') as f:
    restaurants = json.load(f)

print("Campus Restaurants:")
for restaurant in restaurants:
    print(f"\n{restaurant['name']}")
    print(f"  Location: {restaurant['location']}")
    print(f"  Hours: {restaurant['hours']}")
    print(f"  Payment: {', '.join(restaurant['payment_methods'])}")
EOF
```

#### **Via API**

```bash
# Query events
curl -X POST http://localhost:8081/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What events are happening today?"}'

# Query restaurants
curl -X POST http://localhost:8081/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Where can I eat on campus?"}'
```

---

### **Component 9: System Health Monitoring**

Monitor system health and performance.

#### **Check System Status**

```bash
curl http://localhost:8081/system/status | python -m json.tool
```

**Response includes:**
- RAG system status
- Image count
- Gemini API connectivity
- Configuration status
- Timestamp

#### **Check Image Processing Status**

```bash
curl http://localhost:8081/images/status | python -m json.tool
```

**Response includes:**
- Total images processed
- Cache availability
- Last update timestamp
- Auto-monitoring status

#### **Run Health Check Script**

```bash
python << 'EOF'
import requests

def check_health():
    endpoints = [
        ('System Status', 'http://localhost:8081/system/status'),
        ('Image Status', 'http://localhost:8081/images/status'),
        ('Room List', 'http://localhost:8081/api/navigation/rooms')
    ]

    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            status = '✅' if response.status_code == 200 else '❌'
            print(f"{status} {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")

check_health()
EOF
```

---

### **Updating Image Embeddings**
```bash
# Run the embedding update script
python update_embeddings.py

# Or using uv
uv run python update_embeddings.py
```

The `update_embeddings.py` script provides comprehensive testing and management of the embedding system:

#### **What the Script Does:**
- **Tests all embedding update methods** (direct, HTTP endpoints, cache management)
- **Validates system functionality** and reports detailed status
- **Processes all images** in the `images/` folder and generates embeddings
- **Provides usage examples** for different embedding update approaches

#### **Script Output:**
```
🚀 SCRIPT DE ATUALIZAÇÃO DE EMBEDDINGS
==================================================
📦 Importando sistema...
✅ Sistema RAG multimodal disponível
🔄 Inicializando modelos RAG...
✅ Modelos de embedding carregados

📊 STATUS INICIAL:
- Initialized: True
- Total Images: 3
- RAG Available: True

🔄 MÉTODO 1: Atualização Direta
✅ Atualização direta bem-sucedida

🔄 MÉTODO 2: Atualização via Endpoint
✅ Endpoint de atualização funcionando

🔄 MÉTODO 3: Limpeza de Cache
✅ Cache limpo com sucesso

🎉 SCRIPT EXECUTADO COM SUCESSO!
✅ Todos os métodos de atualização funcionando
```

#### **When to Use:**
- **Initial setup**: After adding new images to the `images/` folder
- **System validation**: To verify embedding system is working correctly
- **Troubleshooting**: When experiencing issues with image processing
- **Cache management**: To clear and regenerate embeddings

## 💻 Usage Examples

### **Basic Navigation Queries**
```
User: "How do I get to room 1033 from the main entrance?"
AI: "To reach Room 1033 (Main Office) from the South Entrance:
     1. Enter through the south doors
     2. Walk straight north, down the main hallway
     3. Continue past all the classrooms and labs
     4. The Main Office (1033) will be on your right in the north-east corner"
```

### **Complex Queries with Visual Context**
```
User: "What's the best way to get to the elevator from room 1015?"
AI: "Based on the building layout, here's how to reach the elevator from Room 1015:
     1. Exit Room 1015 (west side of main hall)
     2. Turn right and walk north toward the stairs
     3. The elevator is located just south of the stairs, on your right
     4. Total walking distance: approximately 50 meters"
```

### **Room Information Queries**
```
User: "What rooms are available on this floor?"
AI: "The M1 Blue Building main floor includes:
     • Classrooms: 1003, 1004, 1006, 1013-1016
     • Computer Labs: 1020, 1022, 1024, 1026
     • Main Office: 1033
     • Facilities: Elevator, Stairs, Washrooms
     • Connected to Building H via hallway"
```

## � Modular Architecture

### **Config Module** (`src/config/`)
Manages environment configuration and system settings:
- **environment.py**: Handles environment variables and configuration loading
- **settings.py**: RAG system configuration and model parameters

### **Models Module** (`src/models/`)
Wraps AI model interfaces:
- **embedding_models.py**: Sentence Transformer and embedding generation
- **gemini_models.py**: Google Gemini API integration

### **Services Module** (`src/services/`)
Implements business logic and services:
- **initialization_service.py**: Model initialization and setup
- **validation_service.py**: Input/output validation

### **Utils Module** (`src/utils/`)
Provides utility functions and validators:
- **validators.py**: Data validation and sanitization

## �🔧 API Endpoints

### **Chat Interface**
- **POST** `/chat` - Send messages to the AI navigator
- **GET** `/` - Main chat interface

### **System Status**
- **GET** `/system/status` - Complete system status
- **GET** `/images/status` - Image processing status

### **Image Management**
- **POST** `/images/update` - Update image embeddings
- **POST** `/images/clear-cache` - Clear embedding cache
- **POST** `/images/auto-monitor/start` - Start auto-monitoring
- **POST** `/images/auto-monitor/stop` - Stop auto-monitoring
- **GET** `/images/auto-monitor/status` - Monitor status

## 🏗️ Project Structure

```
Capstone_Project_AIM/
├── 📁 docs/                         # Documentation (organized by category)
│   ├── 📁 architecture/             # Architecture decisions & diagrams
│   │   ├── PROFESSOR_ARCHITECTURE_VISUAL.md
│   │   ├── REORGANIZATION_PLAN.md
│   │   └── REORGANIZATION_SUMMARY.md
│   ├── 📁 guides/                   # User guides & tutorials
│   │   ├── ANNOUNCEMENTS_INTEGRATION.md
│   │   ├── QUICK_START_ANNOUNCEMENTS.md
│   │   ├── PROFESSOR_EXTRACTION_GUIDE.md
│   │   └── ... (8 total guide files)
│   ├── 📁 scraping/                 # Scraper documentation
│   │   ├── D2L_AGENT_INTEGRATION.md
│   │   ├── D2L_SCRAPER_README.md
│   │   └── sharepoint_scraper.md
│   └── 📁 api/                      # API documentation (future)
├── 📁 src/                          # Modular source code
│   ├── 📁 api/                      # Flask application
│   │   ├── app.py                   # Main Flask server (was main.py)
│   │   └── routes/                  # Route modules (future split)
│   ├── 📁 scrapers/                 # Data extraction modules
│   │   ├── 📁 d2l/                  # D2L/Brightspace scrapers
│   │   │   ├── announcements.py     # Course announcements
│   │   │   ├── content_home.py      # Course content
│   │   │   ├── professor_info.py    # Professor information
│   │   │   ├── announcement_content.py
│   │   │   └── links_crawler.py
│   │   ├── 📁 sharepoint/           # SharePoint scrapers
│   │   │   └── events.py            # Campus events
│   │   └── 📁 utils/                # Shared scraping utilities
│   ├── 📁 models/                   # ML models and embeddings
│   │   ├── embedding_models.py      # Sentence Transformer wrapper
│   │   └── gemini_models.py         # Gemini model manager
│   ├── 📁 services/                 # Business logic
│   │   ├── initialization_service.py
│   │   ├── validation_service.py
│   │   ├── announcement_transformer.py
│   │   └── d2l_scraper.py
│   ├── 📁 config/                   # Configuration management
│   │   ├── environment.py
│   │   └── settings.py
│   └── 📁 utils/                    # General utilities
│       └── validators.py
├── 📁 scripts/                      # Utility scripts (organized)
│   ├── 📁 debug/                    # Debugging tools
│   │   ├── debug_announcement.py
│   │   ├── debug_login_page.py
│   │   ├── debug_sharepoint_page.py
│   │   └── demo_auto_update.py
│   ├── 📁 processing/               # Data processing
│   │   ├── process_course.py
│   │   ├── transform_cache.py
│   │   └── update_embeddings.py
│   ├── 📁 generation/               # Code/data generation
│   │   ├── generate_route_templates.py
│   │   ├── generate_route_viewer.py
│   │   └── parse_news_html.py
│   └── 📁 diagnostics/              # System diagnostics
│       ├── diagnose_routes.py
│       ├── check_map_routes.py
│       ├── list_routes.py
│       ├── suggest_next_routes.py
│       └── validate_map_embeddings.py
├── 📁 tests/                        # Comprehensive test suite
│   ├── 📁 unit/                     # Unit tests
│   ├── 📁 integration/              # Integration tests
│   ├── 📁 integration_root/         # Root-level integration tests
│   ├── 📁 system/                   # System tests
│   ├── 📁 performance/              # Performance tests
│   └── conftest.py                  # Pytest configuration
├── 📁 templates/                    # HTML templates
│   └── index.html                   # Main chat interface
├── 📁 static/                       # Static web assets
│   ├── style.css                    # Application styling
│   ├── script.js                    # Frontend JavaScript
│   └── map-controller.js            # Map & navigation logic
├── 📁 data/                         # Data files & databases
│   ├── campus_events.json
│   ├── campus_restaurants.json
│   ├── d2l_announcements.json
│   ├── 📁 course_2001539/           # Course-specific data
│   ├── 📁 course_2001540/
│   └── 📁 sharepoint_events/        # SharePoint events cache
├── 📁 config/                       # Configuration files
│   ├── building_m_rooms.json
│   └── pytest.ini
├── 📁 images/                       # Building floor plans
│   ├── M1.jpeg
│   ├── M2.jpeg
│   └── M3.jpeg
├── 📁 LeafletJS/                    # Map assets
│   └── Floorplans/Building M/
│       ├── M1_official.svg
│       └── building_m_floor1_navigation.json
├── run_app.py                       # Main application entry point (NEW)
├── devserver.sh                     # Development server script
├── extract_all_announcements.py     # Wrapper for D2L scraper
├── extract_sharepoint_events.py     # Wrapper for SharePoint scraper
├── extract_professor_info.py        # Wrapper for professor scraper
├── multimodal_rag_complete.py       # RAG system implementation
├── update_embeddings.py             # Embedding update script
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project configuration
└── README.md                        # This file
```

### **Architecture Highlights**

#### **Feature-Based Organization**
- **docs/**: All documentation organized by purpose (architecture, guides, scraping)
- **src/**: All source code organized by feature (api, scrapers, models, services)
- **scripts/**: Utility scripts organized by function (debug, processing, generation, diagnostics)
- **tests/**: Tests organized by type (unit, integration, system, performance)

#### **Backward Compatibility**
- Wrapper scripts in root maintain old import paths
- `run_app.py` replaces `main.py` as entry point
- `devserver.sh` updated to use new structure
- Git history preserved for all moved files

#### **Benefits**
- ✅ Clean root directory (10 essential files vs. 80+)
- ✅ Clear separation of concerns
- ✅ Easy navigation and discovery
- ✅ Modular and maintainable
- ✅ Ready for team collaboration

## 🔍 System Components

### **1. Flask Web Application (`main.py`)**
- **Chat Interface**: Handles user interactions
- **Image Management**: Processes and manages building images
- **Auto-Monitoring**: Watches for new images and updates embeddings
- **API Endpoints**: RESTful API for system control

### **2. RAG System (`multimodal_rag_complete.py`)**
- **Multimodal Processing**: Handles both text and image inputs
- **Embedding Generation**: Creates vector representations
- **Similarity Search**: Finds relevant information
- **Contextual Analysis**: Combines multiple data sources

### **3. AI Models Integration**
- **Gemini Models**: Text and multimodal understanding
- **Embedding Models**: Vector generation for search
- **Vertex AI**: Cloud-based AI services

### **4. Embedding Management (`update_embeddings.py`)**
- **Comprehensive Testing**: Validates all embedding update methods
- **System Validation**: Checks RAG system functionality and status
- **Cache Management**: Handles embedding cache operations
- **Usage Examples**: Provides documentation for different update approaches
- **Error Handling**: Robust error reporting and troubleshooting

## 💻 Main Application Scripts

### **1. main.py** - Core Flask Application Server

**Purpose**: Main web server orchestrating all system components

**Location**: Now at `src/api/app.py` (moved during reorganization, wrapper at `run_app.py`)

**Key Functions**:
```python
# Chat endpoint - handles AI navigation requests
@app.route("/chat", methods=['POST'])
def chat():
    # Parses navigation requests using Gemini
    # Resolves room names via aliases
    # Finds relevant images using RAG
    # Generates AI responses with context
    # Returns: { reply: HTML, mapAction: navigation_data }

# Navigation parsing - extracts start/end from natural language
def parse_navigation_request(user_message: str):
    # Uses Gemini to parse: "go from X to Y"
    # Returns: { is_navigation, start, end, startNode, endNode }

# Room resolution - handles aliases and mappings
def resolve_room_name(room_name: str):
    # Normalizes input: "1003" → "Room_1003"
    # Checks aliases: "bathroom men" → "Bathroom-Men"
    # Returns official room ID

# API: Navigation from map clicks
@app.route("/api/navigation/from-clicks", methods=['POST'])
def api_navigation_from_clicks():
    # Receives: { startRoom, endRoom }
    # Generates walking directions
    # Returns: { reply, path }

# API: Room center configuration
@app.route("/api/navigation/room-centers", methods=['GET'])
def api_get_room_centers():
    # Returns manual room center overrides
    # Used by map controller for precise positioning
```

**Image Management System**:
- `AdvancedImageManager`: Handles image processing and embeddings
- `AutoImageUpdater`: Monitors file system for new images
- File watcher with 5-second debounce to avoid duplicate processing

**Configuration Loading**:
- `building_m_rooms.json`: Room mappings, aliases, centers
- Environment variables: API keys, project settings
- RAG system initialization with model managers

---

### **2. map-controller.js** - Frontend Map & Navigation Logic

**Purpose**: Manages Leaflet map, SVG overlays, and pathfinding

**Core Components**:

#### **Coordinate Transformation**
```javascript
// Converts SVG pixel coordinates to geographic lat/lng
function svgCoordsToLatLng(svgX, svgY, svgMap, corners) {
    // 1. Normalize to 0-1 range within SVG viewBox
    // 2. Bilinear interpolation across rotated corners
    // 3. Account for 21.3° building rotation
    // Returns: L.latLng(lat, lng)
}

// Gets room visual center with priority system
function getRoomCenterFromSVG(roomId, svgMap, corners) {
    // Priority 1: Check manual override from config
    // Priority 2: Calculate from room polygon getBBox()
    // Priority 3: Fallback to corridor node
    // Returns: LatLng coordinates for marker placement
}
```

#### **Navigation Graph & Pathfinding**
```javascript
// Builds graph from SVG nodes and JSON definition
function buildNavigationGraph(svgMap, graphDefinition, corners) {
    // Extracts node positions from SVG by ID
    // Builds adjacency list with distances
    // Creates metadata (room representations)
    // Returns: { graph, nodePositions, nodeMetadata }
}

// Dijkstra's algorithm for shortest path
function findShortestPath(graph, startNode, endNode) {
    // Standard Dijkstra implementation
    // Uses node distances (real-world meters)
    // Returns: Array of node IDs forming path
}

// Visual path rendering
function drawPathOnMap(path, nodePositions, svgMap) {
    // Highlights start node (green)
    // Highlights end node (red)
    // Highlights intermediate nodes (yellow)
    // Updates SVG circle styles for visibility
}
```

#### **Room Click Handlers**
```javascript
function handleRoomClick(roomId, graphData, svgMap) {
    // Mode: selecting_start
    //   → Place green marker at room center
    //   → Store start coordinates
    //   → Switch to selecting_end mode
    
    // Mode: selecting_end
    //   → Place red marker at room center
    //   → Calculate shortest path
    //   → Render path on map
    //   → Send navigation request to chat
}
```

#### **Map Initialization Sequence**
1. Create Leaflet map with rotation support (21.3°)
2. Load campus GeoJSON to find Building M bounds
3. Calculate rotated corners for overlay
4. Load SVG floor plan (M1_official.svg)
5. Load manual room centers from API
6. Build navigation graph from node definitions
7. Setup click handlers for all rooms and exits

---

### **3. multimodal_rag_complete.py** - RAG System Implementation

**Purpose**: Multimodal retrieval-augmented generation for image-text search

**Key Functions**:

#### **Image Processing**
```python
def processar_imagens_da_pasta(pasta_imagens, embedding_size=512):
    # For each image in folder:
    #   1. Generate description using Gemini vision
    #   2. Create image embedding (multimodal model)
    #   3. Create text embedding from description
    #   4. Store in pandas DataFrame with metadata
    # Returns: DataFrame with all embeddings and descriptions
```

#### **Similarity Search**
```python
def buscar_imagens_similares_com_embedding(
    user_embedding, 
    image_metadata_df, 
    top_n=3,
    column_name="text_embedding_from_image_description"
):
    # Calculates cosine similarity between:
    #   - User query embedding
    #   - Each image's embedding
    # Returns: Top N most relevant images with scores
```

#### **Embedding Generation**
```python
def get_text_embedding_from_text_embedding_model(text: str):
    # Uses Google's text embedding model
    # Returns: 512-dimensional vector

def get_image_embedding_from_multimodal_embedding_model(image_path):
    # Uses Google's multimodal embedding model
    # Returns: 512-dimensional vector
```

#### **Gemini Response**
```python
def get_gemini_response(user_message, relevant_images):
    # Constructs prompt with:
    #   - User query
    #   - Relevant image descriptions
    #   - Building context (map_info)
    # Sends to Gemini 2.0 Flash
    # Returns: Markdown-formatted response
```

---

### **4. floorPlansScript.js** - Building Data Configuration

**Purpose**: Defines building structure, rooms, and navigation graph

**Structure**:
```javascript
const floorPlans = {
  "Building M": {
    "floors": {
      "floor1": {
        "navigationGraph": {
          // Node definitions with connections
          "M1_6": {
            "connections": ["M1_5", "M1_7"],
            "represents": { 
              type: "room", 
              id: "Room_1003" 
            }
          },
          // ... more nodes
        },
        
        "objects": {
          "rooms": {
            "Room_1003": ["Door_1003_1"],
            // Room IDs map to door element IDs in SVG
          },
          "exits": {
            "Outside-Exit_1": []
          }
        }
      }
    }
  }
}
```

**Navigation Graph Logic**:
- **Nodes**: Represent corridor positions, room entrances, intersections
- **Connections**: Define walkable paths between nodes
- **Represents**: Links nodes to rooms, stairs, elevators, exits
- **Distance Calculation**: Uses Euclidean distance between node coordinates

---

### **5. building_m_rooms.json** - Configuration Data

**Purpose**: Room mappings, aliases, and manual coordinate overrides

**Structure**:
```json
{
  "Building M": {
    "aliases": {
      "1003": "Room_1003",
      "bathroom men": "Bathroom-Men"
    },
    
    "roomToNode": {
      "Room_1003": "M1_6",
      "Room_1018": "M1_8"
    },
    
    "roomCentersSVG": {
      "_comment": "Manual overrides in SVG coordinates",
      "Room_1003": { "x": 250.5, "y": 600.3 },
      "Room_1004": {}  // Empty = auto-calculate
    },
    
    "roomDescriptions": {
      "Room_1003": "Room 1003 - Computer Lab"
    }
  }
}
```

**Usage Flow**:
1. User types: "go to 1003"
2. System checks `aliases`: "1003" → "Room_1003"
3. System checks `roomToNode`: "Room_1003" → "M1_6"
4. System checks `roomCentersSVG`: Gets precise center or calculates
5. System uses node "M1_6" for pathfinding, center for marker

---

### **6. update_embeddings.py** - Embedding Management & Testing

**Purpose**: Comprehensive testing and updating of image embeddings

**Location**: Root directory (can also be found in `scripts/processing/update_embeddings.py`)

**Functionality**:
```python
# Tests three update methods:

# Method 1: Direct API call
image_manager.update_embeddings(force_reprocess=True)

# Method 2: HTTP endpoint
requests.post('http://localhost:8081/images/update')

# Method 3: Cache management
image_manager.clear_cache()
image_manager.initialize()

# Provides detailed status reporting:
# - Number of images processed
# - Embedding generation success
# - Cache status
# - RAG system availability
```

**When to Run**:
- After adding new images to `images/` folder
- When experiencing image processing issues
- For system validation and troubleshooting
- To regenerate embeddings with new models

---

## 🔄 Complete Navigation Flow

### **Scenario: User asks "Navigate from Room 1003 to Room 1018"**

```
1. USER INPUT (Chat)
   ├─► User types: "Navigate from Room 1003 to Room 1018"
   └─► Submitted via fetch('/chat', { message })

2. BACKEND PARSING (main.py - chat())
   ├─► parse_navigation_request(message)
   │   ├─► Gemini extracts: start="1003", end="1018"
   │   ├─► resolve_room_name("1003") → "Room_1003"
   │   ├─► resolve_room_name("1018") → "Room_1018"
   │   └─► roomToNode mapping: Room_1003→M1_6, Room_1018→M1_8
   │
   ├─► image_manager.find_relevant_images(message)
   │   ├─► Generate embedding from query
   │   ├─► Search similar images (cosine similarity)
   │   └─► Return top 2 relevant floor plan images
   │
   └─► model.generate_content(prompt + image_context)
       └─► Gemini generates walking directions

3. RESPONSE TO FRONTEND
   └─► JSON: {
       reply: "Turn right from Room 1003...",
       mapAction: {
         type: "SHOW_ROUTE",
         startNode: "M1_6",
         endNode: "M1_8",
         startRoom: "Room_1003",
         endRoom: "Room_1018"
       }
     }

4. FRONTEND MAP RENDERING (map-controller.js)
   ├─► showRouteBuildingM(M1_6, M1_8)
   │   ├─► findShortestPath(graph, M1_6, M1_8)
   │   │   └─► Dijkstra: [M1_6, M1_5, M1_4, M1_Int_1, M1_Turn_1, M1_8]
   │   │
   │   ├─► drawPathOnMap(path, nodePositions, svgMap)
   │   │   ├─► Highlight M1_6 (green)
   │   │   ├─► Highlight M1_8 (red)
   │   │   └─► Highlight intermediate nodes (yellow)
   │   │
   │   ├─► getRoomCenterFromSVG("Room_1003")
   │   │   ├─► Check manual override in config
   │   │   └─► Or calculate from room polygon
   │   │
   │   ├─► Place green marker at Room_1003 center
   │   ├─► Place red marker at Room_1018 center
   │   └─► map.fitBounds([startCoords, endCoords])
   │
   └─► Display chat message with walking directions

5. USER SEES
   ├─► Chat: "Turn right from Room 1003, walk 50m..."
   ├─► Map: Visual path highlighted on floor plan
   ├─► Markers: Green (start) and Red (end) at room centers
   └─► Animation: Map auto-zooms to show full route
```

---

## 🧪 Testing

### **Run All Tests**
```bash
python -m pytest tests/ -v
```

### **Run Specific Test Categories**
```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# System tests
python -m pytest tests/system/ -v
```

### **Performance Tests**
```bash
python tests/performance/test_models_simulation.py
```

## 🐛 Troubleshooting Guide

This comprehensive troubleshooting section helps you resolve common issues.

---

### **Issue 1: Gemini API Key Not Working**

**Symptoms:**
- Error: `API key not found`
- Error: `google.api_core.exceptions.PermissionDenied: 403`
- Chatbot not responding

**Solutions:**

#### **Step 1: Verify API Key is Set**
```bash
# Check environment variable
echo $GEMINI_API_KEY

# Check .env file
cat .env | grep GEMINI_API_KEY
```

#### **Step 2: Validate API Key Format**
```bash
# Gemini API keys should start with 'AIza'
# Example: AIzaSyBHNDh4x8KDtw_O9HtHTtaZXeZV2Ihq9MA

# Test API key
python << 'EOF'
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ API key not found in environment")
elif not api_key.startswith('AIza'):
    print("❌ Invalid API key format")
else:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content("Say hello")
        print("✅ API key is valid!")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ API key test failed: {e}")
EOF
```

#### **Step 3: Regenerate API Key**
1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. Update `.env` file with the new key
4. Restart the application

---

### **Issue 2: Google Cloud Authentication Errors**

**Symptoms:**
- Error: `Could not automatically determine credentials`
- Error: `Application Default Credentials are not available`
- RAG system not initializing

**Solutions:**

#### **Step 1: Install Google Cloud SDK**
```bash
# Check if gcloud is installed
which gcloud

# If not installed, download from:
# https://cloud.google.com/sdk/docs/install
```

#### **Step 2: Authenticate**
```bash
# Login to Google Cloud
gcloud auth application-default login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Verify authentication
gcloud auth application-default print-access-token
```

#### **Step 3: Enable Required APIs**
```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Generative Language API
gcloud services enable generativelanguage.googleapis.com

# Verify enabled services
gcloud services list --enabled | grep -E "aiplatform|generativelanguage"
```

#### **Step 4: Create Service Account (Alternative)**
```bash
# Create service account
gcloud iam service-accounts create fanshawe-navigator \
  --display-name="Fanshawe Navigator Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:fanshawe-navigator@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create credentials.json \
  --iam-account=fanshawe-navigator@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Update .env
echo "GOOGLE_APPLICATION_CREDENTIALS=./credentials.json" >> .env
```

---

### **Issue 3: Image Processing Failures**

**Symptoms:**
- Error: `No images found in images/`
- Error: `Failed to generate embeddings`
- RAG system returns empty results

**Solutions:**

#### **Step 1: Verify Images Exist**
```bash
# Check images directory
ls -la images/

# Expected output should show .jpeg or .png files:
# M1.jpeg
# M2.jpeg
# M3.jpeg
```

#### **Step 2: Verify Image Format**
```bash
# Check image file types
file images/*

# Expected: JPEG image data or PNG image data
```

#### **Step 3: Clear Cache and Reprocess**
```bash
# Delete existing cache
rm -f image_metadata_cache.pkl

# Restart application (will regenerate embeddings)
python main.py
```

#### **Step 4: Manual Embedding Update**
```bash
# Run update script
python update_embeddings.py

# Check for errors in output
# Expected: "✅ Script executed successfully"
```

#### **Step 5: Test Image Processing**
```bash
python << 'EOF'
from PIL import Image
import os

images_dir = 'images'
for filename in os.listdir(images_dir):
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        filepath = os.path.join(images_dir, filename)
        try:
            img = Image.open(filepath)
            print(f"✅ {filename}: {img.size} {img.mode}")
        except Exception as e:
            print(f"❌ {filename}: {e}")
EOF
```

---

### **Issue 4: Port Already in Use**

**Symptoms:**
- Error: `Address already in use`
- Error: `[Errno 98] Address already in use`
- Application won't start

**Solutions:**

#### **Step 1: Find Process Using Port**
```bash
# Linux/Mac
lsof -i :8081

# Windows
netstat -ano | findstr :8081
```

#### **Step 2: Kill the Process**
```bash
# Linux/Mac
kill -9 <PID>

# Windows
taskkill /PID <PID> /F
```

#### **Step 3: Change Port (Alternative)**
```bash
# Option 1: Update .env file
echo "PORT=8082" >> .env

# Option 2: Run with different port
python main.py --port 8082

# Option 3: Modify main.py temporarily
# Change: app.run(debug=True, host='0.0.0.0', port=8081)
# To:     app.run(debug=True, host='0.0.0.0', port=8082)
```

---

### **Issue 5: D2L Scraper Failures**

**Symptoms:**
- Error: `Playwright executable doesn't exist`
- Error: `Login failed`
- 2FA timeout

**Solutions:**

#### **Step 1: Install Playwright Browsers**
```bash
# Install Firefox (used by scraper)
python -m playwright install firefox

# Verify installation
python -m playwright install --help
```

#### **Step 2: Verify D2L Credentials**
```bash
# Check credentials in .env
cat .env | grep D2L

# Should show:
# D2L_USERNAME=your_email@fanshaweonline.ca
# D2L_PASSWORD=your_password
```

#### **Step 3: Test Login Manually**
```bash
# Run scraper in visible mode (not headless)
python extract_all_announcements.py

# Watch browser window for errors
# Enter 2FA code when prompted
```

#### **Step 4: Increase Timeouts**

Edit `src/scrapers/d2l/announcements.py` (or relevant scraper):
```python
# Find this line:
await page.wait_for_selector('input[type="email"]', timeout=5000)

# Change to:
await page.wait_for_selector('input[type="email"]', timeout=30000)
```

---

### **Issue 6: Map Not Displaying**

**Symptoms:**
- Blank map area
- Error: `Cannot read property 'map' of undefined`
- Floor plan not loading

**Solutions:**

#### **Step 1: Check Browser Console**
```
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for JavaScript errors
```

#### **Step 2: Verify Files Exist**
```bash
# Check map files
ls -la LeafletJS/Floorplans/Building\ M/

# Expected files:
# M1_official.svg
# building_m_floor1_navigation.json
```

#### **Step 3: Check Network Requests**
```
1. Open DevTools → Network tab
2. Refresh page
3. Look for failed requests (red)
4. Common failures:
   - 404: File not found
   - CORS errors: Server configuration issue
```

#### **Step 4: Clear Browser Cache**
```
1. Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
2. Select "Cached images and files"
3. Clear data
4. Refresh page (Ctrl+F5 or Cmd+Shift+R)
```

---

### **Issue 7: Navigation Not Working**

**Symptoms:**
- Clicking rooms does nothing
- No route displayed
- Error: `Graph not initialized`

**Solutions:**

#### **Step 1: Verify Configuration**
```bash
# Check room configuration file
cat config/building_m_rooms.json | python -m json.tool

# Should contain:
# - "aliases"
# - "roomToNode"
# - "roomCentersSVG"
```

#### **Step 2: Test Room Resolution**
```bash
python << 'EOF'
import json

with open('config/building_m_rooms.json', 'r') as f:
    config = json.load(f)

# Test alias lookup
test_aliases = ['1003', '1018', 'bathroom men']
for alias in test_aliases:
    result = config['Building M']['aliases'].get(alias)
    print(f"{alias} → {result}")

# Test node mapping
test_rooms = ['Room_1003', 'Room_1018']
for room in test_rooms:
    node = config['Building M']['roomToNode'].get(room)
    print(f"{room} → {node}")
EOF
```

#### **Step 3: Check Browser Console for Graph Errors**
```javascript
// Open DevTools Console and run:
console.log('Graph Data:', currentGraphData);
console.log('Navigation State:', navigationState);

// Expected output should show:
// - graph: { M1_1: {...}, M1_2: {...}, ... }
// - nodePositions: { M1_1: LatLng(...), ... }
```

---

### **Issue 8: Slow Response Times**

**Symptoms:**
- Chat responses take > 10 seconds
- Navigation requests timeout
- High CPU usage

**Solutions:**

#### **Step 1: Check System Resources**
```bash
# Monitor CPU and memory
top  # Linux/Mac
# or
htop  # if installed

# Look for python processes using high CPU
```

#### **Step 2: Reduce Image Count**
```bash
# Move some images out of images/ folder temporarily
mkdir images_backup
mv images/M2.jpeg images_backup/
mv images/M3.jpeg images_backup/

# Regenerate embeddings with fewer images
python update_embeddings.py
```

#### **Step 3: Enable Caching**
```bash
# Verify cache exists
ls -lh image_metadata_cache.pkl

# If file is very small or missing, regenerate:
rm -f image_metadata_cache.pkl
python update_embeddings.py
```

#### **Step 4: Use Faster Model**

Edit `src/api/app.py` to use faster model:
```python
# Find this line:
model = genai.GenerativeModel('gemini-2.5-pro')

# Change to:
model = genai.GenerativeModel('gemini-2.0-flash')  # Faster
```

---

### **Issue 9: Database/JSON Errors**

**Symptoms:**
- Error: `No such file or directory: 'data/campus_events.json'`
- Error: `JSONDecodeError`
- Events/restaurants not loading

**Solutions:**

#### **Step 1: Verify JSON Files Exist**
```bash
# Check data directory
ls -la data/

# Expected files:
# campus_events.json
# campus_restaurants.json
# d2l_announcements.json
```

#### **Step 2: Validate JSON Syntax**
```bash
# Test each JSON file
python -m json.tool data/campus_events.json > /dev/null && echo "✅ campus_events.json valid"
python -m json.tool data/campus_restaurants.json > /dev/null && echo "✅ campus_restaurants.json valid"
python -m json.tool data/d2l_announcements.json > /dev/null && echo "✅ d2l_announcements.json valid"
```

#### **Step 3: Fix JSON Syntax Errors**
```bash
# Use online JSON validator
# Copy file contents to: https://jsonlint.com/

# Common issues:
# - Missing commas
# - Trailing commas
# - Unescaped quotes
# - Missing brackets
```

---

### **Issue 10: Dependencies Not Installing**

**Symptoms:**
- Error: `No module named 'google.generativeai'`
- Error: `ImportError: cannot import name...`
- `pip install` failures

**Solutions:**

#### **Step 1: Upgrade pip**
```bash
python -m pip install --upgrade pip
```

#### **Step 2: Reinstall Dependencies**
```bash
# Remove existing installations
pip uninstall -y -r requirements.txt

# Clean install
pip install -r requirements.txt
```

#### **Step 3: Check Python Version**
```bash
python --version
# Should be 3.11 or higher

# If lower, install Python 3.11+
# https://www.python.org/downloads/
```

#### **Step 4: Create Fresh Virtual Environment**
```bash
# Deactivate current environment
deactivate

# Remove old environment
rm -rf .venv

# Create new environment
python3.11 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### **General Debugging Tips**

#### **Enable Verbose Logging**
```python
# Add to src/api/app.py at the top:
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### **Test Individual Components**
Use the component testing sections above to isolate issues.

#### **Check System Status Endpoint**
```bash
curl http://localhost:8081/system/status | python -m json.tool
```

#### **Review Application Logs**
```bash
# Run with output redirection
python run_app.py 2>&1 | tee application.log

# Search logs for errors
grep -i error application.log
grep -i exception application.log
```

#### **Test with Minimal Configuration**
```bash
# Create minimal .env file
cat > .env.minimal << 'EOF'
GEMINI_API_KEY=your_key_here
FLASK_ENV=development
FLASK_DEBUG=1
EOF

# Test with minimal config
cp .env .env.backup
cp .env.minimal .env
python run_app.py
```

---

### **Getting Help**

If you're still experiencing issues:

1. **Check Documentation**: 
   - [README.md](README.md) - This file (complete system overview)
   - [REORGANIZATION_SUMMARY.md](docs/architecture/REORGANIZATION_SUMMARY.md) - Project reorganization details
   - [QUICK_START_ANNOUNCEMENTS.md](docs/guides/QUICK_START_ANNOUNCEMENTS.md) - Announcements guide
   - [sharepoint_scraper.md](docs/scraping/sharepoint_scraper.md) - SharePoint scraper guide
   - Other guides in `docs/guides/` and `docs/scraping/`
2. **Review Error Messages**: Copy the full error traceback
3. **Check GitHub Issues**: [Project Repository Issues](https://github.com/BlueDoze/Capstone_Project_AIM/issues)
4. **Contact Support**: Email support with:
   - Python version (`python --version`)
   - OS information (`uname -a` or `systeminfo`)
   - Full error message
   - Steps to reproduce

---

### **Debug Mode**
```bash
# Run with debug output
FLASK_DEBUG=1 python run_app.py

# Or set in .env
echo "FLASK_DEBUG=1" >> .env
python run_app.py
```

## 📊 Performance Metrics

### **Response Times**
- **Simple Queries**: < 2 seconds
- **Complex Navigation**: < 5 seconds
- **Image Processing**: < 10 seconds per image

### **System Capacity**
- **Concurrent Users**: 50+
- **Image Storage**: Unlimited (limited by disk space)
- **Cache Size**: ~1MB per 100 images

## 🔒 Security Considerations

- **API Keys**: Stored in environment variables, never in code
- **Input Validation**: All user inputs are sanitized
- **Rate Limiting**: Consider implementing for production
- **HTTPS**: Use SSL/TLS in production environments

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

## 📝 License

This project is developed for educational purposes as part of the Fanshawe College Capstone Project.

## 🙏 Acknowledgments

- **Google AI**: For Gemini models and Vertex AI platform
- **Fanshawe College**: For providing the project requirements
- **Open Source Community**: For the amazing tools and libraries

---

## � Quick Reference

### **File Locations Summary**

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **Main Server** | `src/api/app.py` | Flask application (was `main.py`) |
| **Entry Point** | `run_app.py` | Application wrapper & launcher |
| **Map Controller** | `static/map-controller.js` | Frontend navigation logic |
| **Chat Interface** | `static/script.js` | Chat UI interaction |
| **RAG System** | `multimodal_rag_complete.py` | Image-text search engine |
| **Floor Plans** | `LeafletJS/Floorplans/Building M/` | SVG maps and navigation data |
| **Configuration** | `config/building_m_rooms.json` | Room mappings and centers |
| **Navigation Graph** | `LeafletJS/floorPlansScript.js` | Building structure definition |
| **Room Center Tool** | `tools/find_room_centers.html` | Visual coordinate finder |
| **D2L Announcements** | `src/scrapers/d2l/announcements.py` | Announcement scraper |
| **SharePoint Events** | `src/scrapers/sharepoint/events.py` | Events scraper |
| **Professor Info** | `src/scrapers/d2l/professor_info.py` | Professor scraper |

### **Key Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main chat interface |
| `/chat` | POST | Send navigation queries |
| `/api/navigation/parse` | POST | Parse navigation request |
| `/api/navigation/from-clicks` | POST | Map-initiated navigation |
| `/api/navigation/rooms` | GET | List all rooms |
| `/api/navigation/room-centers` | GET | Get manual coordinate overrides |
| `/system/status` | GET | Complete system status |
| `/images/status` | GET | Image processing status |
| `/images/update` | POST | Update embeddings |
| `/tools/find_room_centers.html` | GET | Coordinate finder tool |

### **Configuration Keys**

**Environment Variables (`.env`)**:
```bash
GEMINI_API_KEY=your_api_key                    # Required
GOOGLE_CLOUD_PROJECT_ID=your_project_id        # For RAG system
GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json # For Vertex AI
```

**Room Configuration (`config/building_m_rooms.json`)**:
- `aliases`: User-friendly name mappings
- `roomToNode`: Room to navigation node mapping
- `roomCentersSVG`: Manual coordinate overrides (x, y)
- `roomDescriptions`: Human-readable room names
- `navigationInstructions`: Room-specific guidance

### **Navigation Graph Structure**

Each node in the navigation graph has:
```javascript
{
  "connections": ["node_id1", "node_id2"],  // Adjacent nodes
  "represents": {                            // What this node represents
    "type": "room|intersection|stairs|elevator|entrance",
    "id": "Room_1003",                      // Optional: room ID
    "goesTo": ["M2", "M3"]                  // Optional: for stairs/elevator
  }
}
```

### **Coordinate Systems**

| System | Origin | Range | Usage |
|--------|--------|-------|-------|
| **SVG** | Top-left of SVG | 0 to viewBox dimensions | Internal calculations |
| **Normalized** | Top-left | 0.0 to 1.0 | Coordinate transformation |
| **Geographic** | Earth center | Lat/Lng degrees | Leaflet map display |
| **Rotated** | Building center | Lat/Lng adjusted | Aligned with campus |

### **Debug Console Commands**

Open browser console (F12) and try:
```javascript
// Check navigation state
console.log(navigationState);

// Check graph data
console.log(currentGraphData);

// Check manual room centers
console.log(manualRoomCenters);

// Test coordinate conversion
const testCoords = svgCoordsToLatLng(250, 600, currentSvgMap, currentCorners);
console.log(testCoords);

// Find path manually
const path = findShortestPath(currentGraphData.graph, "M1_6", "M1_8");
console.log(path);
```

---

## �📞 Support

For technical support or questions:
- **Email**: [your-email@fanshawe.ca]
- **Project Repository**: https://github.com/BlueDoze/Capstone_Project_AIM
- **Documentation**: 
  - `README.md` - This file (complete system overview)
  - `COORDINATE_FIX_SUMMARY.md` - Coordinate system details
  - `MANUAL_ROOM_CENTERS_GUIDE.md` - Room center configuration
  - `TESTING_GUIDE.md` - Testing procedures
  - `INTEGRATION_SUMMARY.md` - System integration details

---

**Last Updated**: November 22, 2025  
**Version**: 3.0 (Reorganized Architecture + Interactive Navigation System)  
**Status**: ✅ Production Ready

---
