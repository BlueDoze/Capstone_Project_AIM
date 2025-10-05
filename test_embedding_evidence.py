#!/usr/bin/env python3
"""
Teste Específico: Carregamento de Modelos de Embedding
=====================================================

Este script demonstra especificamente o carregamento e validação
dos modelos de embedding implementados no sistema RAG multimodal.
"""

import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.embedding_models import EmbeddingModelManager
from config.settings import RAGConfig
from config.environment import EnvironmentManager


def test_embedding_model_loading():
    """Testa especificamente o carregamento dos modelos de embedding"""
    print("🧪 TESTE ESPECÍFICO: Carregamento de Modelos de Embedding")
    print("=" * 60)
    
    # 1. Verificar se as bibliotecas estão disponíveis
    print("📋 Verificando disponibilidade das bibliotecas...")
    try:
        from vertexai.language_models import TextEmbeddingModel
        from vertexai.vision_models import MultiModalEmbeddingModel
        print("✅ Bibliotecas de embedding disponíveis")
    except ImportError as e:
        print(f"❌ Bibliotecas não disponíveis: {e}")
        return False
    
    # 2. Criar gerenciador de embedding
    print("\n🔧 Criando gerenciador de embedding...")
    embedding_manager = EmbeddingModelManager(embedding_size=512)
    print(f"✅ Gerenciador criado com tamanho: {embedding_manager.embedding_size}")
    
    # 3. Testar inicialização do modelo de texto
    print("\n📝 Testando inicialização do modelo de texto...")
    text_success = embedding_manager.initialize_text_embedding_model()
    
    if text_success:
        print("✅ Modelo de embedding de texto carregado com sucesso")
        print(f"   - Nome do modelo: {embedding_manager.text_model_name}")
        print(f"   - Instância criada: {embedding_manager.text_embedding_model is not None}")
    else:
        print("❌ Falha no carregamento do modelo de texto")
        return False
    
    # 4. Testar inicialização do modelo multimodal
    print("\n🖼️  Testando inicialização do modelo multimodal...")
    multimodal_success = embedding_manager.initialize_multimodal_embedding_model()
    
    if multimodal_success:
        print("✅ Modelo de embedding multimodal carregado com sucesso")
        print(f"   - Nome do modelo: {embedding_manager.multimodal_model_name}")
        print(f"   - Instância criada: {embedding_manager.multimodal_embedding_model is not None}")
    else:
        print("❌ Falha no carregamento do modelo multimodal")
        return False
    
    # 5. Validar ambos os modelos
    print("\n🔍 Validando ambos os modelos...")
    validation_success = embedding_manager.validate_embedding_models()
    
    if validation_success:
        print("✅ Ambos os modelos de embedding validados com sucesso")
    else:
        print("❌ Falha na validação dos modelos")
        return False
    
    # 6. Exibir status detalhado
    print("\n📊 Status detalhado dos modelos de embedding:")
    embedding_manager.display_embedding_status()
    
    return True


def test_embedding_integration():
    """Testa a integração dos modelos de embedding com o sistema completo"""
    print("\n🧪 TESTE DE INTEGRAÇÃO: Embedding com Sistema Completo")
    print("=" * 55)
    
    # Carregar configurações
    config = RAGConfig()
    env_manager = EnvironmentManager()
    env_manager.load_env_variables()
    config.PROJECT_ID = env_manager.get_project_id()
    
    print(f"✅ Configuração carregada:")
    print(f"   - Project ID: {config.PROJECT_ID}")
    print(f"   - Embedding Size: {config.EMBEDDING_SIZE}")
    
    # Criar gerenciador com configurações do sistema
    embedding_manager = EmbeddingModelManager(
        embedding_size=config.EMBEDDING_SIZE
    )
    
    # Inicializar modelos
    print("\n🚀 Inicializando modelos com configurações do sistema...")
    
    text_success = embedding_manager.initialize_text_embedding_model()
    multimodal_success = embedding_manager.initialize_multimodal_embedding_model()
    
    if text_success and multimodal_success:
        embedding_manager.is_initialized = True
        print("✅ Integração com sistema completo bem-sucedida")
        
        # Verificar métodos disponíveis
        print("\n🔧 Métodos disponíveis no gerenciador:")
        methods = [method for method in dir(embedding_manager) if not method.startswith('_')]
        for method in methods:
            print(f"   - {method}")
        
        return True
    else:
        print("❌ Falha na integração com sistema completo")
        return False


def main():
    """Função principal de teste"""
    print("🚀 DEMONSTRAÇÃO: Carregamento de Modelos de Embedding")
    print("=" * 65)
    
    # Executar testes
    test1_passed = test_embedding_model_loading()
    test2_passed = test_embedding_integration()
    
    # Resultado final
    print("\n📊 RESULTADO DOS TESTES")
    print("=" * 30)
    print(f"Teste 1 (Carregamento Individual): {'✅ PASSOU' if test1_passed else '❌ FALHOU'}")
    print(f"Teste 2 (Integração com Sistema): {'✅ PASSOU' if test2_passed else '❌ FALHOU'}")
    
    all_passed = test1_passed and test2_passed
    
    if all_passed:
        print("\n🎉 EVIDÊNCIA CONFIRMADA!")
        print("✅ Modelos de embedding carregados com sucesso:")
        print("   - text-embedding-005 (Texto)")
        print("   - multimodalembedding@001 (Multimodal)")
        print("✅ Integração com sistema RAG multimodal funcionando")
        print("✅ Estrutura de inicialização implementada corretamente")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM.")
        print("💡 Verifique se as dependências estão instaladas corretamente")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
