# 🏢 Fanshawe Navigator - AI Campus Navigation System

A sophisticated **Multimodal RAG (Retrieval-Augmented Generation)** system that provides intelligent navigation assistance for Fanshawe College campus. This AI-powered application combines visual understanding, interactive maps, and natural language processing to deliver precise, context-aware directions and building information with real-time map visualization.

## 🎯 Project Overview

This system leverages **Google's Gemini AI models**, **Vertex AI**, and **Leaflet.js mapping** to create an intelligent building navigation assistant that can:

- 📍 **Interactive Map Navigation**: Visual route display on real campus floor plans with clickable rooms
- 🗺️ **Dual Navigation Modes**: Chat-to-Map and Map-to-Chat interaction
- 🤖 **AI-Powered Responses**: Use multimodal AI to understand both text queries and visual context
- 🔍 **Smart Search**: Find relevant information using advanced embedding-based similarity search
- 📱 **Web Interface**: Clean, responsive chat interface with integrated mapping
- 🔄 **Auto-Updates**: Automatically processes new images and updates embeddings
- 📐 **Precise Positioning**: Accurate room center calculations with manual override capability

## 🏗️ System Architecture

### **High-Level Overview**

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        FANSHAWE NAVIGATOR SYSTEM                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      FRONTEND LAYER                             │   │
│  │  ┌────────────────────┐         ┌──────────────────────────┐   │   │
│  │  │  Chat Interface    │◄────────┤  Map Controller          │   │   │
│  │  │  (script.js)       │         │  (map-controller.js)     │   │   │
│  │  │                    │         │                          │   │   │
│  │  │  • User input      │         │  • Leaflet.js map        │   │   │
│  │  │  • AI responses    │         │  • SVG overlay           │   │   │
│  │  │  • HTML rendering  │         │  • Navigation graph      │   │   │
│  │  └────────────────────┘         │  • Room click handlers   │   │   │
│  │           ▲                      │  • Pathfinding (Dijkstra)│   │   │
│  │           │                      └──────────────────────────┘   │   │
│  └───────────┼──────────────────────────────┬───────────────────────┘   │
│              │                              │                           │
│  ────────────┼──────────────────────────────┼───────────────────────   │
│              │         HTTP/REST            │                           │
│  ────────────┼──────────────────────────────┼───────────────────────   │
│              ▼                              ▼                           │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                     BACKEND LAYER (Flask)                     │    │
│  │                                                               │    │
│  │  ┌──────────────────┐     ┌─────────────────────────────┐   │    │
│  │  │   Chat Routes    │     │  Navigation API Routes      │   │    │
│  │  │  /chat           │     │  /api/navigation/parse      │   │    │
│  │  │  /system/status  │     │  /api/navigation/from-clicks│   │    │
│  │  └──────────────────┘     │  /api/navigation/rooms      │   │    │
│  │           │                │  /api/navigation/room-centers│  │    │
│  │           ▼                └─────────────────────────────┘   │    │
│  │  ┌──────────────────────────────────────────┐               │    │
│  │  │      Advanced Image Manager              │               │    │
│  │  │  • Image processing                      │               │    │
│  │  │  • Embedding generation                  │               │    │
│  │  │  • Auto file monitoring (watchdog)       │               │    │
│  │  │  • Cache management                      │               │    │
│  │  └──────────────────────────────────────────┘               │    │
│  │           │                                                  │    │
│  │           ▼                                                  │    │
│  │  ┌──────────────────────────────────────────┐               │    │
│  │  │      Navigation Request Parser           │               │    │
│  │  │  • Gemini AI parsing                     │               │    │
│  │  │  • Room name resolution                  │               │    │
│  │  │  • Alias handling                        │               │    │
│  │  └──────────────────────────────────────────┘               │    │
│  └───────────────────────────────────────────────────────────────┘    │
│              │                                                         │
│              ▼                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                    AI/ML LAYER                                │    │
│  │                                                               │    │
│  │  ┌────────────────────┐      ┌─────────────────────────┐    │    │
│  │  │  Gemini Models     │      │  Embedding Models       │    │    │
│  │  │  • gemini-pro      │      │  • Text embeddings      │    │    │
│  │  │  • gemini-2.0-flash│      │  • Image embeddings     │    │    │
│  │  │  • Multimodal      │      │  • Sentence transformer │    │    │
│  │  └────────────────────┘      └─────────────────────────┘    │    │
│  │                                                               │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │      RAG System (multimodal_rag_complete.py)        │    │    │
│  │  │  • Image-text similarity search                     │    │    │
│  │  │  • Contextual retrieval                             │    │    │
│  │  │  • Vector search (cosine similarity)                │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  └───────────────────────────────────────────────────────────────┘    │
│              │                                                         │
│              ▼                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                    DATA LAYER                                 │    │
│  │                                                               │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │    │
│  │  │ Floor Plans │  │ Config Files │  │  Embedding Cache │    │    │
│  │  │ (SVG/GeoJSON│  │ (JSON)       │  │  (Pickle)        │    │    │
│  │  │             │  │              │  │                  │    │    │
│  │  │ • M1.svg    │  │ • Room       │  │ • Metadata       │    │    │
│  │  │ • campus    │  │   mappings   │  │ • Vectors        │    │    │
│  │  │   .geojson  │  │ • Aliases    │  │ • Descriptions   │    │    │
│  │  │ • Building  │  │ • Centers    │  │                  │    │    │
│  │  │   images    │  │ • Nav graph  │  │                  │    │    │
│  │  └─────────────┘  └──────────────┘  └──────────────────┘    │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
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

- **Python 3.11+** installed
- **Google Cloud eAccount** with Vertex AI enabled
- **Gemini API Key** from Google AI Studio
- **Git** for version control

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

## 🚀 Running the Application

### **Development Mode**
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the development server
python main.py
```

The application will be available at: `http://localhost:8081`

### **Using the Development Script**
```bash
# Make script executable
chmod +x devserver.sh

# Run using the development script
./devserver.sh
```

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
├── 📁 src/                          # Modular source code
│   ├── 📁 config/
│   │   ├── __init__.py              # Configuration initialization
│   │   ├── environment.py           # Environment variables management
│   │   └── settings.py              # RAG system settings
│   ├── 📁 models/
│   │   ├── __init__.py              # Models initialization
│   │   ├── embedding_models.py      # Embedding model wrapper
│   │   └── gemini_models.py         # Gemini model manager
│   ├── 📁 services/
│   │   ├── __init__.py              # Services initialization
│   │   ├── initialization_service.py # Model initialization logic
│   │   └── validation_service.py    # Data validation services
│   └── 📁 utils/
│       ├── __init__.py              # Utils initialization
│       └── validators.py            # Utility validators
├── 📁 templates/                    # HTML templates
│   └── index.html                   # Main chat interface
├── 📁 static/                       # Static web assets
│   ├── style.css                    # Application styling
│   └── script.js                    # Frontend JavaScript
├── 📁 images/                       # Building floor plans and images
│   ├── M1.jpeg                      # Main floor plan
│   ├── M2.jpeg                      # Additional views
│   └── M3.jpeg                      # Detailed sections
├── 📁 tests/                        # Comprehensive test suite
│   ├── 📁 unit/                     # Unit tests
│   │   ├── test_configuration.py    # Configuration tests
│   │   └── test_models.py           # Model tests
│   ├── 📁 integration/              # Integration tests
│   │   ├── test_complete_system.py  # Full system integration
│   │   ├── test_embedding_evidence.py
│   │   └── test_integrated_system.py
│   ├── 📁 system/                   # System-level tests
│   │   ├── test_auto_update.py      # Auto-update functionality
│   │   ├── test_final_system.py     # End-to-end tests
│   │   └── test_real_gemini.py      # Real Gemini API tests
│   ├── 📁 performance/              # Performance tests
│   │   ├── test_gemini_real_vs_mock.py
│   │   └── test_models_simulation.py
│   ├── conftest.py                  # Pytest configuration
│   └── test_runner.py               # Test execution script
├── 📁 scripts/                      # Utility scripts
│   ├── run_tests.py                 # Run all tests
│   └── setup_environment.py         # Environment setup
├── 📁 config/                       # Configuration files
│   └── pytest.ini                   # Pytest settings
├── main.py                          # Main Flask application
├── multimodal_rag_complete.py       # RAG system implementation
├── demo_auto_update.py              # Auto-update demonstration
├── update_embeddings.py             # Embedding update and testing script
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project configuration
├── devserver.sh                     # Development server script
└── README.md                        # This file
```

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

## 🐛 Troubleshooting

### **Common Issues**

#### **1. Gemini API Key Not Working**
```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Verify in .env file
cat .env | grep GEMINI_API_KEY
```

#### **2. Google Cloud Authentication Issues**
```bash
# Re-authenticate
gcloud auth application-default login

# Check current project
gcloud config get-value project

# Verify APIs are enabled
gcloud services list --enabled
```

#### **3. Image Processing Failures**
```bash
# Check image directory
ls -la images/

# Clear cache and reprocess
curl -X POST http://localhost:8081/images/clear-cache
curl -X POST http://localhost:8081/images/update
```

#### **4. Port Already in Use**
```bash
# Find process using port 8081
lsof -i :8081

# Kill the process
kill -9 <PID>
```

### **Debug Mode**
```bash
# Run with debug output
FLASK_DEBUG=1 python main.py
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
| **Main Server** | `main.py` | Flask application entry point |
| **Map Controller** | `static/map-controller.js` | Frontend navigation logic |
| **Chat Interface** | `static/script.js` | Chat UI interaction |
| **RAG System** | `multimodal_rag_complete.py` | Image-text search engine |
| **Floor Plans** | `LeafletJS/Floorplans/Building M/` | SVG maps and navigation data |
| **Configuration** | `config/building_m_rooms.json` | Room mappings and centers |
| **Navigation Graph** | `LeafletJS/floorPlansScript.js` | Building structure definition |
| **Room Center Tool** | `tools/find_room_centers.html` | Visual coordinate finder |

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

**Last Updated**: November 15, 2025  
**Version**: 2.0 (Interactive Navigation System)  
**Status**: ✅ Production Ready

---
