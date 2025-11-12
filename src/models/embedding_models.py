"""
Embedding Models Management
============================

This module manages the initialization and configuration of embedding models
for text and images in the multimodal RAG system.
"""

from typing import Optional, List, Dict, Any
import numpy as np

# Try to import embedding models, but don't fail if not available
try:
    from vertexai.language_models import TextEmbeddingModel
    from vertexai.vision_models import MultiModalEmbeddingModel, Image as vision_model_Image
    EMBEDDING_MODELS_AVAILABLE = True
except ImportError:
    EMBEDDING_MODELS_AVAILABLE = False
    print("⚠️  Embedding models not available. Install with: pip install google-cloud-aiplatform")


class EmbeddingModelManager:
    """Manages embedding models for text and images"""

    def __init__(self, embedding_size: int = 512):
        self.embedding_size = embedding_size
        self.text_embedding_model = None
        self.multimodal_embedding_model = None
        self.is_initialized = False

        # Model configurations
        self.text_model_name = "text-embedding-005"
        self.multimodal_model_name = "multimodalembedding@001"

    def initialize_text_embedding_model(self) -> bool:
        """Initializes the text embedding model"""
        if not EMBEDDING_MODELS_AVAILABLE:
            print("❌ Embedding models not available")
            return False

        try:
            self.text_embedding_model = TextEmbeddingModel.from_pretrained(self.text_model_name)
            print(f"✅ Text embedding model '{self.text_model_name}' initialized")
            return True
        except Exception as e:
            print(f"❌ Error initializing text model: {e}")
            return False

    def initialize_multimodal_embedding_model(self) -> bool:
        """Initializes the multimodal embedding model"""
        if not EMBEDDING_MODELS_AVAILABLE:
            print("❌ Embedding models not available")
            return False

        try:
            self.multimodal_embedding_model = MultiModalEmbeddingModel.from_pretrained(self.multimodal_model_name)
            print(f"✅ Multimodal embedding model '{self.multimodal_model_name}' initialized")
            return True
        except Exception as e:
            print(f"❌ Error initializing multimodal model: {e}")
            return False

    def validate_embedding_models(self) -> bool:
        """Validates if embedding models are available"""
        if not self.text_embedding_model:
            print("❌ Text embedding model not initialized")
            return False

        if not self.multimodal_embedding_model:
            print("❌ Multimodal embedding model not initialized")
            return False

        print("✅ All embedding models are available")
        return True

    def test_text_embedding_generation(self, test_text: str = "This is a test text for embedding generation") -> bool:
        """Tests text embedding generation"""
        if not self.text_embedding_model:
            print("❌ Text model not initialized for testing")
            return False

        try:
            print(f"🧪 Testing text embedding: '{test_text[:50]}...'")

            embeddings = self.text_embedding_model.get_embeddings([test_text])
            text_embedding = [embedding.values for embedding in embeddings][0]

            if text_embedding and len(text_embedding) > 0:
                print(f"✅ Text embedding generated: {len(text_embedding)} dimensions")
                return True
            else:
                print("❌ Empty text embedding")
                return False

        except Exception as e:
            print(f"❌ Error testing text embedding: {e}")
            return False

    def test_multimodal_embedding_generation(self, test_image_path: str = None) -> bool:
        """Tests multimodal embedding generation"""
        if not self.multimodal_embedding_model:
            print("❌ Multimodal model not initialized for testing")
            return False

        # If no test image, create a simple image or skip test
        if not test_image_path:
            print("⚠️  No test image provided. Skipping multimodal test.")
            return True

        try:
            print(f"🧪 Testing multimodal embedding with image: {test_image_path}")

            # Load image
            image = vision_model_Image.load_from_file(test_image_path)

            # Generate embedding
            embeddings = self.multimodal_embedding_model.get_embeddings(
                image=image,
                dimension=self.embedding_size
            )

            image_embedding = embeddings.image_embedding

            if image_embedding and len(image_embedding) > 0:
                print(f"✅ Multimodal embedding generated: {len(image_embedding)} dimensions")
                return True
            else:
                print("❌ Empty multimodal embedding")
                return False

        except Exception as e:
            print(f"❌ Error testing multimodal embedding: {e}")
            return False
    
    def get_text_embedding_model(self) -> Optional[TextEmbeddingModel]:
        """Returns the text embedding model"""
        return self.text_embedding_model

    def get_multimodal_embedding_model(self) -> Optional[MultiModalEmbeddingModel]:
        """Returns the multimodal embedding model"""
        return self.multimodal_embedding_model

    def get_embedding_size(self) -> int:
        """Returns the configured embedding size"""
        return self.embedding_size

    def display_embedding_status(self) -> None:
        """Displays the status of embedding models"""
        print("🔢 EMBEDDING MODELS STATUS")
        print("=" * 40)
        print(f"📊 Embedding size: {self.embedding_size}")
        print(f"📝 Text model: {self.text_model_name}")
        print(f"🖼️  Multimodal model: {self.multimodal_model_name}")
        print(f"✅ Text initialized: {'Yes' if self.text_embedding_model else 'No'}")
        print(f"✅ Multimodal initialized: {'Yes' if self.multimodal_embedding_model else 'No'}")
        print(f"✅ Both initialized: {'Yes' if self.is_initialized else 'No'}")
        print("=" * 40)
