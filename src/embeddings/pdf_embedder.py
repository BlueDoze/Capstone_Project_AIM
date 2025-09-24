#!/usr/bin/env python3
"""
PDF Embedding Module for ChromaDB.
Supports text extraction, image conversion, and hybrid PDF processing.
"""

import os
import io
import base64
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path

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

class PDFProcessor:
    """Base class for PDF processing"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def extract_text(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF with page information"""
        pass
    
    def extract_images(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF pages"""
        pass
    
    def convert_pages_to_images(self, pdf_path: str, dpi: int = 150) -> List[Dict[str, Any]]:
        """Convert PDF pages to images"""
        pass

class PyMuPDFProcessor(PDFProcessor):
    """PDF processor using PyMuPDF (fitz)"""
    
    def extract_text(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():  # Only include pages with text
                    pages_data.append({
                        'page_number': page_num + 1,
                        'text': text.strip(),
                        'char_count': len(text),
                        'word_count': len(text.split())
                    })
            
            doc.close()
            return pages_data
            
        except Exception as e:
            print(f"❌ Error extracting text from {pdf_path}: {e}")
            return []
    
    def extract_images(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF pages"""
        try:
            doc = fitz.open(pdf_path)
            images_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        images_data.append({
                            'page_number': page_num + 1,
                            'image_index': img_index,
                            'image_data': img_data,
                            'width': pix.width,
                            'height': pix.height
                        })
                    
                    pix = None
            
            doc.close()
            return images_data
            
        except Exception as e:
            print(f"❌ Error extracting images from {pdf_path}: {e}")
            return []
    
    def convert_pages_to_images(self, pdf_path: str, dpi: int = 150) -> List[Dict[str, Any]]:
        """Convert PDF pages to images"""
        try:
            doc = fitz.open(pdf_path)
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                pages_data.append({
                    'page_number': page_num + 1,
                    'image_data': img_data,
                    'width': pix.width,
                    'height': pix.height,
                    'dpi': dpi
                })
                
                pix = None
            
            doc.close()
            return pages_data
            
        except Exception as e:
            print(f"❌ Error converting pages to images from {pdf_path}: {e}")
            return []

class PDFEmbedder:
    """PDF embedder supporting multiple strategies"""
    
    def __init__(self, strategy: str = "text", text_embedder=None, image_embedder=None):
        self.strategy = strategy  # "text", "image", "hybrid"
        self.text_embedder = text_embedder
        self.image_embedder = image_embedder
        self.pdf_processor = PyMuPDFProcessor()
    
    def embed_pdf_text(self, pdf_path: str, chunk_size: int = 3000, overlap: int = 500) -> List[Dict[str, Any]]:
        """Embed PDF using text extraction"""
        try:
            # Extract text from PDF
            pages_data = self.pdf_processor.extract_text(pdf_path)
            
            if not pages_data:
                print(f"⚠️ No text found in {pdf_path}")
                return []
            
            # Combine all text
            full_text = "\n\n".join([f"Page {p['page_number']}:\n{p['text']}" for p in pages_data])
            
            # Split into chunks
            chunks = self._split_text_into_chunks(full_text, chunk_size, overlap)
            
            # Generate embeddings for each chunk
            embeddings_data = []
            for i, chunk in enumerate(chunks):
                if self.text_embedder:
                    # Use custom text embedder if available
                    embedding = self.text_embedder.embed_text(chunk)
                else:
                    # Simple hash-based embedding as fallback
                    embedding = self._simple_text_embedding(chunk)
                
                embeddings_data.append({
                    'chunk_id': f"pdf_text_{i}",
                    'text': chunk,
                    'embedding': embedding,
                    'metadata': {
                        'type': 'pdf_text',
                        'source_file': os.path.basename(pdf_path),
                        'chunk_index': i,
                        'strategy': 'text'
                    }
                })
            
            return embeddings_data
            
        except Exception as e:
            print(f"❌ Error embedding PDF text from {pdf_path}: {e}")
            return []
    
    def embed_pdf_images(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Embed PDF using page-to-image conversion"""
        try:
            if not self.image_embedder:
                print("❌ Image embedder not available")
                return []
            
            # Convert pages to images
            pages_data = self.pdf_processor.convert_pages_to_images(pdf_path)
            
            if not pages_data:
                print(f"⚠️ No pages found in {pdf_path}")
                return []
            
            embeddings_data = []
            for page_data in pages_data:
                # Convert image data to PIL Image
                img = Image.open(io.BytesIO(page_data['image_data']))
                
                # Generate embedding
                embedding = self.image_embedder.embed_image(img)
                
                embeddings_data.append({
                    'chunk_id': f"pdf_page_{page_data['page_number']}",
                    'image_data': page_data['image_data'],
                    'embedding': embedding,
                    'metadata': {
                        'type': 'pdf_image',
                        'source_file': os.path.basename(pdf_path),
                        'page_number': page_data['page_number'],
                        'width': page_data['width'],
                        'height': page_data['height'],
                        'strategy': 'image'
                    }
                })
            
            return embeddings_data
            
        except Exception as e:
            print(f"❌ Error embedding PDF images from {pdf_path}: {e}")
            return []
    
    def embed_pdf_hybrid(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Embed PDF using both text and image strategies"""
        try:
            text_data = self.embed_pdf_text(pdf_path)
            image_data = self.embed_pdf_images(pdf_path)
            
            # Combine both types
            all_data = text_data + image_data
            
            # Add hybrid metadata
            for item in all_data:
                item['metadata']['strategy'] = 'hybrid'
            
            return all_data
            
        except Exception as e:
            print(f"❌ Error in hybrid PDF embedding from {pdf_path}: {e}")
            return []
    
    def embed_pdf(self, pdf_path: str, **kwargs) -> List[Dict[str, Any]]:
        """Main method to embed PDF based on strategy"""
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            return []
        
        print(f"📄 Processing PDF: {os.path.basename(pdf_path)}")
        
        if self.strategy == "text":
            return self.embed_pdf_text(pdf_path, **kwargs)
        elif self.strategy == "image":
            return self.embed_pdf_images(pdf_path)
        elif self.strategy == "hybrid":
            return self.embed_pdf_hybrid(pdf_path, **kwargs)
        else:
            print(f"❌ Unknown strategy: {self.strategy}")
            return []
    
    def _split_text_into_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # If break point is reasonable
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _simple_text_embedding(self, text: str, dim: int = 384) -> np.ndarray:
        """Simple hash-based text embedding as fallback"""
        words = text.lower().split()
        embedding = np.zeros(dim)
        
        for word in words:
            hash_val = hash(word) % dim
            embedding[hash_val] += 1
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding

class PDFEmbeddingManager:
    """Manager for handling PDF embeddings with ChromaDB"""
    
    def __init__(self, strategy: str = "text", text_embedder=None, image_embedder=None):
        self.strategy = strategy
        self.pdf_embedder = PDFEmbedder(strategy, text_embedder, image_embedder)
    
    def process_pdfs(self, pdf_paths: List[str], descriptions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Process multiple PDFs and return embeddings with metadata"""
        if descriptions is None:
            descriptions = [f"PDF document: {os.path.basename(path)}" for path in pdf_paths]
        
        all_embeddings = []
        all_documents = []
        all_metadatas = []
        all_ids = []
        
        for pdf_path, description in zip(pdf_paths, descriptions):
            print(f"📄 Processing {os.path.basename(pdf_path)}...")
            
            # Generate embeddings for this PDF
            pdf_data = self.pdf_embedder.embed_pdf(pdf_path)
            
            for item in pdf_data:
                all_embeddings.append(item['embedding'])
                all_documents.append(item.get('text', description))
                all_metadatas.append(item['metadata'])
                all_ids.append(item['chunk_id'])
        
        return {
            "embeddings": all_embeddings,
            "documents": all_documents,
            "metadatas": all_metadatas,
            "ids": all_ids
        }
    
    def process_single_pdf(self, pdf_path: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Process a single PDF"""
        if description is None:
            description = f"PDF document: {os.path.basename(pdf_path)}"
        
        pdf_data = self.pdf_embedder.embed_pdf(pdf_path)
        
        if not pdf_data:
            return {"embeddings": [], "documents": [], "metadatas": [], "ids": []}
        
        embeddings = [item['embedding'] for item in pdf_data]
        documents = [item.get('text', description) for item in pdf_data]
        metadatas = [item['metadata'] for item in pdf_data]
        ids = [item['chunk_id'] for item in pdf_data]
        
        return {
            "embeddings": embeddings,
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids
        }

# Example usage function
def create_sample_pdf_data():
    """Create sample PDF data for testing"""
    sample_data = {
        "pdf_paths": [
            "documents/building_floor_plan.pdf",
            "documents/navigation_guide.pdf",
            "documents/room_directory.pdf",
            "documents/accessibility_map.pdf"
        ],
        "descriptions": [
            "M1 Blue Building floor plan with room layouts and navigation",
            "Step-by-step navigation guide for building visitors",
            "Complete room directory with descriptions and locations",
            "Accessibility map showing accessible routes and facilities"
        ]
    }
    return sample_data
