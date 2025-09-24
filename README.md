# Capstone Project AIM

A Flask web application for the Capstone Project AIM.

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
├── .venv/                 # Virtual environment (created by uv)
├── static/                # Static files (CSS, JS)
│   ├── style.css
│   └── script.js
├── templates/             # HTML templates
│   └── index.html
├── main.py               # Main Flask application
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Dependencies

The project uses the following main dependencies:
- Flask 3.1.2 - Web framework
- Google Generative AI - AI integration
- Python-dotenv - Environment variable management
- Autopep8 - Code formatting

## Development

The virtual environment is configured with Python 3.11.10 and includes all necessary development tools. All dependencies are managed using `uv` for ultra-fast package installation and management.

Previews should run automatically when starting a workspace.