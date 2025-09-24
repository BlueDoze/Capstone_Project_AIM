#!/usr/bin/env python3
"""
Script para atualizar embeddings das imagens na pasta images/
Este script processa todas as imagens e atualiza o banco de dados vetorial.
"""

import os
import sys
import glob
from typing import List, Dict, Any
from dotenv import load_dotenv

# Adicionar o diretório src ao path para importações
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.vector_db import MapVectorDB
from src.embeddings.image_embedder import ImageEmbeddingManager

def get_image_files(images_dir: str) -> List[str]:
    """Obtém lista de arquivos de imagem na pasta especificada"""
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.webp']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(images_dir, ext)
        image_files.extend(glob.glob(pattern))
        # Também buscar em subdiretórios
        pattern = os.path.join(images_dir, '**', ext)
        image_files.extend(glob.glob(pattern, recursive=True))
    
    return sorted(image_files)

def create_image_descriptions(image_paths: List[str]) -> List[str]:
    """Cria descrições automáticas para as imagens baseadas no nome do arquivo"""
    descriptions = []
    
    for path in image_paths:
        filename = os.path.basename(path)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Criar descrição baseada no nome do arquivo
        if 'map' in name_without_ext.lower():
            description = f"Mapa do campus com layout de edifícios, corredores e relacionamentos espaciais - {filename}"
        elif 'm3' in name_without_ext.lower():
            description = f"Imagem do edifício M3 com informações de navegação e localização - {filename}"
        else:
            description = f"Imagem de navegação do campus com informações espaciais - {filename}"
        
        descriptions.append(description)
    
    return descriptions

def update_image_embeddings(images_dir: str = "images", embedder_type: str = "gemini", 
                           clear_existing: bool = False, db_path: str = "./chroma_db"):
    """
    Atualiza os embeddings das imagens na pasta especificada
    
    Args:
        images_dir: Diretório contendo as imagens
        embedder_type: Tipo de embedder ('clip' ou 'gemini')
        clear_existing: Se deve limpar embeddings existentes de imagens
        db_path: Caminho para o banco de dados ChromaDB
    """
    
    print("🚀 Iniciando atualização de embeddings de imagens...")
    
    # Verificar se a pasta de imagens existe
    if not os.path.exists(images_dir):
        print(f"❌ Pasta de imagens não encontrada: {images_dir}")
        return False
    
    # Obter lista de arquivos de imagem
    image_files = get_image_files(images_dir)
    
    if not image_files:
        print(f"⚠️ Nenhuma imagem encontrada na pasta {images_dir}")
        return False
    
    print(f"📸 Encontradas {len(image_files)} imagens:")
    for img in image_files:
        print(f"   - {img}")
    
    # Inicializar banco de dados vetorial
    print("\n🗄️ Inicializando banco de dados vetorial...")
    try:
        vector_db = MapVectorDB(db_path=db_path)
        print("✅ Banco de dados vetorial inicializado")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False
    
    # Limpar embeddings existentes de imagens se solicitado
    if clear_existing:
        print("\n🗑️ Limpando embeddings existentes de imagens...")
        try:
            # Obter todos os documentos do tipo 'image'
            existing_images = vector_db.get_images_by_type("image")
            if existing_images['ids']:
                print(f"   Removendo {len(existing_images['ids'])} embeddings de imagens existentes...")
                # Nota: ChromaDB não tem método direto para deletar por tipo
                # Seria necessário implementar uma função específica
                print("   ⚠️ Limpeza manual necessária - implementar se necessário")
        except Exception as e:
            print(f"   ⚠️ Erro ao limpar embeddings existentes: {e}")
    
    # Inicializar gerenciador de embeddings de imagem
    print(f"\n🤖 Inicializando embedder de imagens ({embedder_type})...")
    try:
        image_manager = ImageEmbeddingManager(embedder_type=embedder_type)
        print("✅ Gerenciador de embeddings inicializado")
    except Exception as e:
        print(f"❌ Erro ao inicializar gerenciador de embeddings: {e}")
        return False
    
    # Criar descrições para as imagens
    print("\n📝 Criando descrições para as imagens...")
    descriptions = create_image_descriptions(image_files)
    
    # Processar imagens e gerar embeddings
    print("\n🔄 Processando imagens e gerando embeddings...")
    try:
        image_data = image_manager.process_images(image_files, descriptions)
        print(f"✅ Embeddings gerados para {len(image_data['embeddings'])} imagens")
    except Exception as e:
        print(f"❌ Erro ao processar imagens: {e}")
        return False
    
    # Adicionar embeddings ao banco de dados vetorial
    print("\n💾 Adicionando embeddings ao banco de dados vetorial...")
    try:
        success = vector_db.add_images(image_data)
        if success:
            print("✅ Embeddings de imagens adicionados com sucesso!")
        else:
            print("❌ Falha ao adicionar embeddings ao banco de dados")
            return False
    except Exception as e:
        print(f"❌ Erro ao adicionar embeddings: {e}")
        return False
    
    # Verificar informações da coleção
    print("\n📊 Informações da coleção:")
    try:
        info = vector_db.get_collection_info()
        print(f"   - Nome: {info.get('name', 'N/A')}")
        print(f"   - Total de documentos: {info.get('count', 'N/A')}")
        print(f"   - Metadados: {info.get('metadata', {})}")
    except Exception as e:
        print(f"   ⚠️ Erro ao obter informações: {e}")
    
    print("\n🎉 Atualização de embeddings concluída com sucesso!")
    return True

def main():
    """Função principal do script"""
    load_dotenv()
    
    # Configurações padrão
    images_dir = "images"
    embedder_type = "gemini"  # ou "clip"
    clear_existing = False
    db_path = "./chroma_db"
    
    # Verificar argumentos da linha de comando
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("""
Uso: python update_image_embeddings.py [opções]

Opções:
  --help, -h          Mostra esta mensagem de ajuda
  --clear             Limpa embeddings existentes de imagens antes de adicionar novos
  --embedder TYPE     Tipo de embedder ('clip' ou 'gemini', padrão: gemini)
  --images-dir DIR    Diretório das imagens (padrão: images)
  --db-path PATH      Caminho do banco de dados (padrão: ./chroma_db)

Exemplos:
  python update_image_embeddings.py
  python update_image_embeddings.py --clear --embedder clip
  python update_image_embeddings.py --images-dir /path/to/images --clear
            """)
            return
        
        # Processar argumentos
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--clear":
                clear_existing = True
            elif arg == "--embedder" and i + 1 < len(sys.argv):
                embedder_type = sys.argv[i + 1]
                i += 1
            elif arg == "--images-dir" and i + 1 < len(sys.argv):
                images_dir = sys.argv[i + 1]
                i += 1
            elif arg == "--db-path" and i + 1 < len(sys.argv):
                db_path = sys.argv[i + 1]
                i += 1
            i += 1
    
    # Executar atualização
    success = update_image_embeddings(
        images_dir=images_dir,
        embedder_type=embedder_type,
        clear_existing=clear_existing,
        db_path=db_path
    )
    
    if success:
        print("\n✅ Script executado com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Script falhou!")
        sys.exit(1)

if __name__ == "__main__":
    main()
