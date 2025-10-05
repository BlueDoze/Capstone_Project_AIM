"""
Gerenciamento de Modelos de Embedding
=====================================

Este módulo gerencia a inicialização e configuração dos modelos de embedding
para texto e imagens no sistema RAG multimodal.
"""

from typing import Optional, List, Dict, Any
import numpy as np

# Tentar importar modelos de embedding, mas não falhar se não estiver disponível
try:
    from vertexai.language_models import TextEmbeddingModel
    from vertexai.vision_models import MultiModalEmbeddingModel, Image as vision_model_Image
    EMBEDDING_MODELS_AVAILABLE = True
except ImportError:
    EMBEDDING_MODELS_AVAILABLE = False
    print("⚠️  Modelos de embedding não disponíveis. Instale com: pip install google-cloud-aiplatform")


class EmbeddingModelManager:
    """Gerencia modelos de embedding para texto e imagens"""
    
    def __init__(self, embedding_size: int = 512):
        self.embedding_size = embedding_size
        self.text_embedding_model = None
        self.multimodal_embedding_model = None
        self.is_initialized = False
        
        # Configurações dos modelos
        self.text_model_name = "text-embedding-005"
        self.multimodal_model_name = "multimodalembedding@001"
    
    def initialize_text_embedding_model(self) -> bool:
        """Inicializa o modelo de embedding de texto"""
        if not EMBEDDING_MODELS_AVAILABLE:
            print("❌ Modelos de embedding não disponíveis")
            return False
            
        try:
            self.text_embedding_model = TextEmbeddingModel.from_pretrained(self.text_model_name)
            print(f"✅ Modelo de embedding de texto '{self.text_model_name}' inicializado")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar modelo de texto: {e}")
            return False
    
    def initialize_multimodal_embedding_model(self) -> bool:
        """Inicializa o modelo de embedding multimodal"""
        if not EMBEDDING_MODELS_AVAILABLE:
            print("❌ Modelos de embedding não disponíveis")
            return False
            
        try:
            self.multimodal_embedding_model = MultiModalEmbeddingModel.from_pretrained(self.multimodal_model_name)
            print(f"✅ Modelo de embedding multimodal '{self.multimodal_model_name}' inicializado")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar modelo multimodal: {e}")
            return False
    
    def validate_embedding_models(self) -> bool:
        """Valida se os modelos de embedding estão disponíveis"""
        if not self.text_embedding_model:
            print("❌ Modelo de embedding de texto não inicializado")
            return False
        
        if not self.multimodal_embedding_model:
            print("❌ Modelo de embedding multimodal não inicializado")
            return False
        
        print("✅ Todos os modelos de embedding estão disponíveis")
        return True
    
    def test_text_embedding_generation(self, test_text: str = "This is a test text for embedding generation") -> bool:
        """Testa a geração de embedding de texto"""
        if not self.text_embedding_model:
            print("❌ Modelo de texto não inicializado para teste")
            return False
        
        try:
            print(f"🧪 Testando embedding de texto: '{test_text[:50]}...'")
            
            embeddings = self.text_embedding_model.get_embeddings([test_text])
            text_embedding = [embedding.values for embedding in embeddings][0]
            
            if text_embedding and len(text_embedding) > 0:
                print(f"✅ Embedding de texto gerado: {len(text_embedding)} dimensões")
                return True
            else:
                print("❌ Embedding de texto vazio")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao testar embedding de texto: {e}")
            return False
    
    def test_multimodal_embedding_generation(self, test_image_path: str = None) -> bool:
        """Testa a geração de embedding multimodal"""
        if not self.multimodal_embedding_model:
            print("❌ Modelo multimodal não inicializado para teste")
            return False
        
        # Se não há imagem de teste, criar uma imagem simples ou pular o teste
        if not test_image_path:
            print("⚠️  Nenhuma imagem de teste fornecida. Pulando teste multimodal.")
            return True
        
        try:
            print(f"🧪 Testando embedding multimodal com imagem: {test_image_path}")
            
            # Carregar imagem
            image = vision_model_Image.load_from_file(test_image_path)
            
            # Gerar embedding
            embeddings = self.multimodal_embedding_model.get_embeddings(
                image=image, 
                dimension=self.embedding_size
            )
            
            image_embedding = embeddings.image_embedding
            
            if image_embedding and len(image_embedding) > 0:
                print(f"✅ Embedding multimodal gerado: {len(image_embedding)} dimensões")
                return True
            else:
                print("❌ Embedding multimodal vazio")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao testar embedding multimodal: {e}")
            return False
    
    def get_text_embedding_model(self) -> Optional[TextEmbeddingModel]:
        """Retorna o modelo de embedding de texto"""
        return self.text_embedding_model
    
    def get_multimodal_embedding_model(self) -> Optional[MultiModalEmbeddingModel]:
        """Retorna o modelo de embedding multimodal"""
        return self.multimodal_embedding_model
    
    def get_embedding_size(self) -> int:
        """Retorna o tamanho do embedding configurado"""
        return self.embedding_size
    
    def display_embedding_status(self) -> None:
        """Exibe o status dos modelos de embedding"""
        print("🔢 STATUS DOS MODELOS DE EMBEDDING")
        print("=" * 40)
        print(f"📊 Tamanho do embedding: {self.embedding_size}")
        print(f"📝 Modelo de texto: {self.text_model_name}")
        print(f"🖼️  Modelo multimodal: {self.multimodal_model_name}")
        print(f"✅ Texto inicializado: {'Sim' if self.text_embedding_model else 'Não'}")
        print(f"✅ Multimodal inicializado: {'Sim' if self.multimodal_embedding_model else 'Não'}")
        print(f"✅ Ambos inicializados: {'Sim' if self.is_initialized else 'Não'}")
        print("=" * 40)
