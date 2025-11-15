"""
Gemini Models Management
========================

This module manages the initialization and configuration of Gemini models,
specifically Gemini 2.5 Pro for the multimodal RAG system.
"""

from typing import Optional, Dict, Any
import os

# Try to import Vertex AI, but don't fail if not available
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig, HarmCategory, HarmBlockThreshold
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    print("⚠️  Vertex AI not available. Install with: pip install google-cloud-aiplatform vertexai")


class GeminiModelManager:
    """Manages Gemini models for the multimodal RAG system"""

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.model = None
        self.is_initialized = False

        # Gemini 2.5 Pro specific configurations
        self.model_name = "gemini-2.5-pro"
        self.generation_config = None
        self.safety_settings = None

    def initialize_vertex_ai(self) -> bool:
        """Initializes Vertex AI"""
        if not VERTEX_AI_AVAILABLE:
            print("❌ Vertex AI not available")
            return False

        try:
            vertexai.init(project=self.project_id, location=self.location)
            print(f"✅ Vertex AI initialized - Project: {self.project_id}, Location: {self.location}")
            return True
        except Exception as e:
            print(f"❌ Error initializing Vertex AI: {e}")
            return False

    def initialize_gemini_2_5_pro(self) -> bool:
        """Initializes specifically the Gemini 2.5 Pro model"""
        if not VERTEX_AI_AVAILABLE:
            print("❌ Vertex AI not available to initialize Gemini")
            return False

        try:
            # Initialize Gemini 2.5 Pro model
            self.model = GenerativeModel(self.model_name)
            print(f"✅ Model {self.model_name} initialized successfully")

            # Configure generation parameters
            self.generation_config = GenerationConfig(
                temperature=0.5,
                max_output_tokens=2048,
                top_p=0.95,
                top_k=40
            )

            # Configure safety settings
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            self.is_initialized = True
            print("✅ Gemini 2.5 Pro settings applied")
            return True

        except Exception as e:
            print(f"❌ Error initializing Gemini 2.5 Pro: {e}")
            return False

    def validate_gemini_availability(self) -> bool:
        """Validates if the Gemini model is available"""
        if not self.is_initialized or not self.model:
            print("❌ Gemini model was not initialized")
            return False

        print("✅ Gemini 2.5 Pro model is available")
        return True

    def test_gemini_response(self, test_prompt: str = "Hello, can you respond with 'Gemini 2.5 Pro is working!'") -> bool:
        """Tests a basic Gemini response"""
        if not self.is_initialized or not self.model:
            print("❌ Model not initialized for testing")
            return False

        try:
            print(f"🧪 Testing Gemini 2.5 Pro with prompt: '{test_prompt}'")

            response = self.model.generate_content(
                test_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            if response and response.text:
                print(f"✅ Gemini response: {response.text}")
                return True
            else:
                print("❌ Empty response from Gemini")
                return False

        except Exception as e:
            print(f"❌ Error testing Gemini: {e}")
            return False

    def get_gemini_model(self) -> Optional[GenerativeModel]:
        """Returns the initialized Gemini model"""
        if self.is_initialized:
            return self.model
        else:
            print("⚠️  Gemini model not initialized")
            return None

    def get_generation_config(self) -> Optional[GenerationConfig]:
        """Returns the generation configuration"""
        return self.generation_config

    def get_safety_settings(self) -> Optional[Dict]:
        """Returns the safety settings"""
        return self.safety_settings

    def display_model_status(self) -> None:
        """Displays the Gemini model status"""
        print("🤖 GEMINI 2.5 PRO MODEL STATUS")
        print("=" * 40)
        print(f"📋 Model: {self.model_name}")
        print(f"🔧 Project ID: {self.project_id}")
        print(f"📍 Location: {self.location}")
        print(f"✅ Initialized: {'Yes' if self.is_initialized else 'No'}")
        print(f"🔧 Configuration: {'Available' if self.generation_config else 'Not available'}")
        print(f"🛡️  Safety: {'Configured' if self.safety_settings else 'Not configured'}")
        print("=" * 40)
