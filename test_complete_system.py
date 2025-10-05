#!/usr/bin/env python3
"""
Teste Completo do Sistema RAG Multimodal
========================================

Este script executa testes completos de todas as funcionalidades
implementadas no sistema RAG multimodal, incluindo todas as etapas.
"""

import sys
import os
import time
from datetime import datetime

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.validation_service import ValidationService
from services.initialization_service import InitializationService
from config.settings import RAGConfig
from config.environment import EnvironmentManager


def test_etapa_1_configuration():
    """Testa Etapa 1: Configuração"""
    print("🧪 TESTE ETAPA 1: CONFIGURAÇÃO")
    print("=" * 40)
    
    try:
        # Testar configurações
        config = RAGConfig()
        env_manager = EnvironmentManager()
        
        # Carregar ambiente
        env_loaded = env_manager.load_env_variables()
        config.PROJECT_ID = env_manager.get_project_id()
        
        # Validar configurações
        config_valid = config.validate_config()
        env_valid = env_manager.validate_required_vars()
        dirs_created = config.create_directories()
        
        success = config_valid and env_valid and dirs_created
        
        print(f"✅ Configuração: {'PASSOU' if config_valid else 'FALHOU'}")
        print(f"✅ Ambiente: {'PASSOU' if env_valid else 'FALHOU'}")
        print(f"✅ Diretórios: {'PASSOU' if dirs_created else 'FALHOU'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro na Etapa 1: {e}")
        return False


def test_etapa_2_initialization():
    """Testa Etapa 2: Inicialização de Modelos"""
    print("\n🧪 TESTE ETAPA 2: INICIALIZAÇÃO DE MODELOS")
    print("=" * 50)
    
    try:
        # Criar serviço de inicialização
        init_service = InitializationService()
        
        # Preparar sistema
        prep_success = init_service.prepare_system()
        if not prep_success:
            print("❌ Falha na preparação")
            return False
        
        # Inicializar modelos
        model_success = init_service.initialize_models()
        if not model_success:
            print("❌ Falha na inicialização de modelos")
            return False
        
        # Validar recursos
        resource_success = init_service.validate_resources()
        if not resource_success:
            print("❌ Falha na validação de recursos")
            return False
        
        # Testar respostas dos modelos
        print("\n🤖 Testando respostas dos modelos...")
        
        # Testar Gemini
        gemini_test = init_service.gemini_manager.test_gemini_response(
            "Responda apenas: ETAPA 2 FUNCIONANDO"
        )
        
        # Testar embedding de texto
        text_embedding_test = init_service.embedding_manager.test_text_embedding_generation(
            "Teste da Etapa 2"
        )
        
        print(f"✅ Gemini: {'PASSOU' if gemini_test else 'FALHOU'}")
        print(f"✅ Embedding Texto: {'PASSOU' if text_embedding_test else 'FALHOU'}")
        
        success = prep_success and model_success and resource_success and gemini_test and text_embedding_test
        
        return success
        
    except Exception as e:
        print(f"❌ Erro na Etapa 2: {e}")
        return False


def test_etapa_3_resource_validation():
    """Testa Etapa 3: Validação de Recursos"""
    print("\n🧪 TESTE ETAPA 3: VALIDAÇÃO DE RECURSOS")
    print("=" * 50)
    
    try:
        # Criar serviço de validação
        validation_service = ValidationService()
        
        # Executar validação completa
        results = validation_service.run_complete_validation()
        
        success = results.get('success', False)
        
        print(f"✅ Validação Completa: {'PASSOU' if success else 'FALHOU'}")
        
        if 'summary' in results:
            summary = results['summary']
            print(f"📊 Taxa de Sucesso: {summary.get('success_rate', 0):.1f}%")
            print(f"📊 Testes Aprovados: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro na Etapa 3: {e}")
        return False


def test_integration_complete():
    """Testa integração completa de todas as etapas"""
    print("\n🧪 TESTE INTEGRAÇÃO COMPLETA")
    print("=" * 35)
    
    try:
        # Criar serviço de validação (que inclui tudo)
        validation_service = ValidationService()
        
        # Executar validação completa
        results = validation_service.run_complete_validation()
        
        success = results.get('success', False)
        
        # Exibir resultados detalhados
        print(f"✅ Preparação: {'PASSOU' if results.get('preparation') else 'FALHOU'}")
        print(f"✅ Inicialização: {'PASSOU' if results.get('initialization') else 'FALHOU'}")
        print(f"✅ End-to-End: {'PASSOU' if results.get('end_to_end') else 'FALHOU'}")
        
        if 'summary' in results:
            summary = results['summary']
            print(f"📊 Taxa de Sucesso Geral: {summary.get('success_rate', 0):.1f}%")
            
            # Mostrar erros se houver
            if summary.get('errors'):
                print(f"\n❌ Erros encontrados ({len(summary['errors'])}):")
                for error in summary['errors'][:3]:  # Mostrar apenas os primeiros 3
                    print(f"   - {error}")
                if len(summary['errors']) > 3:
                    print(f"   ... e mais {len(summary['errors']) - 3} erros")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro na integração completa: {e}")
        return False


def test_performance_metrics():
    """Testa métricas de performance"""
    print("\n🧪 TESTE MÉTRICAS DE PERFORMANCE")
    print("=" * 40)
    
    try:
        # Medir tempo de inicialização
        start_time = time.time()
        
        init_service = InitializationService()
        init_service.prepare_system()
        init_service.initialize_models()
        
        init_time = time.time() - start_time
        
        # Medir tempo de resposta do Gemini
        start_time = time.time()
        
        gemini_response = init_service.gemini_manager.test_gemini_response(
            "Responda rapidamente: PERFORMANCE TEST"
        )
        
        response_time = time.time() - start_time
        
        # Medir tempo de embedding
        start_time = time.time()
        
        embedding_response = init_service.embedding_manager.test_text_embedding_generation(
            "Performance test for embedding generation"
        )
        
        embedding_time = time.time() - start_time
        
        print(f"⏱️  Tempo de Inicialização: {init_time:.2f}s")
        print(f"⏱️  Tempo de Resposta Gemini: {response_time:.2f}s")
        print(f"⏱️  Tempo de Embedding: {embedding_time:.2f}s")
        
        # Avaliar performance
        performance_ok = (
            init_time < 30 and  # Inicialização em menos de 30s
            response_time < 30 and  # Resposta em menos de 30s
            embedding_time < 5  # Embedding em menos de 5s
        )
        
        print(f"✅ Performance: {'PASSOU' if performance_ok else 'FALHOU'}")
        
        return performance_ok
        
    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")
        return False


def main():
    """Função principal de teste completo"""
    print("🚀 TESTE COMPLETO DO SISTEMA RAG MULTIMODAL")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Executar todos os testes
    test_results = {}
    
    # Etapa 1: Configuração
    test_results['etapa_1'] = test_etapa_1_configuration()
    
    # Etapa 2: Inicialização
    test_results['etapa_2'] = test_etapa_2_initialization()
    
    # Etapa 3: Validação de Recursos
    test_results['etapa_3'] = test_etapa_3_resource_validation()
    
    # Integração Completa
    test_results['integracao'] = test_integration_complete()
    
    # Performance
    test_results['performance'] = test_performance_metrics()
    
    # Resultado final
    print(f"\n{'='*60}")
    print("📊 RESULTADO FINAL DOS TESTES")
    print(f"{'='*60}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"✅ Etapa 1 (Configuração): {'PASSOU' if test_results['etapa_1'] else 'FALHOU'}")
    print(f"✅ Etapa 2 (Inicialização): {'PASSOU' if test_results['etapa_2'] else 'FALHOU'}")
    print(f"✅ Etapa 3 (Validação): {'PASSOU' if test_results['etapa_3'] else 'FALHOU'}")
    print(f"✅ Integração Completa: {'PASSOU' if test_results['integracao'] else 'FALHOU'}")
    print(f"✅ Performance: {'PASSOU' if test_results['performance'] else 'FALHOU'}")
    
    print(f"\n📈 Taxa de Sucesso Geral: {success_rate:.1f}%")
    print(f"📊 Testes Aprovados: {passed_tests}/{total_tests}")
    
    if success_rate == 100:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema RAG multimodal totalmente funcional")
        print("✅ Pronto para uso em produção")
        print("✅ Todas as etapas implementadas com sucesso")
    elif success_rate >= 80:
        print("\n⚠️  MAIORIA DOS TESTES PASSOU")
        print("💡 Alguns problemas menores precisam ser resolvidos")
    else:
        print("\n❌ MÚLTIPLOS TESTES FALHARAM")
        print("🔧 Sistema precisa de correções significativas")
    
    print(f"\n{'='*60}")
    print("🏁 TESTE COMPLETO FINALIZADO")
    print(f"{'='*60}")
    
    return success_rate == 100


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
