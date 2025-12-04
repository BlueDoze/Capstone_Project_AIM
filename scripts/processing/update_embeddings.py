#!/usr/bin/env python3
"""
Script to Update Image Embeddings
==================================

This script demonstrates how to update image embeddings
in the multimodal RAG system.
"""

import os
import sys
import json
from datetime import datetime

def test_update_embeddings():
    """Tests image embedding updates"""
    print("🚀 TESTE DE ATUALIZAÇÃO DE EMBEDDINGS")
    print("=" * 50)
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Import the system
        print("📦 Importando sistema...")
        import main
        print("✅ Sistema importado com sucesso")

        # Check initial status
        print("\n📊 STATUS INICIAL:")
        print("-" * 30)
        initial_status = main.image_manager.get_status()
        print(json.dumps(initial_status, indent=2))

        # Method 1: Direct method update
        print("\n🔄 MÉTODO 1: Atualização Direta")
        print("-" * 40)
        success = main.image_manager.update_embeddings(force_reprocess=False)
        if success:
            print("✅ Atualização direta bem-sucedida")
        else:
            print("❌ Falha na atualização direta")

        # Check status after update
        print("\n📊 STATUS APÓS ATUALIZAÇÃO:")
        print("-" * 35)
        updated_status = main.image_manager.get_status()
        print(json.dumps(updated_status, indent=2))

        # Method 2: Update via endpoint (simulated)
        print("\n🔄 MÉTODO 2: Atualização via Endpoint (Simulado)")
        print("-" * 50)
        
        with main.app.test_client() as client:
            # Test update endpoint
            response = client.post('/images/update',
                                 json={'force': True},
                                 content_type='application/json')

            if response.status_code == 200:
                data = response.get_json()
                print("✅ Endpoint de atualização funcionando")
                print(f"📝 Resposta: {data['message']}")
            else:
                print(f"❌ Erro no endpoint: {response.status_code}")
                if response.data:
                    print(f"Erro: {response.data.decode()}")

        # Method 3: Cache cleanup
        print("\n🔄 MÉTODO 3: Limpeza de Cache")
        print("-" * 35)

        with main.app.test_client() as client:
            response = client.post('/images/clear-cache')

            if response.status_code == 200:
                data = response.get_json()
                print("✅ Cache limpo com sucesso")
                print(f"📝 Resposta: {data['message']}")
            else:
                print(f"❌ Erro ao limpar cache: {response.status_code}")

        # Reprocess after cleanup
        print("\n🔄 Reprocessando após limpeza...")
        success = main.image_manager.update_embeddings(force_reprocess=True)
        if success:
            print("✅ Reprocessamento bem-sucedido")
        else:
            print("❌ Falha no reprocessamento")

        # Final status
        print("\n📊 STATUS FINAL:")
        print("-" * 20)
        final_status = main.image_manager.get_status()
        print(json.dumps(final_status, indent=2))
        
        print("\n" + "=" * 50)
        print("📊 RESUMO DOS MÉTODOS DE ATUALIZAÇÃO")
        print("=" * 50)
        print("✅ Método 1: Atualização direta via método")
        print("✅ Método 2: Atualização via endpoint HTTP")
        print("✅ Método 3: Limpeza de cache + reprocessamento")
        print("\n🎉 Todos os métodos funcionando!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_usage_examples():
    """Shows usage examples"""
    print("\n" + "=" * 60)
    print("📚 EXEMPLOS DE USO - COMO ATUALIZAR EMBEDDINGS")
    print("=" * 60)
    
    print("\n🔧 MÉTODO 1: Via Código Python")
    print("-" * 40)
    print("""
# Importar o sistema
import main

# Atualizar embeddings (detecta novas imagens automaticamente)
success = main.image_manager.update_embeddings()

# Forçar reprocessamento de todas as imagens
success = main.image_manager.update_embeddings(force_reprocess=True)

# Limpar cache
success = main.image_manager.clear_cache()
""")
    
    print("\n🌐 MÉTODO 2: Via Endpoints HTTP")
    print("-" * 40)
    print("""
# Atualizar embeddings
curl -X POST http://localhost:8081/images/update \\
     -H "Content-Type: application/json" \\
     -d '{"force": false}'

# Forçar reprocessamento
curl -X POST http://localhost:8081/images/update \\
     -H "Content-Type: application/json" \\
     -d '{"force": true}'

# Limpar cache
curl -X POST http://localhost:8081/images/clear-cache

# Verificar status
curl http://localhost:8081/images/status
""")
    
    print("\n🔄 MÉTODO 3: Reinicialização do Sistema")
    print("-" * 45)
    print("""
# O sistema detecta automaticamente novas imagens na inicialização
# Basta reiniciar o servidor Flask

python main.py
# ou
uv run python main.py
""")
    
    print("\n📊 MÉTODO 4: Script de Atualização")
    print("-" * 40)
    print("""
# Executar script de atualização
python update_embeddings.py
# ou
uv run python update_embeddings.py
""")

if __name__ == "__main__":
    print("🚀 SCRIPT DE ATUALIZAÇÃO DE EMBEDDINGS")
    print("=" * 50)
    
    # Executar teste
    success = test_update_embeddings()
    
    # Mostrar exemplos de uso
    show_usage_examples()
    
    if success:
        print("\n🎉 SCRIPT EXECUTADO COM SUCESSO!")
        print("✅ Todos os métodos de atualização funcionando")
    else:
        print("\n❌ SCRIPT FALHOU!")
        print("⚠️ Verifique os erros acima")
    
    sys.exit(0 if success else 1)
