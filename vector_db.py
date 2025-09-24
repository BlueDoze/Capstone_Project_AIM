#!/usr/bin/env python3
"""
Vector Database Module for ChromaDB operations.
Handles initialization, document storage, and retrieval for map navigation.
"""

import chromadb
from typing import List, Dict, Any, Optional, Union
import os
import numpy as np

class MapVectorDB:
    """ChromaDB wrapper for map navigation data"""
    
    def __init__(self, db_path: str = "./chroma_db"):
        """Initialize the vector database"""
        self.db_path = db_path
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection("map_navigation")
                print("✅ Using existing map navigation collection")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name="map_navigation",
                    metadata={"description": "Campus navigation data for Fanshawe College"}
                )
                print("✅ Created new map navigation collection")
                
        except Exception as e:
            print(f"❌ Error initializing ChromaDB: {e}")
            raise
    
    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str], embeddings: Optional[List[List[float]]] = None):
        """Add documents to the vector database"""
        try:
            if embeddings is not None:
                # Add documents with custom embeddings
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                # Add documents with default text embeddings
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            print(f"✅ Added {len(documents)} documents to vector database")
            return True
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            return False
    
    def search(self, query: str, n_results: int = 3, query_embeddings: Optional[List[List[float]]] = None) -> Dict[str, Any]:
        """Search for relevant documents based on query"""
        try:
            if query_embeddings is not None:
                # Search using custom embeddings (for images)
                results = self.collection.query(
                    query_embeddings=query_embeddings,
                    n_results=n_results
                )
            else:
                # Search using text query
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
            
            # Format results for easier use
            formatted_results = {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'ids': results['ids'][0] if results['ids'] else []
            }
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching vector database: {e}")
            return {'documents': [], 'metadatas': [], 'distances': [], 'ids': []}
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            return {
                'name': self.collection.name,
                'count': self.collection.count(),
                'metadata': self.collection.metadata
            }
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return {}
    
    def add_images(self, image_data: Dict[str, Any]):
        """Add image embeddings to the vector database"""
        try:
            embeddings = image_data.get('embeddings', [])
            documents = image_data.get('documents', [])
            metadatas = image_data.get('metadatas', [])
            ids = image_data.get('ids', [])
            
            if not all([embeddings, documents, metadatas, ids]):
                raise ValueError("Missing required image data fields")
            
            # Convert numpy arrays to lists if needed
            embeddings_list = []
            for emb in embeddings:
                if isinstance(emb, np.ndarray):
                    embeddings_list.append(emb.tolist())
                else:
                    embeddings_list.append(emb)
            
            self.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings_list
            )
            
            print(f"✅ Added {len(documents)} image embeddings to vector database")
            return True
            
        except Exception as e:
            print(f"❌ Error adding images: {e}")
            return False
    
    def search_by_image(self, image_embedding: Union[List[float], np.ndarray], n_results: int = 3) -> Dict[str, Any]:
        """Search for similar images using image embedding"""
        try:
            # Convert to list if numpy array
            if isinstance(image_embedding, np.ndarray):
                query_embedding = image_embedding.tolist()
            else:
                query_embedding = image_embedding
            
            return self.search(
                query="",  # Empty query since we're using embeddings
                n_results=n_results,
                query_embeddings=[query_embedding]
            )
            
        except Exception as e:
            print(f"❌ Error searching by image: {e}")
            return {'documents': [], 'metadatas': [], 'distances': [], 'ids': []}
    
    def get_images_by_type(self, image_type: str) -> Dict[str, Any]:
        """Get all images of a specific type"""
        try:
            results = self.collection.get(
                where={"type": "image", "category": image_type}
            )
            
            return {
                'documents': results['documents'] if results['documents'] else [],
                'metadatas': results['metadatas'] if results['metadatas'] else [],
                'ids': results['ids'] if results['ids'] else []
            }
            
        except Exception as e:
            print(f"❌ Error getting images by type: {e}")
            return {'documents': [], 'metadatas': [], 'ids': []}
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection("map_navigation")
            self.collection = self.client.create_collection(
                name="map_navigation",
                metadata={"description": "Campus navigation data for Fanshawe College"}
            )
            print("✅ Collection cleared successfully")
        except Exception as e:
            print(f"❌ Error clearing collection: {e}")

# Global instance for the Flask app
vector_db = None

def initialize_vector_db():
    """Initialize the global vector database instance"""
    global vector_db
    if vector_db is None:
        vector_db = MapVectorDB()
    return vector_db

def get_vector_db() -> Optional[MapVectorDB]:
    """Get the global vector database instance"""
    return vector_db
