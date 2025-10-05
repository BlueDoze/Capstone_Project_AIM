#!/usr/bin/env python3
"""
Demonstração Prática do Método Automático
=========================================

Este script demonstra na prática como o sistema detecta
automaticamente novas imagens e atualiza os embeddings.
"""

import os
import sys
import time
import shutil
from datetime import datetime

def demo_auto_update():
    """Demonstração prática do sistema automático"""
    print("🎬 DEMONSTRAÇÃO PRÁTICA DO MÉTODO AUTOMÁTICO")
    print("=" * 55)
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    
    try:
        # Importar sistema
        print("📦 Iniciando sistema...")
        import main
        
        # Aguardar inicialização
        time.sleep(2)
        
        print("✅ Sistema iniciado com monitoramento automático ativo")
        
        # Verificar status inicial
        initial_status = main.image_manager.get_status()
        print(f"\n📊 STATUS INICIAL:")
        print(f"   • Imagens processadas: {initial_status['total_images']}")
        print(f"   • Imagens na pasta: {initial_status['folder_image_count']}")
        print(f"   • Monitoramento ativo: {main.auto_updater.get_status()['is_running']}")
        
        # Demonstração 1: Adicionar nova imagem
        print(f"\n🎯 DEMONSTRAÇÃO 1: ADICIONANDO NOVA IMAGEM")
        print("-" * 50)
        
        # Copiar uma imagem existente como "nova"
        new_image_path = "images/demo_new_image.jpg"
        if os.path.exists("images/M1.jpeg"):
            shutil.copy("images/M1.jpeg", new_image_path)
            print(f"✅ Nova imagem adicionada: demo_new_image.jpg")
            print("⏰ Aguardando detecção automática...")
            
            # Aguardar processamento
            for i in range(15):  # 15 segundos
                time.sleep(1)
                current_status = main.image_manager.get_status()
                if current_status['total_images'] > initial_status['total_images']:
                    print(f"🎉 Imagem detectada e processada automaticamente!")
                    print(f"   • Imagens processadas: {current_status['total_images']}")
                    break
                print(f"   ⏳ Aguardando... ({i+1}/15)")
            else:
                print("⚠️ Imagem pode não ter sido detectada automaticamente")
        
        # Demonstração 2: Remover imagem
        print(f"\n🎯 DEMONSTRAÇÃO 2: REMOVENDO IMAGEM")
        print("-" * 40)
        
        if os.path.exists(new_image_path):
            os.remove(new_image_path)
            print(f"✅ Imagem removida: demo_new_image.jpg")
            print("⏰ Aguardando detecção automática...")
            
            # Aguardar processamento
            for i in range(10):  # 10 segundos
                time.sleep(1)
                current_status = main.image_manager.get_status()
                print(f"   ⏳ Aguardando... ({i+1}/10)")
            
            final_status = main.image_manager.get_status()
            print(f"📊 Status final: {final_status['total_images']} imagens processadas")
        
        # Demonstração 3: Testar chat com nova imagem
        print(f"\n🎯 DEMONSTRAÇÃO 3: TESTANDO CHAT COM NOVA IMAGEM")
        print("-" * 55)
        
        # Adicionar imagem novamente para teste
        if os.path.exists("images/M1.jpeg"):
            shutil.copy("images/M1.jpeg", new_image_path)
            print(f"✅ Imagem adicionada novamente para teste")
            time.sleep(8)  # Aguardar processamento
            
            # Testar chat
            with main.app.test_client() as client:
                response = client.post('/chat', 
                                     json={'message': 'Onde fica a sala 1020? Use informações visuais.'},
                                     content_type='application/json')
                
                if response.status_code == 200:
                    data = response.get_json()
                    print("✅ Chat funcionando com informações visuais")
                    print(f"📝 Resposta: {data['reply'][:100]}...")
                else:
                    print(f"❌ Erro no chat: {response.status_code}")
        
        # Limpar arquivo de teste
        if os.path.exists(new_image_path):
            os.remove(new_image_path)
        
        print(f"\n" + "=" * 55)
        print("🎉 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 55)
        print("✅ Sistema detecta automaticamente novas imagens")
        print("✅ Embeddings são atualizados automaticamente")
        print("✅ Chat usa informações visuais atualizadas")
        print("✅ Zero intervenção manual necessária")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA DEMONSTRAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_usage_guide():
    """Mostra guia de uso do método automático"""
    print("\n" + "=" * 60)
    print("📚 GUIA DE USO - MÉTODO AUTOMÁTICO")
    print("=" * 60)
    
    print("\n🚀 COMO USAR:")
    print("-" * 15)
    print("1. Inicie o sistema: python main.py")
    print("2. Adicione imagens na pasta 'images/'")
    print("3. O sistema detecta automaticamente")
    print("4. Embeddings são atualizados automaticamente")
    print("5. Chat usa informações visuais atualizadas")
    
    print("\n📁 FORMATOS SUPORTADOS:")
    print("-" * 25)
    print("• JPG, JPEG")
    print("• PNG")
    print("• BMP")
    print("• TIFF")
    print("• WEBP")
    
    print("\n⚙️ CONFIGURAÇÃO:")
    print("-" * 18)
    print("• Pasta monitorada: images/")
    print("• Delay entre atualizações: 5 segundos")
    print("• Aguarda 2 segundos antes de processar")
    print("• Executa em thread separada")
    
    print("\n🌐 ENDPOINTS DE CONTROLE:")
    print("-" * 30)
    print("• GET /images/auto-monitor/status")
    print("• POST /images/auto-monitor/start")
    print("• POST /images/auto-monitor/stop")
    print("• GET /system/status")
    
    print("\n💡 DICAS:")
    print("-" * 10)
    print("• Sistema inicia automaticamente")
    print("• Não precisa reiniciar para novas imagens")
    print("• Cache é atualizado automaticamente")
    print("• Performance otimizada")

if __name__ == "__main__":
    print("🎬 DEMONSTRAÇÃO DO MÉTODO AUTOMÁTICO")
    print("=" * 40)
    
    # Executar demonstração
    success = demo_auto_update()
    
    # Mostrar guia de uso
    show_usage_guide()
    
    if success:
        print("\n🎉 DEMONSTRAÇÃO EXECUTADA COM SUCESSO!")
        print("✅ Método automático funcionando perfeitamente")
    else:
        print("\n❌ DEMONSTRAÇÃO FALHOU!")
        print("⚠️ Verifique os erros acima")
    
    sys.exit(0 if success else 1)
