#!/usr/bin/env python3
"""
Teste da Etapa 1: Configuração
==============================

Este script testa o carregamento e validação das configurações do sistema RAG multimodal.
"""

import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config.settings import RAGConfig
from config.environment import EnvironmentManager


def test_configuration_loading():
    """Testa o carregamento de configurações"""
    print("🧪 TESTE 1: Carregamento de Configurações")
    print("=" * 50)
    
    # Criar instância de configuração
    config = RAGConfig()
    
    # Carregar variáveis de ambiente primeiro
    env_manager = EnvironmentManager()
    env_manager.load_env_variables()
    
    # Atualizar configuração com variáveis de ambiente
    config.PROJECT_ID = env_manager.get_project_id() or "test_project_id"
    
    # Exibir configurações
    config.display_config()
    
    # Validar configurações
    is_valid = config.validate_config()
    
    if is_valid:
        print("✅ Teste de configuração PASSOU")
    else:
        print("❌ Teste de configuração FALHOU")
    
    return is_valid


def test_environment_loading():
    """Testa o carregamento de variáveis de ambiente"""
    print("\n🧪 TESTE 2: Carregamento de Variáveis de Ambiente")
    print("=" * 50)
    
    # Criar gerenciador de ambiente
    env_manager = EnvironmentManager()
    
    # Tentar carregar arquivo .env
    env_loaded = env_manager.load_env_variables()
    
    # Exibir status das variáveis
    env_manager.display_env_status()
    
    # Validar variáveis obrigatórias
    required_valid = env_manager.validate_required_vars()
    
    # Obter configurações
    api_keys = env_manager.get_api_keys()
    optional_config = env_manager.get_optional_config()
    
    if env_loaded and required_valid:
        print("✅ Teste de ambiente PASSOU")
        return True
    else:
        print("❌ Teste de ambiente FALHOU")
        return False


def test_directory_creation():
    """Testa a criação de diretórios necessários"""
    print("\n🧪 TESTE 3: Criação de Diretórios")
    print("=" * 50)
    
    config = RAGConfig()
    
    # Criar diretórios
    directories_created = config.create_directories()
    
    if directories_created:
        print("✅ Teste de diretórios PASSOU")
        return True
    else:
        print("❌ Teste de diretórios FALHOU")
        return False


def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DA ETAPA 1: CONFIGURAÇÃO")
    print("=" * 60)
    
    # Executar testes
    test1_passed = test_configuration_loading()
    test2_passed = test_environment_loading()
    test3_passed = test_directory_creation()
    
    # Resultado final
    print("\n📊 RESULTADO DOS TESTES")
    print("=" * 30)
    print(f"Teste 1 (Configuração): {'✅ PASSOU' if test1_passed else '❌ FALHOU'}")
    print(f"Teste 2 (Ambiente): {'✅ PASSOU' if test2_passed else '❌ FALHOU'}")
    print(f"Teste 3 (Diretórios): {'✅ PASSOU' if test3_passed else '❌ FALHOU'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    
    if all_passed:
        print("\n🎉 TODOS OS TESTES PASSARAM! Etapa 1 concluída com sucesso.")
        print("✅ Pronto para próxima etapa: Inicialização de Modelos")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM. Verifique as configurações.")
        print("💡 Dica: Crie um arquivo .env com suas chaves de API")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
