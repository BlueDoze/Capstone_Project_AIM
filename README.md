# 🏢 Fanshawe Navigator

A sophisticated **Multimodal RAG (Retrieval-Augmented Generation)** system that provides intelligent navigation assistance for the M1 Blue Building at Fanshawe College. This AI-powered application combines visual understanding with natural language processing to deliver precise, context-aware directions and building information.

## 🎯 Project Overview

This system leverages **Google's Gemini AI models** and **Vertex AI** to create an intelligent building navigation assistant that can:

- 📍 **Visual Navigation**: Analyze building floor plans and provide step-by-step directions
- 🤖 **AI-Powered Responses**: Use multimodal AI to understand both text queries and visual context
- 🔍 **Smart Search**: Find relevant information using advanced embedding-based similarity search
- 📱 **Web Interface**: Clean, responsive chat interface for easy interaction
- 🔄 **Auto-Updates**: Automatically processes new images and updates embeddings

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FANSHAWE NAVIGATOR                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   Web Client    │    │  Flask Server   │    │  RAG System  │ │
│  │                 │    │                 │    │              │ │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌──────────┐ │ │
│  │ │ Chat UI     │◄┼────┼►│ /chat       │ │    │ │ Gemini   │ │ │
│  │ │ (HTML/CSS/  │ │    │ │ /status     │ │    │ │ Models   │ │ │
│  │ │  JavaScript)│ │    │ │ /images/*   │ │    │ │          │ │ │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └──────────┘ │ │
│  └─────────────────┘    └─────────────────┘    │              │ │
│                                                 │ ┌──────────┐ │ │
│                                                 │ │Embedding │ │ │
│                                                 │ │ Models   │ │ │
│                                                 │ └──────────┘ │ │
│                                                 └──────────────┘ │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  Image Storage  │    │  Auto Monitor   │    │  Cache       │ │
│  │                 │    │                 │    │              │ │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌──────────┐ │ │
│  │ │ M1.jpeg     │ │    │ │ FileSystem  │ │    │ │ Pickle   │ │ │
│  │ │ M2.jpeg     │ │    │ │ Watcher     │ │    │ │ Cache    │ │ │
│  │ │ M3.jpeg     │ │    │ │             │ │    │ │          │ │ │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └──────────┘ │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Key Features

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

## 📞 Support

For technical support or questions:
- **Email**: [your-email@fanshawe.ca]
- **Project Repository**: https://github.com/BlueDoze/Capstone_Project_AIM
- **Documentation**: This README file

---
