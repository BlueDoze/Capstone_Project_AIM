# Capstone Project AIM - Campus Navigation System

A Flask-based web application for Fanshawe College campus navigation assistance using AI-powered document search and vector embeddings.

## Prerequisites

- Python 3.11.10
- `uv` package manager (ultra-fast Python package manager)

## Initial Setup

### 1. Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

### 2. Create Virtual Environment
```bash
uv venv .venv --python 3.11.10
```

### 3. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
uv pip install -r requirements.txt
```

## Running the Application

1. Activate the virtual environment:
```bash
export PATH="$HOME/.local/bin:$PATH"
source .venv/bin/activate
```

2. Run the Flask application:
```bash
python main.py
```

## Project Structure

```
Capstone_Project_AIM/
├── main.py                    # Main Flask application (entry point)
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── .env                       # Environment variables (API keys)
├── .venv/                     # Virtual environment (created by uv)
├── devserver.sh              # Development server script
├── src/                       # Main source code directory
│   ├── __init__.py
│   ├── embeddings/            # Image & PDF embedding modules
│   │   ├── __init__.py
│   │   ├── image_embedder.py  # CLIP & Gemini Vision embeddings
│   │   └── pdf_embedder.py     # PDF text & image processing
│   ├── processing/            # Data processing modules
│   │   ├── __init__.py
│   │   └── pdf_data_processor.py # PDF data processing & chunking
│   ├── database/             # Database modules
│   │   ├── __init__.py
│   │   └── vector_db.py      # ChromaDB vector database operations
│   └── utils/                 # Utility functions
│       └── __init__.py
├── templates/                 # Flask HTML templates
│   └── index.html
├── static/                    # Static web assets
│   ├── style.css
│   └── script.js
├── documents/                 # PDF documents for processing
├── images/                    # Image files (including map.pdf)
│   └── map.pdf               # Campus map for navigation
├── chroma_db/                 # ChromaDB vector database storage
└── test_*/                    # Test database directories
```

## Dependencies

The project uses the following main dependencies:
- **Flask 3.1.2** - Web framework for the application
- **Google Generative AI** - AI integration for natural language processing
- **ChromaDB** - Vector database for document embeddings and search
- **PyMuPDF (fitz)** - PDF processing and text extraction
- **PIL (Pillow)** - Image processing
- **CLIP** - Image embedding models (optional)
- **Python-dotenv** - Environment variable management
- **NumPy** - Numerical computations for embeddings

## Features

- **AI-Powered Navigation**: Uses Google Gemini AI for intelligent campus navigation assistance
- **Vector Search**: ChromaDB integration for semantic search of campus documents
- **PDF Processing**: Automatic processing of campus maps and documents
- **Multi-Modal Embeddings**: Support for both text and image embeddings
- **Real-time Chat**: Interactive chat interface for navigation queries
- **Modular Architecture**: Well-organized codebase with separation of concerns

## API Endpoints

- `GET /` - Main application interface
- `POST /chat` - Chat with the AI navigation assistant
- `POST /search/pdf` - Search PDF documents
- `GET /debug/vector-db` - Debug vector database status

## Environment Setup

Create a `.env` file in the project root with the following variables:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

## Development

The virtual environment is configured with Python 3.11.10 and includes all necessary development tools. All dependencies are managed using `uv` for ultra-fast package installation and management.

### Code Organization

The project follows a modular architecture with clear separation of concerns:

- **`src/embeddings/`** - Handles image and PDF embedding generation using CLIP and Gemini Vision
- **`src/processing/`** - Manages PDF data processing and document chunking
- **`src/database/`** - Contains ChromaDB operations and vector database management
- **`src/utils/`** - Utility functions and helpers (extensible for future needs)

### Adding New Features

1. **New Embedding Models**: Add to `src/embeddings/`
2. **Data Processors**: Add to `src/processing/`
3. **Database Operations**: Add to `src/database/`
4. **Utility Functions**: Add to `src/utils/`

## Troubleshooting

- **Import Errors**: Ensure virtual environment is activated and all dependencies are installed
- **API Errors**: Check that `GEMINI_API_KEY` is set in `.env` file
- **Database Issues**: Clear `chroma_db/` directory to reset vector database
- **PDF Processing**: Ensure PyMuPDF is properly installed for PDF operations

## License

This project is part of the Fanshawe College Capstone Project AIM.