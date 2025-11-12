"""
Model Initialization Service
=============================

This module orchestrates the initialization of all models needed
for the multimodal RAG system, including Gemini and embedding models.
"""

from typing import Tuple, Optional
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.settings import RAGConfig
from config.environment import EnvironmentManager
from models.gemini_models import GeminiModelManager
from models.embedding_models import EmbeddingModelManager


class InitializationService:
    """Main initialization service for multimodal RAG system"""

    def __init__(self):
        self.config = None
        self.env_manager = None
        self.gemini_manager = None
        self.embedding_manager = None
        self.is_fully_initialized = False

    def prepare_system(self) -> bool:
        """Prepares the system by loading configurations and environment variables"""
        print("🚀 PREPARING MULTIMODAL RAG SYSTEM")
        print("=" * 50)

        try:
            # 1. Load configurations
            self.config = RAGConfig()

            # 2. Load environment variables
            self.env_manager = EnvironmentManager()
            env_loaded = self.env_manager.load_env_variables()

            if not env_loaded:
                print("⚠️  .env file not found, using system variables")

            # 3. Validate required variables
            if not self.env_manager.validate_required_vars():
                print("❌ Required variables not defined")
                return False

            # 4. Update configuration with environment variables
            self.config.PROJECT_ID = self.env_manager.get_project_id()

            # 5. Create necessary directories
            if not self.config.create_directories():
                print("❌ Error creating directories")
                return False

            print("✅ System prepared successfully")
            return True

        except Exception as e:
            print(f"❌ Error preparing system: {e}")
            return False

    def initialize_models(self) -> bool:
        """Initializes all necessary models"""
        print("\n🤖 INITIALIZING MODELS")
        print("=" * 30)

        try:
            # 1. Initialize Gemini 2.5 Pro
            self.gemini_manager = GeminiModelManager(
                project_id=self.config.PROJECT_ID,
                location=self.config.LOCATION
            )

            # Initialize Vertex AI
            if not self.gemini_manager.initialize_vertex_ai():
                print("❌ Vertex AI initialization failed")
                return False

            # Initialize Gemini 2.5 Pro
            if not self.gemini_manager.initialize_gemini_2_5_pro():
                print("❌ Gemini 2.5 Pro initialization failed")
                return False

            # 2. Initialize embedding models
            self.embedding_manager = EmbeddingModelManager(
                embedding_size=self.config.EMBEDDING_SIZE
            )

            # Initialize text model
            if not self.embedding_manager.initialize_text_embedding_model():
                print("❌ Text model initialization failed")
                return False

            # Initialize multimodal model
            if not self.embedding_manager.initialize_multimodal_embedding_model():
                print("❌ Multimodal model initialization failed")
                return False

            self.embedding_manager.is_initialized = True

            print("✅ All models initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Error initializing models: {e}")
            return False

    def validate_resources(self) -> bool:
        """Validates if all resources are working"""
        print("\n🔍 VALIDATING RESOURCES")
        print("=" * 25)

        try:
            # 1. Validate Gemini
            if not self.gemini_manager.validate_gemini_availability():
                print("❌ Gemini is not available")
                return False

            # 2. Validate embedding models
            if not self.embedding_manager.validate_embedding_models():
                print("❌ Embedding models are not available")
                return False

            print("✅ All resources validated successfully")
            return True

        except Exception as e:
            print(f"❌ Error validating resources: {e}")
            return False

    def run_preparation_phase(self) -> bool:
        """Executes the complete preparation phase"""
        print("🎯 RUNNING COMPLETE PREPARATION PHASE")
        print("=" * 50)

        # 1. Prepare system
        if not self.prepare_system():
            return False

        # 2. Initialize models
        if not self.initialize_models():
            return False

        # 3. Validate resources
        if not self.validate_resources():
            return False

        self.is_fully_initialized = True
        print("\n🎉 PREPARATION PHASE COMPLETED SUCCESSFULLY!")
        return True

    def get_system_status(self) -> dict:
        """Returns current system status"""
        return {
            "config_loaded": self.config is not None,
            "env_loaded": self.env_manager is not None,
            "gemini_initialized": self.gemini_manager is not None and self.gemini_manager.is_initialized,
            "embedding_initialized": self.embedding_manager is not None and self.embedding_manager.is_initialized,
            "fully_initialized": self.is_fully_initialized
        }
    
    def display_system_status(self) -> None:
        """Displays complete system status"""
        print("\n📊 COMPLETE SYSTEM STATUS")
        print("=" * 35)

        status = self.get_system_status()

        print(f"🔧 Configuration: {'✅' if status['config_loaded'] else '❌'}")
        print(f"🌍 Environment: {'✅' if status['env_loaded'] else '❌'}")
        print(f"🤖 Gemini 2.5 Pro: {'✅' if status['gemini_initialized'] else '❌'}")
        print(f"🔢 Embeddings: {'✅' if status['embedding_initialized'] else '❌'}")
        print(f"🎯 Complete System: {'✅' if status['fully_initialized'] else '❌'}")

        print("=" * 35)

        # Display detailed model status
        if self.gemini_manager:
            self.gemini_manager.display_model_status()

        if self.embedding_manager:
            self.embedding_manager.display_embedding_status()
