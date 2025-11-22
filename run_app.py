#!/usr/bin/env python3
"""
Wrapper script to run the Flask application from the new location.
This maintains backward compatibility with old imports and paths.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the app from new location
from src.api.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
