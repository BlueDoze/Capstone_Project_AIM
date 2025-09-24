#!/usr/bin/env python3
"""
Image Embedding Module for ChromaDB.
Supports multiple embedding models: CLIP, Gemini Vision, and OpenAI CLIP.
"""

import os
import base64
import numpy as np
from typing import List, Union, Optional, Dict, Any
import requests
from PIL import Image
import io

# Try to import optional dependencies
try:
    import torch
    import open_clip
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    print("⚠️ CLIP not available. Install with: pip install torch open_clip_torch")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini not available. Install with: pip install google-generativeai")

class ImageEmbedder:
    """Base class for image embedding models"""
    
    def __init__(self, model_name: str = "clip"):
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu" if CLIP_AVAILABLE else "cpu"
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        pass
    
    def embed_image(self, image_path: str) -> np.ndarray:
        """Generate embedding for a single image"""
        pass
    
    def embed_images(self, image_paths: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple images"""
        pass

class CLIPEmbedder(ImageEmbedder):
    """CLIP-based image embedder"""
    
    def __init__(self, model_name: str = "ViT-B-32"):
        if not CLIP_AVAILABLE:
            raise ImportError("CLIP is not installed. Install with: pip install torch open_clip_torch")
        
        self.clip_model_name = model_name
        super().__init__("clip")
    
    def _load_model(self):
        """Load CLIP model"""
        try:
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                self.clip_model_name, 
                pretrained='openai',
                device=self.device
            )
            print(f"✅ CLIP model {self.clip_model_name} loaded successfully")
        except Exception as e:
            print(f"❌ Error loading CLIP model: {e}")
            raise
    
    def embed_image(self, image_path: str) -> np.ndarray:
        """Generate CLIP embedding for a single image"""
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                # Normalize the features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
            return image_features.cpu().numpy().flatten()
            
        except Exception as e:
            print(f"❌ Error embedding image {image_path}: {e}")
            raise
    
    def embed_images(self, image_paths: List[str]) -> List[np.ndarray]:
        """Generate CLIP embeddings for multiple images"""
        embeddings = []
        for path in image_paths:
            try:
                embedding = self.embed_image(path)
                embeddings.append(embedding)
            except Exception as e:
                print(f"❌ Error processing {path}: {e}")
                # Add zero vector as fallback
                embeddings.append(np.zeros(512))  # CLIP ViT-B/32 has 512 dimensions
        
        return embeddings

class GeminiVisionEmbedder(ImageEmbedder):
    """Gemini Vision-based image embedder"""
    
    def __init__(self, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("Gemini is not installed. Install with: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        super().__init__("gemini_vision")
    
    def _load_model(self):
        """Configure Gemini API"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Gemini Vision model configured successfully")
        except Exception as e:
            print(f"❌ Error configuring Gemini: {e}")
            raise
    
    def embed_image(self, image_path: str) -> np.ndarray:
        """Generate Gemini Vision embedding for a single image"""
        try:
            # Load and encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode()
            
            # Create prompt for embedding generation
            prompt = "Describe this image in detail for navigation purposes. Focus on spatial relationships, room types, landmarks, and navigational features."
            
            # Generate response (we'll use the text response as a proxy for embedding)
            # Note: Gemini doesn't directly provide embeddings, so we'll use text description
            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
            
            # Convert text response to embedding-like vector
            # This is a simplified approach - in practice, you might want to use
            # a text embedder on the response
            text = response.text
            # Simple hash-based embedding (you could use a proper text embedder here)
            embedding = np.array([hash(word) % 1000 for word in text.split()[:512]])
            if len(embedding) < 512:
                embedding = np.pad(embedding, (0, 512 - len(embedding)), 'constant')
            
            return embedding[:512]  # Ensure consistent size
            
        except Exception as e:
            print(f"❌ Error embedding image {image_path}: {e}")
            raise
    
    def embed_images(self, image_paths: List[str]) -> List[np.ndarray]:
        """Generate Gemini Vision embeddings for multiple images"""
        embeddings = []
        for path in image_paths:
            try:
                embedding = self.embed_image(path)
                embeddings.append(embedding)
            except Exception as e:
                print(f"❌ Error processing {path}: {e}")
                # Add zero vector as fallback
                embeddings.append(np.zeros(512))
        
        return embeddings

class ImageEmbeddingManager:
    """Manager for handling image embeddings with ChromaDB"""
    
    def __init__(self, embedder_type: str = "clip", **kwargs):
        self.embedder_type = embedder_type
        self.embedder = self._create_embedder(**kwargs)
    
    def _create_embedder(self, **kwargs) -> ImageEmbedder:
        """Create the appropriate embedder based on type"""
        if self.embedder_type.lower() == "clip":
            if not CLIP_AVAILABLE:
                print("⚠️ CLIP not available, falling back to Gemini Vision")
                return GeminiVisionEmbedder(**kwargs)
            return CLIPEmbedder(**kwargs)
        elif self.embedder_type.lower() == "gemini":
            return GeminiVisionEmbedder(**kwargs)
        else:
            raise ValueError(f"Unsupported embedder type: {self.embedder_type}")
    
    def process_images(self, image_paths: List[str], descriptions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Process multiple images and return embeddings with metadata"""
        if descriptions is None:
            descriptions = [f"Image from {os.path.basename(path)}" for path in image_paths]
        
        # Generate embeddings
        embeddings = self.embedder.embed_images(image_paths)
        
        # Prepare data for ChromaDB
        ids = [f"img_{i}" for i in range(len(image_paths))]
        metadatas = []
        
        for i, (path, desc) in enumerate(zip(image_paths, descriptions)):
            metadata = {
                "type": "image",
                "path": path,
                "filename": os.path.basename(path),
                "description": desc,
                "embedder": self.embedder_type
            }
            metadatas.append(metadata)
        
        return {
            "embeddings": embeddings,
            "documents": descriptions,
            "metadatas": metadatas,
            "ids": ids
        }
    
    def embed_single_image(self, image_path: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Process a single image"""
        if description is None:
            description = f"Image from {os.path.basename(image_path)}"
        
        embedding = self.embedder.embed_image(image_path)
        
        return {
            "embedding": embedding,
            "document": description,
            "metadata": {
                "type": "image",
                "path": image_path,
                "filename": os.path.basename(image_path),
                "description": description,
                "embedder": self.embedder_type
            },
            "id": f"img_{os.path.basename(image_path)}"
        }

# Example usage function
def create_sample_image_data():
    """Create sample image data for testing"""
    sample_data = {
        "image_paths": [
            "images/building_entrance.jpg",
            "images/main_hallway.jpg", 
            "images/room_1003.jpg",
            "images/computer_lab.jpg",
            "images/main_office.jpg"
        ],
        "descriptions": [
            "South entrance of M1 Blue Building with main doors and accessible entrance",
            "Main hallway running north-south with classrooms on both sides",
            "Large classroom 1003 near south entrance on west side",
            "Computer lab with workstations and equipment",
            "Main office 1033 in north-east corner with reception desk"
        ]
    }
    return sample_data
