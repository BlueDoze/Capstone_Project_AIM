#!/usr/bin/env python3
"""
Teste Específico: Resposta Real do Gemini vs Mock
===============================================

Este script testa se o modelo Gemini está realmente respondendo
ou se é apenas mock/simulação.
"""

import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.gemini_models import GeminiModelManager
from config.settings import RAGConfig
from config.environment import EnvironmentManager


def test_gemini_real_response():
    """Testa se o Gemini está realmente respondendo"""
    print("🧪 TESTE: Resposta Real do Gemini vs Mock")
    print("=" * 50)
    
    # Preparar configurações
    config = RAGConfig()
    env_manager = EnvironmentManager()
    env_manager.load_env_variables()
    config.PROJECT_ID = env_manager.get_project_id()
    
    print(f"📋 Configuração:")
    print(f"   - Project ID: {config.PROJECT_ID}")
    print(f"   - Gemini Model: {config.GEMINI_MODEL}")
    
    # Criar gerenciador Gemini
    gemini_manager = GeminiModelManager(
        project_id=config.PROJECT_ID,
        location=config.LOCATION
    )
    
    # Inicializar Vertex AI
    print("\n🚀 Inicializando Vertex AI...")
    vertex_success = gemini_manager.initialize_vertex_ai()
    
    if not vertex_success:
        print("❌ Falha na inicialização do Vertex AI")
        return False
    
    # Inicializar Gemini
    print("\n🤖 Inicializando Gemini 2.5 Pro...")
    gemini_success = gemini_manager.initialize_gemini_2_5_pro()
    
    if not gemini_success:
        print("❌ Falha na inicialização do Gemini")
        return False
    
    # Testar resposta real
    print("\n🧪 Testando resposta REAL do Gemini...")
    print("   Prompt: 'Responda apenas com: TESTE REAL'")
    
    try:
        response = gemini_manager.model.generate_content(
            "Responda apenas com: TESTE REAL",
            generation_config=gemini_manager.generation_config,
            safety_settings=gemini_manager.safety_settings
        )
        
        if response and response.text:
            print(f"✅ RESPOSTA REAL DO GEMINI: {response.text}")
            print("🎉 O modelo Gemini está funcionando de verdade!")
            return True
        else:
            print("❌ Resposta vazia do Gemini")
            return False
            
    except Exception as e:
        print(f"❌ ERRO REAL DO GEMINI: {e}")
        print("⚠️  O modelo Gemini NÃO está respondendo - é apenas mock/simulação")
        return False


def test_gemini_with_different_prompts():
    """Testa Gemini com diferentes prompts para confirmar"""
    print("\n🧪 TESTE ADICIONAL: Múltiplos Prompts")
    print("=" * 40)
    
    config = RAGConfig()
    env_manager = EnvironmentManager()
    env_manager.load_env_variables()
    config.PROJECT_ID = env_manager.get_project_id()
    
    gemini_manager = GeminiModelManager(
        project_id=config.PROJECT_ID,
        location=config.LOCATION
    )
    
    # Inicializar
    gemini_manager.initialize_vertex_ai()
    gemini_manager.initialize_gemini_2_5_pro()
    
    # Testar diferentes prompts
    test_prompts = [
        "Olá, como você está?",
        "Qual é a capital do Brasil?",
        "Conte uma piada",
        "1 + 1 = ?"
    ]
    
    success_count = 0
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Teste {i}: '{prompt}'")
        
        try:
            response = gemini_manager.model.generate_content(prompt)
            
            if response and response.text:
                print(f"✅ Resposta: {response.text[:100]}...")
                success_count += 1
            else:
                print("❌ Resposta vazia")
                
        except Exception as e:
            print(f"❌ Erro: {str(e)[:100]}...")
    
    print(f"\n📊 Resultado: {success_count}/{len(test_prompts)} prompts funcionaram")
    
    if success_count > 0:
        print("✅ Gemini está respondendo de verdade!")
        return True
    else:
        print("❌ Gemini não está respondendo - apenas mock")
        return False


def analyze_gemini_status():
    """Analisa o status atual do Gemini"""
    print("\n🔍 ANÁLISE: Status do Gemini")
    print("=" * 30)
    
    config = RAGConfig()
    env_manager = EnvironmentManager()
    env_manager.load_env_variables()
    config.PROJECT_ID = env_manager.get_project_id()
    
    print(f"📋 Informações do Projeto:")
    print(f"   - Project ID: {config.PROJECT_ID}")
    print(f"   - Tipo: {'REAL' if config.PROJECT_ID != 'test_project_id_here' else 'TESTE/MOCK'}")
    
    if config.PROJECT_ID == 'test_project_id_here':
        print("\n⚠️  DIAGNÓSTICO:")
        print("   - Project ID é de teste ('test_project_id_here')")
        print("   - Não há chaves de API reais configuradas")
        print("   - Gemini não pode responder sem credenciais válidas")
        print("   - Status: MOCK/SIMULAÇÃO")
    else:
        print("\n✅ DIAGNÓSTICO:")
        print("   - Project ID parece ser real")
        print("   - Pode ter chaves de API válidas")
        print("   - Gemini pode responder de verdade")
        print("   - Status: POTENCIALMENTE REAL")
    
    return config.PROJECT_ID != 'test_project_id_here'


def main():
    """Função principal de teste"""
    print("🚀 ANÁLISE: Gemini Real vs Mock")
    print("=" * 40)
    
    # Analisar status
    is_real_project = analyze_gemini_status()
    
    # Testar resposta
    real_response = test_gemini_real_response()
    
    # Teste adicional
    multiple_responses = test_gemini_with_different_prompts()
    
    # Resultado final
    print("\n📊 CONCLUSÃO FINAL")
    print("=" * 20)
    
    if real_response and multiple_responses:
        print("🎉 GEMINI ESTÁ RESPONDENDO DE VERDADE!")
        print("✅ Modelo real funcionando")
        print("✅ Respostas autênticas")
    elif is_real_project:
        print("⚠️  GEMINI PODE SER REAL, MAS COM PROBLEMAS:")
        print("❌ Project ID real mas sem resposta")
        print("💡 Verifique chaves de API e permissões")
    else:
        print("❌ GEMINI É APENAS MOCK/SIMULAÇÃO:")
        print("❌ Project ID de teste")
        print("❌ Sem chaves de API reais")
        print("❌ Não há resposta real do modelo")
        print("💡 Para resposta real, configure chaves válidas no .env")
    
    return real_response


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
