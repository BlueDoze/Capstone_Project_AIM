#!/usr/bin/env python3
"""
Teste da Etapa 2: Inicialização de Modelos (Modo Simulação)
==========================================================

Este script testa a inicialização de todos os modelos necessários
para o sistema RAG multimodal, simulando respostas quando não há chaves válidas.
"""

import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.initialization_service import InitializationService


def test_initialization_without_api_calls():
    """Testa inicialização sem fazer chamadas reais à API"""
    print("🧪 TESTE: Inicialização sem Chamadas de API")
    print("=" * 50)
    
    # Criar serviço de inicialização
    init_service = InitializationService()
    
    # Preparar sistema
    print("📋 Preparando sistema...")
    prep_success = init_service.prepare_system()
    
    if not prep_success:
        print("❌ Falha na preparação do sistema")
        return False
    
    # Inicializar modelos (sem testar respostas)
    print("🤖 Inicializando modelos...")
    model_success = init_service.initialize_models()
    
    if not model_success:
        print("❌ Falha na inicialização de modelos")
        return False
    
    # Validar recursos (sem testar respostas)
    print("🔍 Validando recursos...")
    validation_success = init_service.validate_resources()
    
    if not validation_success:
        print("❌ Falha na validação de recursos")
        return False
    
    # Exibir status detalhado
    init_service.display_system_status()
    
    print("✅ Inicialização concluída com sucesso (modo simulação)")
    return True


def test_configuration_integration():
    """Testa integração com configurações da Etapa 1"""
    print("\n🧪 TESTE: Integração com Configurações")
    print("=" * 45)
    
    init_service = InitializationService()
    
    # Preparar sistema
    if not init_service.prepare_system():
        return False
    
    # Verificar se configurações foram carregadas corretamente
    config = init_service.config
    env_manager = init_service.env_manager
    
    print(f"✅ Project ID: {config.PROJECT_ID}")
    print(f"✅ Location: {config.LOCATION}")
    print(f"✅ Gemini Model: {config.GEMINI_MODEL}")
    print(f"✅ Embedding Size: {config.EMBEDDING_SIZE}")
    
    # Verificar se diretórios foram criados
    import os
    if os.path.exists(config.IMAGE_SAVE_DIR):
        print(f"✅ Diretório de imagens: {config.IMAGE_SAVE_DIR}")
    else:
        print(f"❌ Diretório de imagens não encontrado: {config.IMAGE_SAVE_DIR}")
        return False
    
    if os.path.exists(config.PDF_FOLDER_PATH):
        print(f"✅ Diretório de PDFs: {config.PDF_FOLDER_PATH}")
    else:
        print(f"❌ Diretório de PDFs não encontrado: {config.PDF_FOLDER_PATH}")
        return False
    
    print("✅ Integração com configurações funcionando")
    return True


def test_model_managers():
    """Testa os gerenciadores de modelos individualmente"""
    print("\n🧪 TESTE: Gerenciadores de Modelos")
    print("=" * 40)
    
    init_service = InitializationService()
    
    # Preparar sistema
    if not init_service.prepare_system():
        return False
    
    # Inicializar modelos
    if not init_service.initialize_models():
        return False
    
    # Testar gerenciador Gemini
    gemini_manager = init_service.gemini_manager
    print(f"✅ Gemini Manager criado: {gemini_manager is not None}")
    print(f"✅ Modelo Gemini: {gemini_manager.model_name}")
    print(f"✅ Configuração disponível: {gemini_manager.generation_config is not None}")
    print(f"✅ Configurações de segurança: {gemini_manager.safety_settings is not None}")
    
    # Testar gerenciador de embedding
    embedding_manager = init_service.embedding_manager
    print(f"✅ Embedding Manager criado: {embedding_manager is not None}")
    print(f"✅ Tamanho do embedding: {embedding_manager.embedding_size}")
    print(f"✅ Modelo de texto: {embedding_manager.text_model_name}")
    print(f"✅ Modelo multimodal: {embedding_manager.multimodal_model_name}")
    
    print("✅ Gerenciadores de modelos funcionando")
    return True


def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DA ETAPA 2: INICIALIZAÇÃO DE MODELOS (MODO SIMULAÇÃO)")
    print("=" * 80)
    
    # Executar testes
    test1_passed = test_initialization_without_api_calls()
    test2_passed = test_configuration_integration()
    test3_passed = test_model_managers()
    
    # Resultado final
    print("\n📊 RESULTADO DOS TESTES")
    print("=" * 30)
    print(f"Teste 1 (Inicialização): {'✅ PASSOU' if test1_passed else '❌ FALHOU'}")
    print(f"Teste 2 (Integração): {'✅ PASSOU' if test2_passed else '❌ FALHOU'}")
    print(f"Teste 3 (Gerenciadores): {'✅ PASSOU' if test3_passed else '❌ FALHOU'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    
    if all_passed:
        print("\n🎉 TODOS OS TESTES PASSARAM! Etapa 2 concluída com sucesso.")
        print("✅ Estrutura de inicialização de modelos implementada corretamente")
        print("✅ Pronto para próxima etapa: Validação de Recursos")
        print("\n💡 NOTA: Para testes com APIs reais, configure chaves válidas no .env")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM. Verifique a implementação.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
