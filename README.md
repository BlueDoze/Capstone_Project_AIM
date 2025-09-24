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

## Updating Embeddings

The application includes scripts to update embeddings for both images and PDFs in the `images/` directory. This is useful when you add new files or want to refresh the vector database.

### Using the Update Script

The `update_image_embeddings.py` script provides several options for updating embeddings:

#### Basic Usage
```bash
python update_image_embeddings.py
```

#### Available Options
- `--help, -h` - Show help message
- `--clear` - Clear existing image embeddings before adding new ones
- `--embedder TYPE` - Choose embedder type ('clip' or 'gemini', default: gemini)
- `--images-dir DIR` - Specify images directory (default: images)
- `--db-path PATH` - Set database path (default: ./chroma_db)

#### Examples
```bash
# Basic update
python update_image_embeddings.py

# Clear and recreate all embeddings
python update_image_embeddings.py --clear

# Use CLIP instead of Gemini
python update_image_embeddings.py --embedder clip

# Specify custom images directory
python update_image_embeddings.py --images-dir /path/to/images --clear
```

### What the Script Does

1. **🔍 Detects Images**: Automatically finds all images in the `images/` directory (jpg, jpeg, png, gif, bmp, tiff, webp)

2. **📝 Generates Descriptions**: Creates automatic descriptions based on filename:
   - Files with "map" → Campus map description
   - Files with "M3" → M3 building description  
   - Others → Generic navigation description

3. **🤖 Processes Embeddings**: Uses the existing embedding system (Gemini Vision by default)

4. **💾 Updates Database**: Adds new embeddings to ChromaDB

### When to Update Embeddings

- **New Images**: When you add new images to the `images/` directory
- **Modified Images**: When existing images are updated or replaced
- **Fresh Start**: When you want to completely refresh the vector database
- **Different Embedder**: When switching between CLIP and Gemini Vision models
- **PDF Updates**: When you modify the `map.pdf` file (the script processes both images and PDFs)

### Supported File Types

The script automatically processes these file formats:

**Image Formats:**
- `.jpg`, `.jpeg` - JPEG images
- `.png` - PNG images  
- `.gif` - GIF images
- `.bmp` - Bitmap images
- `.tiff` - TIFF images
- `.webp` - WebP images

**PDF Files:**
- `.pdf` - PDF documents (processed as both text chunks and page images)

### Processing Strategies

The system supports multiple processing approaches:

1. **Image Processing**: Direct image files are processed using Gemini Vision embeddings
2. **PDF Text Processing**: PDF content is extracted as text and chunked for text-based search
3. **PDF Image Processing**: PDF pages are converted to images and processed with visual embeddings
4. **Hybrid Processing**: Combines both text and image processing for comprehensive coverage

### Current Database Contents

After running the update script, your vector database will contain:
- **Image Embeddings**: All image files from the `images/` directory
- **PDF Text Chunks**: Extracted text content from `map.pdf`
- **PDF Page Images**: Visual representations of PDF pages for spatial search

## Project Structure

```
Capstone_Project_AIM/
├── main.py                    # Main Flask application (entry point)
├── update_image_embeddings.py # Script to update image embeddings
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
- **Multi-Modal Processing**: Handles both images and PDFs with different processing strategies
- **PDF Processing**: Automatic processing of campus maps with text extraction and page-to-image conversion
- **Multi-Modal Embeddings**: Support for both text and image embeddings using Gemini Vision
- **Real-time Chat**: Interactive chat interface for navigation queries
- **Flexible Embedding Updates**: Easy script-based updates for new images and documents
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
- **Embedding Issues**: Use `python update_image_embeddings.py --clear` to refresh image embeddings
- **New Images Not Working**: Run the update script to process new images added to the `images/` directory
- **Dimension Errors**: The script automatically handles different embedding dimensions (384 vs 512)
- **PDF Not Found**: Ensure `map.pdf` is in the `images/` directory for processing
- **Mixed Content**: The script handles both image files and PDF files in the same directory
- **Duplicate Entries**: The script may create duplicate entries for the same file - this is normal and doesn't affect functionality

## License

This project is part of the Fanshawe College Capstone Project AIM.