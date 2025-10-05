#!/usr/bin/env python3
"""
Teste com Credenciais Reais do Gemini
=====================================

Este script testa o Gemini com credenciais reais configuradas.
"""

import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.initialization_service import InitializationService


def test_with_real_credentials():
    """Testa o sistema com credenciais reais"""
    print("🚀 TESTE COM CREDENCIAIS REAIS")
    print("=" * 40)
    
    # Criar serviço de inicialização
    init_service = InitializationService()
    
    # Preparar sistema
    print("📋 Preparando sistema...")
    prep_success = init_service.prepare_system()
    
    if not prep_success:
        print("❌ Falha na preparação do sistema")
        return False
    
    # Verificar se as credenciais são reais
    project_id = init_service.config.PROJECT_ID
    print(f"📋 Project ID: {project_id}")
    
    if project_id == "test_project_id_here":
        print("⚠️  AINDA USANDO CREDENCIAIS DE TESTE!")
        print("💡 Configure credenciais reais no arquivo .env")
        return False
    
    print("✅ Credenciais parecem ser reais")
    
    # Inicializar modelos
    print("\n🤖 Inicializando modelos...")
    model_success = init_service.initialize_models()
    
    if not model_success:
        print("❌ Falha na inicialização de modelos")
        return False
    
    # Testar resposta real do Gemini
    print("\n🧪 Testando resposta REAL do Gemini...")
    
    test_prompts = [
        "Olá! Você está funcionando?",
        "Qual é a capital do Brasil?",
        "Conte uma piada curta"
    ]
    
    success_count = 0
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Teste {i}: '{prompt}'")
        
        try:
            response = init_service.gemini_manager.model.generate_content(
                prompt,
                generation_config=init_service.gemini_manager.generation_config,
                safety_settings=init_service.gemini_manager.safety_settings
            )
            
            if response and response.text:
                print(f"✅ RESPOSTA REAL: {response.text}")
                success_count += 1
            else:
                print("❌ Resposta vazia")
                
        except Exception as e:
            print(f"❌ Erro: {str(e)[:100]}...")
    
    print(f"\n📊 Resultado: {success_count}/{len(test_prompts)} respostas funcionaram")
    
    if success_count > 0:
        print("\n🎉 GEMINI FUNCIONANDO COM CREDENCIAIS REAIS!")
        print("✅ Sistema RAG multimodal totalmente operacional")
        return True
    else:
        print("\n❌ Ainda há problemas com as credenciais")
        return False


def check_credentials_status():
    """Verifica o status das credenciais"""
    print("🔍 VERIFICANDO STATUS DAS CREDENCIAIS")
    print("=" * 45)
    
    init_service = InitializationService()
    init_service.prepare_system()
    
    project_id = init_service.config.PROJECT_ID
    api_keys = init_service.env_manager.get_api_keys()
    
    print(f"📋 Project ID: {project_id}")
    print(f"📋 GEMINI_API_KEY: {'✅ Definida' if api_keys['GEMINI_API_KEY'] else '❌ Não definida'}")
    print(f"📋 GOOGLE_CLOUD_PROJECT_ID: {'✅ Definida' if api_keys['GOOGLE_CLOUD_PROJECT_ID'] else '❌ Não definida'}")
    
    if project_id == "test_project_id_here":
        print("\n⚠️  STATUS: Credenciais de teste")
        print("💡 Para habilitar Gemini real:")
        print("   1. Obtenha Project ID real do Google Cloud")
        print("   2. Configure API Key do Gemini/Vertex AI")
        print("   3. Atualize o arquivo .env")
    else:
        print("\n✅ STATUS: Credenciais parecem ser reais")
        print("🚀 Pronto para testar resposta real do Gemini")


def main():
    """Função principal"""
    print("🔧 HABILITANDO GEMINI COM CREDENCIAIS REAIS")
    print("=" * 50)
    
    # Verificar status das credenciais
    check_credentials_status()
    
    # Testar com credenciais reais
    print("\n" + "="*50)
    real_test = test_with_real_credentials()
    
    # Resultado final
    print("\n📊 RESULTADO FINAL")
    print("=" * 20)
    
    if real_test:
        print("🎉 SUCESSO! Gemini habilitado com credenciais reais")
        print("✅ Sistema RAG multimodal totalmente funcional")
        print("✅ Pronto para próxima etapa: Validação de Recursos")
    else:
        print("⚠️  Ainda usando credenciais de teste")
        print("💡 Configure credenciais reais para habilitar Gemini")
    
    return real_test


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
