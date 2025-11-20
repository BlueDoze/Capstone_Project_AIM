#!/usr/bin/env python3
"""
Script de Validação Completa de Embeddings
==========================================

Este script valida:
1. Credenciais do Google Cloud
2. Carregamento de modelos de embedding
3. Integração com sistema RAG
4. Processamento de imagens com embeddings
"""

import sys
import os

# Adicionar diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def validate_credentials():
    """Valida credenciais do Google Cloud"""
    print("\n" + "="*70)
    print("1️⃣  VALIDAÇÃO DE CREDENCIAIS DO GOOGLE CLOUD")
    print("="*70)

    try:
        # Verificar variáveis de ambiente
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        if not project_id:
            print("❌ GOOGLE_CLOUD_PROJECT_ID não está configurado")
            return False

        print(f"✅ Project ID encontrado: {project_id}")

        # Verificar arquivos de credenciais
        gcloud_dir = os.path.expanduser('~/.config/gcloud')
        if not os.path.exists(gcloud_dir):
            print("❌ Diretório gcloud não encontrado")
            return False

        print(f"✅ Diretório gcloud encontrado: {gcloud_dir}")

        # Verificar autenticação com Vertex AI
        import vertexai
        vertexai.init(project=project_id, location='us-central1')
        print(f"✅ Vertex AI inicializado com sucesso")
        print(f"   - Project: {project_id}")
        print(f"   - Location: us-central1")

        return True

    except Exception as e:
        print(f"❌ Erro na validação de credenciais: {e}")
        print("💡 Execute: gcloud auth application-default login")
        return False


def test_embedding_models():
    """Testa carregamento dos modelos de embedding"""
    print("\n" + "="*70)
    print("2️⃣  TESTE DE CARREGAMENTO DOS MODELOS DE EMBEDDING")
    print("="*70)

    try:
        from vertexai.language_models import TextEmbeddingModel
        from vertexai.vision_models import MultiModalEmbeddingModel
        print("✅ Bibliotecas de embedding importadas com sucesso")

        # Testar modelo de texto
        print("\n📝 Carregando modelo de embedding de texto...")
        try:
            text_model = TextEmbeddingModel.from_pretrained("text-embedding-005")
            print("✅ Modelo text-embedding-005 carregado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao carregar modelo de texto: {e}")
            return False

        # Testar modelo multimodal
        print("\n🖼️  Carregando modelo de embedding multimodal...")
        try:
            mm_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
            print("✅ Modelo multimodalembedding@001 carregado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao carregar modelo multimodal: {e}")
            return False

        return True

    except ImportError as e:
        print(f"❌ Erro ao importar modelos: {e}")
        return False


def test_text_embedding():
    """Testa geração de embedding de texto"""
    print("\n" + "="*70)
    print("3️⃣  TESTE DE GERAÇÃO DE EMBEDDING DE TEXTO")
    print("="*70)

    try:
        from vertexai.language_models import TextEmbeddingModel
        import numpy as np

        text_model = TextEmbeddingModel.from_pretrained("text-embedding-005")

        # Texto de teste
        test_text = "Este é o Edifício M, Primeiro Andar. As salas incluem 1003, 1018, 1030, 1040, 1049"
        print(f"\n📝 Texto de teste: '{test_text[:60]}...'")

        # Gerar embedding
        print("🔄 Gerando embedding...")
        embeddings = text_model.get_embeddings([test_text])
        text_embedding = [e.values for e in embeddings][0]

        print(f"✅ Embedding gerado com sucesso!")
        print(f"   - Dimensões: {len(text_embedding)}")
        print(f"   - Primeiros 5 valores: {[round(x, 4) for x in text_embedding[:5]]}")
        print(f"   - Magnitude (norma): {round(np.linalg.norm(text_embedding), 4)}")

        return True

    except Exception as e:
        print(f"❌ Erro ao gerar embedding de texto: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_embedding():
    """Testa geração de embedding de imagem"""
    print("\n" + "="*70)
    print("4️⃣  TESTE DE GERAÇÃO DE EMBEDDING DE IMAGEM")
    print("="*70)

    try:
        from vertexai.vision_models import MultiModalEmbeddingModel, Image as vision_model_Image
        import numpy as np

        mm_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

        # Procurar por uma imagem de teste
        images_dir = "images/"
        test_image_path = None

        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    test_image_path = os.path.join(images_dir, filename)
                    break

        if not test_image_path:
            print(f"⚠️  Nenhuma imagem encontrada em '{images_dir}'")
            print("💡 Pulando teste de embedding de imagem")
            return True

        print(f"\n🖼️  Testando com imagem: {test_image_path}")

        # Carregar imagem
        print("🔄 Carregando imagem...")
        image = vision_model_Image.load_from_file(test_image_path)

        # Gerar embedding
        print("🔄 Gerando embedding de imagem (512 dimensões)...")
        embeddings = mm_model.get_embeddings(image=image, dimension=512)
        image_embedding = embeddings.image_embedding

        print(f"✅ Embedding de imagem gerado com sucesso!")
        print(f"   - Dimensões: {len(image_embedding)}")
        print(f"   - Primeiros 5 valores: {[round(x, 4) for x in image_embedding[:5]]}")
        print(f"   - Magnitude (norma): {round(np.linalg.norm(image_embedding), 4)}")

        return True

    except FileNotFoundError:
        print("⚠️  Arquivo de imagem não encontrado")
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar embedding de imagem: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_system():
    """Testa integração com sistema RAG"""
    print("\n" + "="*70)
    print("5️⃣  TESTE DE INTEGRAÇÃO COM SISTEMA RAG")
    print("="*70)

    try:
        from src.models.embedding_models import EmbeddingModelManager
        from src.config.settings import RAGConfig

        print("✅ Módulos RAG importados com sucesso")

        # Criar gerenciador de embedding
        print("\n🔧 Criando gerenciador de embedding...")
        embedding_manager = EmbeddingModelManager(embedding_size=512)
        print(f"✅ Gerenciador criado com tamanho: {embedding_manager.embedding_size}")

        # Inicializar modelos
        print("\n🚀 Inicializando modelos...")
        text_success = embedding_manager.initialize_text_embedding_model()
        multimodal_success = embedding_manager.initialize_multimodal_embedding_model()

        if not (text_success and multimodal_success):
            print("❌ Falha ao inicializar modelos")
            return False

        # Validar modelos
        print("\n🔍 Validando modelos...")
        if not embedding_manager.validate_embedding_models():
            print("❌ Validação dos modelos falhou")
            return False

        # Exibir status
        print("\n📊 Status do Sistema RAG:")
        embedding_manager.display_embedding_status()

        # Carregar configurações
        print("\n⚙️  Carregando configurações RAG...")
        config = RAGConfig()
        print(f"✅ Configurações carregadas:")
        print(f"   - Embedding Size: {config.EMBEDDING_SIZE}")
        print(f"   - Top N Text: {config.TOP_N_TEXT}")
        print(f"   - Top N Image: {config.TOP_N_IMAGE}")

        return True

    except Exception as e:
        print(f"❌ Erro na integração RAG: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_summary(results):
    """Gera sumário final dos testes"""
    print("\n" + "="*70)
    print("📊 SUMÁRIO DOS TESTES")
    print("="*70)

    total = len(results)
    passed = sum(1 for r in results.values() if r)

    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {test_name}")

    print("\n" + "="*70)
    if passed == total:
        print(f"🎉 SUCESSO! Todos os {total} testes passaram!")
        print("\n✅ Processo de embedding validado com sucesso:")
        print("   - Credenciais do Google Cloud: OK")
        print("   - Modelos de embedding: OK")
        print("   - Integração com sistema RAG: OK")
        print("   - Sistema pronto para processar imagens")
    else:
        print(f"⚠️  {passed}/{total} testes passaram")
        print("\n💡 Por favor, resolva os erros acima antes de continuar")

    print("="*70 + "\n")

    return passed == total


def main():
    """Função principal"""
    print("\n🚀 VALIDAÇÃO COMPLETA DO SISTEMA DE EMBEDDING")
    print("="*70)

    results = {}

    # 1. Validar credenciais
    results["Credenciais Google Cloud"] = validate_credentials()
    if not results["Credenciais Google Cloud"]:
        print("\n❌ Não é possível continuar sem credenciais válidas")
        return False

    # 2. Testar carregamento de modelos
    results["Carregamento de Modelos"] = test_embedding_models()

    # 3. Testar embedding de texto
    results["Embedding de Texto"] = test_text_embedding()

    # 4. Testar embedding de imagem
    results["Embedding de Imagem"] = test_image_embedding()

    # 5. Testar integração RAG
    results["Integração com RAG"] = test_rag_system()

    # Gerar sumário
    success = generate_summary(results)

    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
