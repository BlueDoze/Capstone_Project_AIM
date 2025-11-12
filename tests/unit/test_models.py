#!/usr/bin/env python3
"""
Teste da Etapa 2: Inicialização de Modelos
==========================================

Este script testa a inicialização de todos os modelos necessários
para o sistema RAG multimodal, incluindo Gemini 2.5 Pro e modelos de embedding.
"""

import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.initialization_service import InitializationService


def test_initialization_service():
    """Testa o serviço de inicialização completo"""
    print("🧪 TESTE 1: Serviço de Inicialização Completo")
    print("=" * 50)
    
    # Criar serviço de inicialização
    init_service = InitializationService()
    
    # Executar fase de preparação completa
    success = init_service.run_preparation_phase()
    
    if success:
        print("✅ Teste de inicialização PASSOU")
        
        # Exibir status detalhado
        init_service.display_system_status()
        
        return True
    else:
        print("❌ Teste de inicialização FALHOU")
        return False


def test_individual_components():
    """Testa componentes individuais"""
    print("\n🧪 TESTE 2: Componentes Individuais")
    print("=" * 40)
    
    init_service = InitializationService()
    
    # Testar preparação do sistema
    print("\n📋 Testando preparação do sistema...")
    prep_success = init_service.prepare_system()
    
    if not prep_success:
        print("❌ Preparação do sistema falhou")
        return False
    
    # Testar inicialização de modelos
    print("\n🤖 Testando inicialização de modelos...")
    model_success = init_service.initialize_models()
    
    if not model_success:
        print("❌ Inicialização de modelos falhou")
        return False
    
    # Testar validação de recursos
    print("\n🔍 Testando validação de recursos...")
    validation_success = init_service.validate_resources()
    
    if not validation_success:
        print("❌ Validação de recursos falhou")
        return False
    
    print("✅ Todos os componentes individuais funcionaram")
    return True


def test_model_responses():
    """Testa respostas dos modelos"""
    print("\n🧪 TESTE 3: Respostas dos Modelos")
    print("=" * 35)
    
    init_service = InitializationService()
    
    # Preparar sistema
    if not init_service.prepare_system():
        print("❌ Falha na preparação do sistema")
        return False
    
    # Inicializar modelos
    if not init_service.initialize_models():
        print("❌ Falha na inicialização de modelos")
        return False
    
    # Testar resposta do Gemini
    print("\n🤖 Testando resposta do Gemini 2.5 Pro...")
    gemini_test = init_service.gemini_manager.test_gemini_response()
    
    # Testar embedding de texto
    print("\n📝 Testando embedding de texto...")
    text_embedding_test = init_service.embedding_manager.test_text_embedding_generation()
    
    # Testar embedding multimodal (se houver imagem)
    print("\n🖼️  Testando embedding multimodal...")
    multimodal_test = init_service.embedding_manager.test_multimodal_embedding_generation()
    
    all_tests_passed = gemini_test and text_embedding_test and multimodal_test
    
    if all_tests_passed:
        print("✅ Todos os testes de resposta passaram")
    else:
        print("❌ Alguns testes de resposta falharam")
    
    return all_tests_passed


def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DA ETAPA 2: INICIALIZAÇÃO DE MODELOS")
    print("=" * 70)
    
    # Executar testes
    test1_passed = test_initialization_service()
    test2_passed = test_individual_components()
    test3_passed = test_model_responses()
    
    # Resultado final
    print("\n📊 RESULTADO DOS TESTES")
    print("=" * 30)
    print(f"Teste 1 (Inicialização Completa): {'✅ PASSOU' if test1_passed else '❌ FALHOU'}")
    print(f"Teste 2 (Componentes Individuais): {'✅ PASSOU' if test2_passed else '❌ FALHOU'}")
    print(f"Teste 3 (Respostas dos Modelos): {'✅ PASSOU' if test3_passed else '❌ FALHOU'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    
    if all_passed:
        print("\n🎉 TODOS OS TESTES PASSARAM! Etapa 2 concluída com sucesso.")
        print("✅ Pronto para próxima etapa: Validação de Recursos")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM. Verifique as configurações.")
        print("💡 Dica: Verifique se as chaves de API estão corretas")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
