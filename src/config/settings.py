"""
Configurações Principais do Sistema RAG Multimodal
================================================

Define todas as configurações necessárias para o funcionamento do sistema,
incluindo modelos, diretórios e parâmetros de processamento.
"""

from typing import List, Dict, Any
import os
from pathlib import Path


class RAGConfig:
    """Configurações principais do sistema RAG multimodal"""
    
    def __init__(self):
        # Google Cloud Configuration
        self.PROJECT_ID: str = ""
        self.LOCATION: str = "us-central1"
        
        # Embedding Configuration
        self.EMBEDDING_SIZE: int = 512
        self.TOP_N_TEXT: int = 10
        self.TOP_N_IMAGE: int = 5
        
        # Processing Configuration
        self.CHARACTER_LIMIT: int = 1000
        self.OVERLAP: int = 100
        
        # Directory Configuration
        self.IMAGE_SAVE_DIR: str = "images/"
        self.PDF_FOLDER_PATH: str = "map/"
        
        # Model Configuration (Simplified - Only Gemini 2.5 Pro)
        self.GEMINI_MODEL: str = "gemini-2.5-pro"
        self.EMBEDDING_MODELS: List[str] = [
            "text-embedding-005",
            "multimodalembedding@001"
        ]
        
        # Gemini 2.5 Pro Specific Configuration
        self.GEMINI_CONFIG: Dict[str, Any] = {
            "temperature": 0.2,
            "max_output_tokens": 2048,
            "top_p": 0.95,
            "top_k": 40
        }
        
        # Safety Settings
        self.SAFETY_SETTINGS: Dict[str, str] = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
        }
    
    def validate_config(self) -> bool:
        """Valida se todas as configurações obrigatórias estão definidas"""
        required_fields = [
            'PROJECT_ID',
            'GEMINI_MODEL',
            'EMBEDDING_MODELS'
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                print(f"❌ Campo obrigatório não definido: {field}")
                return False
        
        print("✅ Configurações validadas com sucesso")
        return True
    
    def create_directories(self) -> bool:
        """Cria os diretórios necessários se não existirem"""
        directories = [
            self.IMAGE_SAVE_DIR,
            self.PDF_FOLDER_PATH
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                print(f"✅ Diretório criado/verificado: {directory}")
            except Exception as e:
                print(f"❌ Erro ao criar diretório {directory}: {e}")
                return False
        
        return True
    
    def display_config(self) -> None:
        """Exibe as configurações atuais"""
        print("📋 CONFIGURAÇÕES DO SISTEMA RAG MULTIMODAL")
        print("=" * 50)
        print(f"🔧 Project ID: {self.PROJECT_ID}")
        print(f"📍 Location: {self.LOCATION}")
        print(f"🤖 Gemini Model: {self.GEMINI_MODEL}")
        print(f"📊 Embedding Size: {self.EMBEDDING_SIZE}")
        print(f"📁 Image Directory: {self.IMAGE_SAVE_DIR}")
        print(f"📄 PDF Directory: {self.PDF_FOLDER_PATH}")
        print(f"🔢 Top N Text: {self.TOP_N_TEXT}")
        print(f"🔢 Top N Image: {self.TOP_N_IMAGE}")
        print("=" * 50)
