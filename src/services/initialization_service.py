"""
Serviço de Inicialização de Modelos
===================================

Este módulo orquestra a inicialização de todos os modelos necessários
para o sistema RAG multimodal, incluindo Gemini e modelos de embedding.
"""

from typing import Tuple, Optional
import os
import sys

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.settings import RAGConfig
from config.environment import EnvironmentManager
from models.gemini_models import GeminiModelManager
from models.embedding_models import EmbeddingModelManager


class InitializationService:
    """Serviço principal de inicialização do sistema RAG multimodal"""
    
    def __init__(self):
        self.config = None
        self.env_manager = None
        self.gemini_manager = None
        self.embedding_manager = None
        self.is_fully_initialized = False
    
    def prepare_system(self) -> bool:
        """Prepara o sistema carregando configurações e variáveis de ambiente"""
        print("🚀 PREPARANDO SISTEMA RAG MULTIMODAL")
        print("=" * 50)
        
        try:
            # 1. Carregar configurações
            self.config = RAGConfig()
            
            # 2. Carregar variáveis de ambiente
            self.env_manager = EnvironmentManager()
            env_loaded = self.env_manager.load_env_variables()
            
            if not env_loaded:
                print("⚠️  Arquivo .env não encontrado, usando variáveis do sistema")
            
            # 3. Validar variáveis obrigatórias
            if not self.env_manager.validate_required_vars():
                print("❌ Variáveis obrigatórias não definidas")
                return False
            
            # 4. Atualizar configuração com variáveis de ambiente
            self.config.PROJECT_ID = self.env_manager.get_project_id()
            
            # 5. Criar diretórios necessários
            if not self.config.create_directories():
                print("❌ Erro ao criar diretórios")
                return False
            
            print("✅ Sistema preparado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao preparar sistema: {e}")
            return False
    
    def initialize_models(self) -> bool:
        """Inicializa todos os modelos necessários"""
        print("\n🤖 INICIALIZANDO MODELOS")
        print("=" * 30)
        
        try:
            # 1. Inicializar Gemini 2.5 Pro
            self.gemini_manager = GeminiModelManager(
                project_id=self.config.PROJECT_ID,
                location=self.config.LOCATION
            )
            
            # Inicializar Vertex AI
            if not self.gemini_manager.initialize_vertex_ai():
                print("❌ Falha na inicialização do Vertex AI")
                return False
            
            # Inicializar Gemini 2.5 Pro
            if not self.gemini_manager.initialize_gemini_2_5_pro():
                print("❌ Falha na inicialização do Gemini 2.5 Pro")
                return False
            
            # 2. Inicializar modelos de embedding
            self.embedding_manager = EmbeddingModelManager(
                embedding_size=self.config.EMBEDDING_SIZE
            )
            
            # Inicializar modelo de texto
            if not self.embedding_manager.initialize_text_embedding_model():
                print("❌ Falha na inicialização do modelo de texto")
                return False
            
            # Inicializar modelo multimodal
            if not self.embedding_manager.initialize_multimodal_embedding_model():
                print("❌ Falha na inicialização do modelo multimodal")
                return False
            
            self.embedding_manager.is_initialized = True
            
            print("✅ Todos os modelos inicializados com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar modelos: {e}")
            return False
    
    def validate_resources(self) -> bool:
        """Valida se todos os recursos estão funcionando"""
        print("\n🔍 VALIDANDO RECURSOS")
        print("=" * 25)
        
        try:
            # 1. Validar Gemini
            if not self.gemini_manager.validate_gemini_availability():
                print("❌ Gemini não está disponível")
                return False
            
            # 2. Validar modelos de embedding
            if not self.embedding_manager.validate_embedding_models():
                print("❌ Modelos de embedding não estão disponíveis")
                return False
            
            print("✅ Todos os recursos validados com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro na validação de recursos: {e}")
            return False
    
    def run_preparation_phase(self) -> bool:
        """Executa a fase completa de preparação"""
        print("🎯 EXECUTANDO FASE DE PREPARAÇÃO COMPLETA")
        print("=" * 50)
        
        # 1. Preparar sistema
        if not self.prepare_system():
            return False
        
        # 2. Inicializar modelos
        if not self.initialize_models():
            return False
        
        # 3. Validar recursos
        if not self.validate_resources():
            return False
        
        self.is_fully_initialized = True
        print("\n🎉 FASE DE PREPARAÇÃO CONCLUÍDA COM SUCESSO!")
        return True
    
    def get_system_status(self) -> dict:
        """Retorna o status atual do sistema"""
        return {
            "config_loaded": self.config is not None,
            "env_loaded": self.env_manager is not None,
            "gemini_initialized": self.gemini_manager is not None and self.gemini_manager.is_initialized,
            "embedding_initialized": self.embedding_manager is not None and self.embedding_manager.is_initialized,
            "fully_initialized": self.is_fully_initialized
        }
    
    def display_system_status(self) -> None:
        """Exibe o status completo do sistema"""
        print("\n📊 STATUS COMPLETO DO SISTEMA")
        print("=" * 35)
        
        status = self.get_system_status()
        
        print(f"🔧 Configuração: {'✅' if status['config_loaded'] else '❌'}")
        print(f"🌍 Ambiente: {'✅' if status['env_loaded'] else '❌'}")
        print(f"🤖 Gemini 2.5 Pro: {'✅' if status['gemini_initialized'] else '❌'}")
        print(f"🔢 Embeddings: {'✅' if status['embedding_initialized'] else '❌'}")
        print(f"🎯 Sistema Completo: {'✅' if status['fully_initialized'] else '❌'}")
        
        print("=" * 35)
        
        # Exibir status detalhado dos modelos
        if self.gemini_manager:
            self.gemini_manager.display_model_status()
        
        if self.embedding_manager:
            self.embedding_manager.display_embedding_status()
