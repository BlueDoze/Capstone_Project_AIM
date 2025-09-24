#!/usr/bin/env python3
"""
PDF Data Processor for handling PDF embeddings in the map navigation system.
Processes PDFs and creates embeddings for document-based navigation assistance.
"""

import os
from typing import List, Dict, Any, Optional
from pdf_embedder import PDFEmbeddingManager, PyMuPDFProcessor
from image_embedder import CLIPEmbedder

class PDFDataProcessor:
    """Processes PDFs for the map navigation system"""
    
    def __init__(self, strategy: str = "text"):
        self.strategy = strategy
        self.pdf_processor = PyMuPDFProcessor()
        
        # Initialize embedders based on strategy
        self.text_embedder = None
        self.image_embedder = None
        
        if strategy in ["image", "hybrid"]:
            try:
                self.image_embedder = CLIPEmbedder()
                print("✅ CLIP embedder initialized for PDF images")
            except Exception as e:
                print(f"⚠️ CLIP embedder not available: {e}")
        
        self.embedding_manager = PDFEmbeddingManager(
            strategy=strategy,
            text_embedder=self.text_embedder,
            image_embedder=self.image_embedder
        )
    
    def process_building_pdfs(self, pdfs_dir: str = "documents") -> Dict[str, Any]:
        """Process building-related PDFs and create embeddings"""
        
        # Define sample PDF data (you would replace this with actual PDF paths)
        sample_pdfs = {
            "pdf_paths": [
                "documents/building_floor_plan.pdf",
                "documents/navigation_guide.pdf",
                "documents/room_directory.pdf",
                "documents/accessibility_map.pdf",
                "documents/emergency_exits.pdf",
                "documents/parking_guide.pdf"
            ],
            "descriptions": [
                "M1 Blue Building floor plan showing room layouts, corridors, and spatial relationships",
                "Step-by-step navigation guide for visitors with detailed directions and landmarks",
                "Complete room directory with room numbers, descriptions, and locations",
                "Accessibility map showing accessible routes, elevators, and facilities",
                "Emergency exit routes and safety procedures for building evacuation",
                "Parking information including locations, accessibility, and regulations"
            ],
            "categories": [
                "floor_plan",
                "navigation",
                "directory",
                "accessibility",
                "safety",
                "parking"
            ],
            "document_types": [
                "map",
                "guide",
                "directory",
                "map",
                "safety",
                "guide"
            ]
        }
        
        # Check if PDFs directory exists, if not create sample structure
        if not os.path.exists(pdfs_dir):
            print(f"⚠️ PDFs directory '{pdfs_dir}' not found. Creating sample structure...")
            os.makedirs(pdfs_dir, exist_ok=True)
            self._create_sample_pdfs_info(pdfs_dir)
        
        # Process PDFs that actually exist
        existing_pdfs = []
        existing_descriptions = []
        existing_categories = []
        existing_types = []
        
        for i, path in enumerate(sample_pdfs["pdf_paths"]):
            if os.path.exists(path):
                existing_pdfs.append(path)
                existing_descriptions.append(sample_pdfs["descriptions"][i])
                existing_categories.append(sample_pdfs["categories"][i])
                existing_types.append(sample_pdfs["document_types"][i])
            else:
                print(f"⚠️ PDF not found: {path}")
        
        if not existing_pdfs:
            print("❌ No PDFs found. Please add PDFs to the 'documents' directory.")
            return self._create_empty_pdf_data()
        
        # Generate embeddings
        print(f"📄 Processing {len(existing_pdfs)} PDFs...")
        pdf_data = self.embedding_manager.process_pdfs(existing_pdfs, existing_descriptions)
        
        # Add additional metadata
        for i, metadata in enumerate(pdf_data["metadatas"]):
            # Find the corresponding PDF info
            pdf_index = existing_pdfs.index(metadata.get('source_file', ''))
            if pdf_index < len(existing_categories):
                metadata.update({
                    "category": existing_categories[pdf_index],
                    "document_type": existing_types[pdf_index],
                    "pdf_type": "building_navigation"
                })
        
        return pdf_data
    
    def _create_sample_pdfs_info(self, pdfs_dir: str):
        """Create sample PDF information file"""
        sample_info = """# Sample PDFs for M1 Blue Building Navigation

To use PDF embeddings, add these PDFs to the 'documents' directory:

1. building_floor_plan.pdf - Floor plan with room layouts and corridors
2. navigation_guide.pdf - Step-by-step visitor navigation guide
3. room_directory.pdf - Complete room directory with descriptions
4. accessibility_map.pdf - Accessible routes and facilities map
5. emergency_exits.pdf - Emergency exit routes and safety procedures
6. parking_guide.pdf - Parking locations and accessibility information

Each PDF should be:
- High quality and readable
- Related to building navigation
- Named according to the list above
- In PDF format

The system will automatically process these PDFs and create embeddings for document-based navigation assistance.

## PDF Processing Strategies:

1. **Text Strategy**: Extracts text from PDFs and creates text embeddings
2. **Image Strategy**: Converts PDF pages to images and creates image embeddings  
3. **Hybrid Strategy**: Combines both text and image embeddings for comprehensive search

Choose the strategy that best fits your PDF content type.
"""
        
        with open(os.path.join(pdfs_dir, "README.md"), "w") as f:
            f.write(sample_info)
        
        print(f"📝 Created sample PDF info at {pdfs_dir}/README.md")
    
    def _create_empty_pdf_data(self) -> Dict[str, Any]:
        """Create empty PDF data structure"""
        return {
            "embeddings": [],
            "documents": [],
            "metadatas": [],
            "ids": []
        }
    
    def process_single_pdf(self, pdf_path: str, description: str, category: str = "general", doc_type: str = "document") -> Dict[str, Any]:
        """Process a single PDF"""
        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found: {pdf_path}")
            return self._create_empty_pdf_data()
        
        print(f"📄 Processing single PDF: {pdf_path}")
        pdf_data = self.embedding_manager.process_single_pdf(pdf_path, description)
        
        # Add additional metadata
        for metadata in pdf_data["metadatas"]:
            metadata.update({
                "category": category,
                "document_type": doc_type,
                "pdf_type": "building_navigation"
            })
        
        return pdf_data
    
    def get_pdf_categories(self) -> List[str]:
        """Get list of available PDF categories"""
        return [
            "floor_plan",
            "navigation",
            "directory",
            "accessibility",
            "safety",
            "parking",
            "emergency",
            "facilities",
            "guide",
            "map"
        ]
    
    def get_pdf_strategies(self) -> List[str]:
        """Get list of available PDF processing strategies"""
        return ["text", "image", "hybrid"]
    
    def analyze_pdf_content(self, pdf_path: str) -> Dict[str, Any]:
        """Analyze PDF content to suggest best processing strategy"""
        try:
            # Extract basic info
            pages_data = self.pdf_processor.extract_text(pdf_path)
            images_data = self.pdf_processor.extract_images(pdf_path)
            
            # Analyze content
            total_text_length = sum(page['char_count'] for page in pages_data)
            total_images = len(images_data)
            total_pages = len(pages_data)
            
            # Suggest strategy
            if total_images > total_pages * 0.5:
                suggested_strategy = "image"
                reason = "PDF contains many images/diagrams"
            elif total_text_length > 1000:
                suggested_strategy = "text"
                reason = "PDF contains substantial text content"
            else:
                suggested_strategy = "hybrid"
                reason = "PDF contains both text and images"
            
            return {
                "total_pages": total_pages,
                "total_text_length": total_text_length,
                "total_images": total_images,
                "suggested_strategy": suggested_strategy,
                "reason": reason,
                "has_text": total_text_length > 0,
                "has_images": total_images > 0
            }
            
        except Exception as e:
            print(f"❌ Error analyzing PDF {pdf_path}: {e}")
            return {}

def create_pdf_chunks() -> Dict[str, Any]:
    """Create PDF chunks for the vector database"""
    processor = PDFDataProcessor()
    return processor.process_building_pdfs()

def process_custom_pdfs(pdf_paths: List[str], descriptions: List[str], categories: Optional[List[str]] = None) -> Dict[str, Any]:
    """Process custom PDFs with descriptions"""
    processor = PDFDataProcessor()
    
    if categories is None:
        categories = ["general"] * len(pdf_paths)
    
    # Process each PDF individually
    all_embeddings = []
    all_documents = []
    all_metadatas = []
    all_ids = []
    
    for i, (path, desc, cat) in enumerate(zip(pdf_paths, descriptions, categories)):
        pdf_data = processor.process_single_pdf(path, desc, cat)
        
        if pdf_data["embeddings"]:
            all_embeddings.extend(pdf_data["embeddings"])
            all_documents.extend(pdf_data["documents"])
            all_metadatas.extend(pdf_data["metadatas"])
            all_ids.extend(pdf_data["ids"])
    
    return {
        "embeddings": all_embeddings,
        "documents": all_documents,
        "metadatas": all_metadatas,
        "ids": all_ids
    }
