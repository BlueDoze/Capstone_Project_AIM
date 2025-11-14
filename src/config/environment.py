"""
Environment Variables Management
=================================

This module manages the loading and validation of environment variables
needed for the multimodal RAG system operation.
"""

import os
from typing import Dict, List, Optional

# Try to import dotenv, but don't fail if not available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv not available. Using only system environment variables.")


class EnvironmentManager:
    """Manages system environment variables"""

    def __init__(self):
        self.required_vars: List[str] = [
            "GEMINI_API_KEY",
            "GOOGLE_CLOUD_PROJECT_ID"
        ]

        self.optional_vars: Dict[str, str] = {
            "VERTEX_AI_LOCATION": "us-central1",
            "EMBEDDING_SIZE": "512",
            "TOP_N_TEXT": "10",
            "TOP_N_IMAGE": "5"
        }

    def load_env_variables(self, env_file: str = ".env") -> bool:
        """Loads environment variables from .env file"""
        if not DOTENV_AVAILABLE:
            print("⚠️  dotenv not available. Using only system environment variables.")
            return True

        try:
            if os.path.exists(env_file):
                load_dotenv(env_file)
                print(f"✅ File {env_file} loaded successfully")
                return True
            else:
                print(f"⚠️  File {env_file} not found")
                return False
        except Exception as e:
            print(f"❌ Error loading {env_file}: {e}")
            return False

    def validate_required_vars(self) -> bool:
        """Validates if all required variables are defined"""
        missing_vars = []

        for var in self.required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ Required variables not defined: {missing_vars}")
            print("💡 Add these variables to the .env file:")
            for var in missing_vars:
                print(f"   {var}=your_value_here")
            return False

        print("✅ All required variables are defined")
        return True

    def get_project_id(self) -> Optional[str]:
        """Gets the Google Cloud Project ID"""
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        if project_id:
            print(f"✅ Project ID obtained: {project_id}")
        else:
            print("❌ Project ID not found")
        return project_id

    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Gets all necessary API keys"""
        api_keys = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "GOOGLE_CLOUD_PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        }

        # Check which keys are available
        available_keys = [key for key, value in api_keys.items() if value]
        missing_keys = [key for key, value in api_keys.items() if not value]

        if available_keys:
            print(f"✅ Available keys: {available_keys}")

        if missing_keys:
            print(f"❌ Missing keys: {missing_keys}")

        return api_keys

    def get_optional_config(self) -> Dict[str, str]:
        """Gets optional configurations with default values"""
        config = {}

        for var, default_value in self.optional_vars.items():
            config[var] = os.getenv(var, default_value)

        print(f"✅ Optional settings loaded: {list(config.keys())}")
        return config

    def display_env_status(self) -> None:
        """Displays environment variables status"""
        print("🔍 ENVIRONMENT VARIABLES STATUS")
        print("=" * 40)

        # Required variables
        print("📋 Required Variables:")
        for var in self.required_vars:
            status = "✅" if os.getenv(var) else "❌"
            print(f"  {status} {var}")

        # Optional variables
        print("\n📋 Optional Variables:")
        for var, default_value in self.optional_vars.items():
            value = os.getenv(var, default_value)
            print(f"  ✅ {var} = {value}")

        print("=" * 40)
