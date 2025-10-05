#!/usr/bin/env python3
"""
Sistema Completo de RAG Multimodal com Gemini
==============================================

Este script implementa um sistema completo de Retrieval-Augmented Generation (RAG) multimodal
que processa documentos PDF, extrai imagens, gera embeddings e realiza análises contextuais
usando modelos Gemini do Google Cloud Vertex AI.

Funcionalidades:
- Processamento de PDFs e extração de texto/imagens
- Geração de embeddings para texto e imagens
- Busca por similaridade usando embeddings
- Análise contextual com modelos Gemini
- Sistema de citações e referências
- Processamento direto de imagens de pasta

Autor: Sistema Multimodal RAG
Data: 2025
"""

import os
import sys
import glob
import time
import argparse
import subprocess
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from pathlib import Path

# Imports principais
import numpy as np
import pandas as pd
import PIL
import fitz
import requests
from IPython.display import display

# Google Cloud e Vertex AI
import vertexai
from vertexai.generative_models import (
    Content,
    GenerationConfig,
    GenerationResponse,
    GenerativeModel,
    HarmCategory,
    HarmBlockThreshold,
    Image,
    Part,
)
from vertexai.language_models import TextEmbeddingModel
from vertexai.vision_models import MultiModalEmbeddingModel, Image as vision_model_Image

# Formatação e utilidades
from rich import print as rich_print
from rich.markdown import Markdown as rich_Markdown
from IPython.display import Markdown, display

# =============================================================================
# CONFIGURAÇÃO E INICIALIZAÇÃO
# =============================================================================

class Config:
    """Configurações do sistema"""
    def __init__(self):
        self.PROJECT_ID = "gen-lang-client-0303567819"
        self.LOCATION = "us-central1"
        self.EMBEDDING_SIZE = 512
        self.TOP_N_TEXT = 10
        self.TOP_N_IMAGE = 5
        self.CHARACTER_LIMIT = 1000
        self.OVERLAP = 100
        self.IMAGE_SAVE_DIR = "images/"
        self.PDF_FOLDER_PATH = "map/"
        
    def update_from_args(self, args):
        """Atualiza configurações a partir de argumentos da linha de comando"""
        if args.project_id:
            self.PROJECT_ID = args.project_id
        if args.location:
            self.LOCATION = args.location
        if args.embedding_size:
            self.EMBEDDING_SIZE = args.embedding_size
        if args.image_dir:
            self.IMAGE_SAVE_DIR = args.image_dir
        if args.pdf_dir:
            self.PDF_FOLDER_PATH = args.pdf_dir

# Instância global de configuração
config = Config()

# =============================================================================
# FUNÇÕES DE UTILITÁRIOS (do multimodal_qa_with_rag_utils.py)
# =============================================================================

def set_global_variable(variable_name: str, value: any) -> None:
    """
    Sets the value of a global variable.

    Args:
        variable_name: The name of the global variable (as a string).
        value: The value to assign to the global variable. This can be of any type.
    """
    global_vars = globals()  # Get a dictionary of global variables
    global_vars[variable_name] = value 

def get_text_embedding_from_text_embedding_model(
    text: str,
    return_array: Optional[bool] = False,
) -> list:
    """
    Generates a numerical text embedding from a provided text input using a text embedding model.

    Args:
        text: The input text string to be embedded.
        return_array: If True, returns the embedding as a NumPy array.
                      If False, returns the embedding as a list. (Default: False)

    Returns:
        list or numpy.ndarray: A 768-dimensional vector representation of the input text.
                               The format (list or NumPy array) depends on the
                               value of the 'return_array' parameter.
    """
    embeddings = text_embedding_model.get_embeddings([text])
    text_embedding = [embedding.values for embedding in embeddings][0]

    if return_array:
        text_embedding = np.fromiter(text_embedding, dtype=float)

    # returns 768 dimensional array
    return text_embedding

def get_image_embedding_from_multimodal_embedding_model(
    image_uri: str,
    embedding_size: int = 512,
    text: Optional[str] = None,
    return_array: Optional[bool] = False,
) -> list:
    """Extracts an image embedding from a multimodal embedding model.
    The function can optionally utilize contextual text to refine the embedding.

    Args:
        image_uri (str): The URI (Uniform Resource Identifier) of the image to process.
        text (Optional[str]): Optional contextual text to guide the embedding generation. Defaults to "".
        embedding_size (int): The desired dimensionality of the output embedding. Defaults to 512.
        return_array (Optional[bool]): If True, returns the embedding as a NumPy array.
        Otherwise, returns a list. Defaults to False.

    Returns:
        list: A list containing the image embedding values. If `return_array` is True, returns a NumPy array instead.
    """
    image = vision_model_Image.load_from_file(image_uri)
    embeddings = multimodal_embedding_model.get_embeddings(
        image=image, contextual_text=text, dimension=embedding_size
    )  # 128, 256, 512, 1408
    image_embedding = embeddings.image_embedding

    if return_array:
        image_embedding = np.fromiter(image_embedding, dtype=float)

    return image_embedding

def get_gemini_response(
    generative_multimodal_model,
    model_input: List[str],
    stream: bool = True,
    generation_config: Optional[GenerationConfig] = GenerationConfig(
        temperature=0.2, max_output_tokens=2048
    ),
    safety_settings: Optional[dict] = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    },
    print_exception: bool = False,
) -> str:
    """
    This function generates text in response to a list of model inputs.

    Args:
        model_input: A list of strings representing the inputs to the model.
        stream: Whether to generate the response in a streaming fashion (returning chunks of text at a time) or all at once. Defaults to False.

    Returns:
        The generated text as a string.
    """
    response = generative_multimodal_model.generate_content(
        model_input,
        generation_config=generation_config,
        stream=stream,
        safety_settings=safety_settings,
    )
    response_list = []

    for chunk in response:
        try:
            response_list.append(chunk.text)
        except Exception as e:
            if print_exception:
              print(
                  "Exception occurred while calling gemini. Something is blocked. Lower the safety thresholds [safety_settings: BLOCK_NONE ] if not already done. -----",
                  e,
              )
            else:
              print("Exception occurred while calling gemini. Something is blocked. Lower the safety thresholds [safety_settings: BLOCK_NONE ] if not already done. -----")
            response_list.append("**Something blocked.**")
            continue
    response = "".join(response_list)

    return response

def get_cosine_score(
    dataframe: pd.DataFrame, column_name: str, input_text_embd: np.ndarray
) -> float:
    """
    Calculates the cosine similarity between the user query embedding and the dataframe embedding for a specific column.

    Args:
        dataframe: The pandas DataFrame containing the data to compare against.
        column_name: The name of the column containing the embeddings to compare with.
        input_text_embd: The NumPy array representing the user query embedding.

    Returns:
        The cosine similarity score (rounded to two decimal places) between the user query embedding and the dataframe embedding.
    """

    text_cosine_score = round(np.dot(dataframe[column_name], input_text_embd), 2)
    return text_cosine_score

# =============================================================================
# FUNÇÃO AUSENTE: buscar_imagens_similares_com_embedding
# =============================================================================

def buscar_imagens_similares_com_embedding(
    image_embedding: np.ndarray,
    image_metadata_df: pd.DataFrame,
    top_n: int = 5,
    column_name: str = "mm_embedding_from_img_only"
) -> List[Dict[str, Any]]:
    """
    Busca imagens similares usando embedding de imagem como entrada.
    
    Args:
        image_embedding: Embedding da imagem de consulta
        image_metadata_df: DataFrame com metadados das imagens
        top_n: Número de imagens similares para retornar
        column_name: Nome da coluna com embeddings das imagens
    
    Returns:
        Lista de dicionários com informações das imagens similares
    """
    print(f"🔍 Buscando {top_n} imagens similares usando embedding...")
    
    # Calcular similaridade coseno
    cosine_scores = image_metadata_df.apply(
        lambda x: get_cosine_score(x, column_name, image_embedding),
        axis=1,
    )
    
    # Remover scores perfeitos (mesma imagem)
    cosine_scores = cosine_scores[cosine_scores < 1.0]
    
    # Obter top N scores
    if isinstance(cosine_scores, pd.DataFrame):
        cosine_scores = cosine_scores.iloc[:, 0]
    
    top_n_indices = cosine_scores.nlargest(top_n).index.tolist()
    top_n_scores = cosine_scores.nlargest(top_n).values.tolist()
    
    # Criar lista de resultados
    similar_results = []
    
    for i, (idx, score) in enumerate(zip(top_n_indices, top_n_scores)):
        row = image_metadata_df.iloc[idx]
        
        result = {
            'cosine_score': score,
            'file_name': row.get('file_name', 'N/A'),
            'img_path': row.get('img_path', 'N/A'),
            'page_num': row.get('page_num', 'N/A'),
            'img_desc': row.get('img_desc', 'N/A'),
            'original_filename': row.get('original_filename', 'N/A'),
            'source_type': row.get('source_type', 'N/A')
        }
        
        similar_results.append(result)
    
    print(f"✅ Encontradas {len(similar_results)} imagens similares")
    return similar_results

# =============================================================================
# FUNÇÕES DE PROCESSAMENTO DE IMAGENS
# =============================================================================

def extrair_imagens_do_pdf(pdf_path: str, output_dir: str = "images/", prefixo: str = "map") -> List[str]:
    """
    Extrai imagens de um PDF e salva na pasta de imagens
    
    Args:
        pdf_path: Caminho para o PDF
        output_dir: Diretório de saída
        prefixo: Prefixo para os nomes dos arquivos
    
    Returns:
        Lista de caminhos das imagens extraídas
    """
    print(f"🔍 Processando PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF não encontrado: {pdf_path}")
        return []
    
    # Criar diretório se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    # Abrir PDF
    doc = fitz.open(pdf_path)
    imagens_extraidas = []
    
    print(f"📊 PDF tem {len(doc)} páginas")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images()
        
        print(f"📄 Página {page_num + 1}: {len(images)} imagens encontradas")
        
        for img_index, img in enumerate(images):
            try:
                # Extrair imagem
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                # Converter para RGB se necessário
                if pix.colorspace and pix.colorspace.n > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                # Nome do arquivo
                img_filename = f"{prefixo}_page_{page_num + 1}_img_{img_index + 1}.png"
                img_path = os.path.join(output_dir, img_filename)
                
                # Salvar imagem
                pix.save(img_path)
                imagens_extraidas.append(img_path)
                
                print(f"  ✅ Extraída: {img_filename}")
                
                pix = None  # Liberar memória
                
            except Exception as e:
                print(f"  ❌ Erro ao extrair imagem {img_index}: {e}")
                continue
    
    doc.close()
    print(f"\n🎉 Total de {len(imagens_extraidas)} imagens extraídas!")
    return imagens_extraidas

def processar_imagens_da_pasta(
    pasta_imagens: str = "images/",
    embedding_size: int = 512,
    gerar_descricoes: bool = True,
    formatos_suportados: List[str] = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
) -> pd.DataFrame:
    """
    Processa todas as imagens de uma pasta, gerando embeddings e descrições para RAG
    
    Args:
        pasta_imagens: Caminho da pasta com imagens
        embedding_size: Tamanho do embedding (128, 256, 512, 1408)
        gerar_descricoes: Se deve gerar descrições das imagens com Gemini
        formatos_suportados: Lista de formatos de imagem aceitos
    
    Returns:
        pd.DataFrame: DataFrame compatível com o sistema RAG existente
    """
    print(f"🔍 PROCESSANDO IMAGENS DA PASTA: {pasta_imagens}")
    print("="*60)
    
    # Verificar se a pasta existe
    if not os.path.exists(pasta_imagens):
        print(f"❌ Pasta '{pasta_imagens}' não encontrada!")
        return pd.DataFrame()
    
    # Encontrar todas as imagens na pasta
    imagens_encontradas = []
    for formato in formatos_suportados:
        pattern = os.path.join(pasta_imagens, f"*{formato}")
        imagens_encontradas.extend(glob.glob(pattern))
        pattern = os.path.join(pasta_imagens, f"*{formato.upper()}")
        imagens_encontradas.extend(glob.glob(pattern))
    
    # Remover duplicatas
    imagens_encontradas = list(set(imagens_encontradas))
    
    if not imagens_encontradas:
        print(f"❌ Nenhuma imagem encontrada na pasta '{pasta_imagens}'")
        print(f"Formatos suportados: {formatos_suportados}")
        return pd.DataFrame()
    
    print(f"📊 Encontradas {len(imagens_encontradas)} imagens:")
    for img in imagens_encontradas:
        print(f"  - {os.path.basename(img)}")
    
    # Lista para armazenar dados processados
    dados_imagens = []
    
    # Prompt para descrição das imagens
    prompt_descricao = """Analise esta imagem detalhadamente e forneça uma descrição precisa.
    Inclua:
    - O que você vê na imagem
    - Elementos principais e detalhes importantes
    - Texto visível (se houver)
    - Tipo de imagem (mapa, diagrama, foto, etc.)
    - Informações relevantes para busca e recuperação
    
    Seja específico e detalhado para facilitar buscas futuras."""
    
    print(f"\n🚀 PROCESSANDO CADA IMAGEM...")
    print("="*60)
    
    for i, caminho_imagem in enumerate(imagens_encontradas, 1):
        nome_arquivo = os.path.basename(caminho_imagem)
        print(f"\n📸 PROCESSANDO {i}/{len(imagens_encontradas)}: {nome_arquivo}")
        
        try:
            # 1. Gerar embedding da imagem
            print("  🔄 Gerando embedding...")
            image_embedding = get_image_embedding_from_multimodal_embedding_model(
                image_uri=caminho_imagem,
                embedding_size=embedding_size,
                return_array=True
            )
            print(f"  ✅ Embedding gerado: shape {image_embedding.shape}")
            
            # 2. Gerar descrição da imagem (se solicitado)
            descricao = ""
            if gerar_descricoes:
                print("  🤖 Gerando descrição com Gemini...")
                try:
                    imagem_gemini = Image.load_from_file(caminho_imagem)
                    
                    descricao = get_gemini_response(
                        multimodal_model_2_0_flash,
                        model_input=[prompt_descricao, imagem_gemini],
                        stream=False,
                    )
                    print(f"  ✅ Descrição gerada: {len(descricao)} caracteres")
                    
                except Exception as desc_error:
                    print(f"  ⚠️  Erro ao gerar descrição: {desc_error}")
                    descricao = f"Imagem: {nome_arquivo}"
            
            # 3. Gerar embedding da descrição (para compatibilidade com RAG)
            text_embedding = None
            if descricao:
                try:
                    text_embedding = get_text_embedding_from_text_embedding_model(descricao)
                    print("  ✅ Text embedding da descrição gerado")
                except Exception as text_emb_error:
                    print(f"  ⚠️  Erro ao gerar text embedding: {text_emb_error}")
            
            # 4. Criar registro compatível com o sistema existente
            registro = {
                'file_name': f"pasta_images_{nome_arquivo}",  # Nome único
                'page_num': 1,  # Imagens individuais = página 1
                'img_num': i,
                'img_path': caminho_imagem,
                'img_desc': descricao,
                'mm_embedding_from_img_only': image_embedding.tolist(),  # Compatibilidade
                'text_embedding_from_image_description': text_embedding if text_embedding else None,
                'source_type': 'pasta_imagens',  # Identificar origem
                'original_filename': nome_arquivo
            }
            
            dados_imagens.append(registro)
            print(f"  ✅ Processamento concluído para {nome_arquivo}")
            
        except Exception as e:
            print(f"  ❌ Erro ao processar {nome_arquivo}: {e}")
            continue
    
    # Criar DataFrame
    if dados_imagens:
        df_imagens = pd.DataFrame(dados_imagens)
        print(f"\n🎉 PROCESSAMENTO CONCLUÍDO!")
        print(f"📊 DataFrame criado com {len(df_imagens)} imagens processadas")
        print(f"📋 Colunas: {list(df_imagens.columns)}")
        
        return df_imagens
    else:
        print(f"\n❌ Nenhuma imagem foi processada com sucesso")
        return pd.DataFrame()

# =============================================================================
# FUNÇÕES DE ANÁLISE E VALIDAÇÃO
# =============================================================================

def validar_busca_similaridade(image_metadata_df: pd.DataFrame, imagem_alvo: str = "M3.jpeg") -> List[Dict[str, Any]]:
    """
    Valida o sistema de busca por similaridade usando uma imagem específica
    
    Args:
        image_metadata_df: DataFrame com metadados das imagens
        imagem_alvo: Nome da imagem para buscar similaridades
    
    Returns:
        Lista de resultados de similaridade
    """
    print(f"=== VALIDAÇÃO DE BUSCA POR SIMILARIDADE ===")
    print(f"🎯 Imagem alvo: {imagem_alvo}")
    
    if image_metadata_df.empty:
        print("❌ DataFrame de metadados está vazio!")
        return []
    
    print(f"📊 Dataset: {len(image_metadata_df)} imagens processadas")
    
    # Mostrar todas as imagens no dataset
    print(f"\n📋 IMAGENS NO DATASET:")
    for idx, row in image_metadata_df.iterrows():
        print(f"  {idx + 1}. {row['original_filename']}")
    
    # Encontrar imagem alvo
    alvo_rows = image_metadata_df[image_metadata_df['original_filename'].str.contains(imagem_alvo, case=False, na=False)]
    
    if alvo_rows.empty:
        print(f"\n❌ {imagem_alvo} não encontrada no dataset!")
        print("Verifique se a imagem está na pasta 'images/' e execute o processamento novamente")
        return []
    
    print(f"\n✅ {imagem_alvo} encontrada no dataset!")
    alvo_row = alvo_rows.iloc[0]
    print(f"  📁 Arquivo: {alvo_row['original_filename']}")
    print(f"  📂 Caminho: {alvo_row['img_path']}")
    
    # Extrair embedding da imagem alvo
    alvo_embedding = np.array(alvo_row['mm_embedding_from_img_only'])
    print(f"  📊 Embedding shape: {alvo_embedding.shape}")
    
    # Criar dataset sem a imagem alvo para comparação
    outras_imagens_df = image_metadata_df[~image_metadata_df['original_filename'].str.contains(imagem_alvo, case=False, na=False)]
    
    if outras_imagens_df.empty:
        print(f"\n⚠️  Apenas {imagem_alvo} encontrada no dataset")
        print("Execute a extração de imagens do PDF primeiro para ter mais dados")
        return []
    
    print(f"\n🔍 EXECUTANDO BUSCA POR SIMILARIDADE...")
    print(f"📊 Comparando {imagem_alvo} com {len(outras_imagens_df)} outras imagens")
    
    # Usar nossa função de busca por similaridade
    try:
        similar_results = buscar_imagens_similares_com_embedding(
            image_embedding=alvo_embedding,
            image_metadata_df=outras_imagens_df,
            top_n=min(5, len(outras_imagens_df))
        )
        
        if similar_results:
            print(f"\n🎉 SUCESSO! Encontradas {len(similar_results)} imagens similares:")
            print("="*80)
            
            for i, result in enumerate(similar_results, 1):
                print(f"\n🖼️  RESULTADO {i}:")
                print(f"  📈 Similaridade: {result['cosine_score']:.4f}")
                print(f"  📁 Arquivo: {result['file_name']}")
                print(f"  📂 Caminho: {result['img_path']}")
                
                # Mostrar descrição se disponível
                desc = result['img_desc']
                if desc and desc != 'N/A' and len(str(desc)) > 10:
                    desc_str = str(desc)
                    print(f"  📝 Descrição: {desc_str[:200]}{'...' if len(desc_str) > 200 else ''}")
            
            # Análise de scores
            scores = [r['cosine_score'] for r in similar_results]
            print(f"\n📊 ANÁLISE DE SCORES:")
            print(f"  - Score máximo: {max(scores):.4f}")
            print(f"  - Score mínimo: {min(scores):.4f}")
            print(f"  - Score médio: {sum(scores)/len(scores):.4f}")
            
            print(f"\n✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
            return similar_results
            
        else:
            print("❌ Nenhuma imagem similar encontrada.")
            print("Isso pode indicar problemas com embeddings ou dados muito diferentes.")
            return []
            
    except Exception as e:
        print(f"❌ Erro durante a busca: {e}")
        import traceback
        traceback.print_exc()
        return []

def analise_contextual_com_gemini(
    imagem_caminho: str,
    matching_results: List[Dict[str, Any]],
    modelo_gemini=None
) -> None:
    """
    Realiza análise contextual usando Gemini baseada em imagens similares
    
    Args:
        imagem_caminho: Caminho para a imagem a ser analisada
        matching_results: Resultados da busca por similaridade
        modelo_gemini: Modelo Gemini para análise
    """
    print(f"=== ANÁLISE CONTEXTUAL COM GEMINI ===")
    
    if not matching_results:
        print("❌ Nenhum resultado de busca por similaridade encontrado.")
        print("Execute a validação de busca por similaridade primeiro.")
        return
    
    print(f"✅ Temos {len(matching_results)} resultados de busca por similaridade!")
    
    # Preparar contexto baseado nos resultados similares
    contexto_descricoes = []
    
    for i, result in enumerate(matching_results):
        desc = result.get('img_desc', '')
        score = result.get('cosine_score', 0)
        
        if desc and desc != 'N/A' and len(str(desc)) > 10:
            contexto_descricoes.append(f"Imagem similar {i+1} (similaridade: {score:.3f}): {desc}")
    
    print(f"📝 Coletadas {len(contexto_descricoes)} descrições de imagens similares")
    
    # Perguntas específicas sobre a imagem
    perguntas_contextualizadas = [
        "Baseado nas imagens similares encontradas, o que você pode me dizer sobre esta imagem?",
        "Quais elementos em comum existem entre esta imagem e as imagens similares?",
        "Se esta imagem é um mapa ou planta, quais informações específicas posso extrair?",
        "Há algum padrão arquitetônico ou de layout visível nesta imagem?",
        "What are the rooms in this floor? (baseado no contexto das imagens similares)"
    ]
    
    print("\n🤖 ANÁLISE CONTEXTUAL COM GEMINI:")
    
    try:
        # Carregar a imagem
        imagem_gemini = Image.load_from_file(imagem_caminho)
        print(f"✅ Imagem carregada: {imagem_caminho}")
        
        # Preparar contexto das imagens similares
        contexto_texto = "\n".join(contexto_descricoes[:3])  # Top 3 descrições
        
        for i, pergunta in enumerate(perguntas_contextualizadas, 1):
            print(f"\n" + "="*70)
            print(f"📋 PERGUNTA {i}: {pergunta}")
            print("="*70)
            
            # Criar prompt contextualizado
            prompt_contextualizado = f"""
            Analise a imagem fornecida considerando o seguinte contexto de imagens similares:
            
            CONTEXTO DE IMAGENS SIMILARES ENCONTRADAS:
            {contexto_texto}
            
            PERGUNTA ESPECÍFICA:
            {pergunta}
            
            Por favor, forneça uma resposta detalhada baseada tanto na análise visual da imagem 
            quanto no contexto das imagens similares fornecido acima.
            """
            
            try:
                resposta = get_gemini_response(
                    modelo_gemini,
                    model_input=[prompt_contextualizado, imagem_gemini],
                    stream=False,
                )
                
                print(f"🤖 RESPOSTA CONTEXTUALIZADA:")
                print(f"{resposta}")
                
            except Exception as gemini_error:
                print(f"❌ Erro na análise contextual: {gemini_error}")
                
                # Fallback: análise simples sem contexto
                try:
                    resposta_simples = get_gemini_response(
                        modelo_gemini,
                        model_input=[pergunta, imagem_gemini],
                        stream=False,
                    )
                    print(f"🤖 RESPOSTA SIMPLES (sem contexto):")
                    print(f"{resposta_simples}")
                    
                except Exception as simple_error:
                    print(f"❌ Erro na análise simples: {simple_error}")
    
    except Exception as e:
        print(f"❌ Erro ao carregar imagem: {e}")
    
    # Mostrar resumo final
    print(f"\n" + "="*70)
    print("📊 RESUMO DOS RESULTADOS DE SIMILARIDADE:")
    print("="*70)
    
    for i, result in enumerate(matching_results, 1):
        print(f"\n🖼️  Imagem Similar {i}:")
        print(f"  📈 Similaridade: {result.get('cosine_score', 0):.4f}")
        print(f"  📁 Arquivo: {result.get('file_name', 'N/A')}")
        print(f"  📄 Página: {result.get('page_num', 'N/A')}")
        print(f"  📂 Caminho: {result.get('img_path', 'N/A')}")

def analise_direta_com_gemini(imagem_caminho: str, modelo_gemini=None) -> None:
    """
    Realiza análise direta de uma imagem usando Gemini
    
    Args:
        imagem_caminho: Caminho para a imagem
        modelo_gemini: Modelo Gemini para análise
    """
    print(f"=== ANÁLISE DIRETA COM GEMINI ===")
    
    if not modelo_gemini:
        print("❌ Modelo Gemini não fornecido!")
        return
    
    print("🔍 Analisando imagem com Gemini...")
    
    # Perguntas específicas sobre a imagem
    perguntas = [
        "What are the rooms or areas shown in this floor plan?",
        "How can I go from room 2001 to room 2037?"
    ]
    
    try:
        # Carregar a imagem
        imagem_gemini = Image.load_from_file(imagem_caminho)
        print(f"✅ Imagem carregada: {imagem_caminho}")
        
        # Fazer cada pergunta
        for i, pergunta in enumerate(perguntas, 1):
            print(f"\n📋 PERGUNTA {i}: {pergunta}")
            print("-" * 60)
            
            try:
                # Usar o modelo diretamente (método mais confiável)
                response = modelo_gemini.generate_content([pergunta, imagem_gemini])
                response_text = response.text if hasattr(response, 'text') else str(response)
                
                print(f"🤖 RESPOSTA:")
                print(f"{response_text}")
                
            except Exception as question_error:
                print(f"❌ Erro na pergunta {i}: {question_error}")
                
                # Tentar método alternativo com get_gemini_response
                try:
                    alt_response = get_gemini_response(
                        modelo_gemini,
                        model_input=[pergunta, imagem_gemini],
                        stream=False
                    )
                    print(f"🤖 RESPOSTA (método alternativo):")
                    print(f"{alt_response}")
                except Exception as alt_error:
                    print(f"❌ Método alternativo também falhou: {alt_error}")
    
    except Exception as e:
        print(f"❌ Erro geral ao analisar imagem: {e}")
        import traceback
        traceback.print_exc()

# =============================================================================
# INICIALIZAÇÃO DOS MODELOS
# =============================================================================

def inicializar_modelos():
    """Inicializa todos os modelos necessários"""
    print("🚀 INICIALIZANDO MODELOS...")
    print("="*50)
    
    try:
        # Configurar projeto
        if "google.colab" not in sys.modules:
            try:
                PROJECT_ID = subprocess.check_output(
                    ["gcloud", "config", "get-value", "project"], text=True
                ).strip()
                config.PROJECT_ID = PROJECT_ID
                print(f"✅ Project ID obtido automaticamente: {PROJECT_ID}")
            except:
                print(f"⚠️  Usando Project ID padrão: {config.PROJECT_ID}")
        
        print(f"📋 Project ID: {config.PROJECT_ID}")
        print(f"📍 Location: {config.LOCATION}")
        
        # Inicializar Vertex AI
        vertexai.init(project=config.PROJECT_ID, location=config.LOCATION)
        print("✅ Vertex AI inicializado")
        
        # Carregar modelos multimodais
        global multimodal_model_2_0_flash, multimodal_model_15, multimodal_model_15_flash
        multimodal_model_2_0_flash = GenerativeModel("gemini-2.0-flash-001")
        multimodal_model_15 = GenerativeModel("gemini-1.5-pro-001")
        multimodal_model_15_flash = GenerativeModel("gemini-1.5-flash-001")
        print("✅ Modelos multimodais carregados")
        
        # Carregar modelos de embedding
        global text_embedding_model, multimodal_embedding_model
        text_embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")
        multimodal_embedding_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
        print("✅ Modelos de embedding carregados")
        
        # Configurar variáveis globais
        set_global_variable("text_embedding_model", text_embedding_model)
        set_global_variable("multimodal_embedding_model", multimodal_embedding_model)
        print("✅ Variáveis globais configuradas")
        
        print("\n🎉 TODOS OS MODELOS INICIALIZADOS COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO AO INICIALIZAR MODELOS: {e}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# FLUXO PRINCIPAL
# =============================================================================

def executar_fluxo_completo(args):
    """Executa o fluxo completo do sistema RAG multimodal"""
    print("🚀 INICIANDO SISTEMA RAG MULTIMODAL COMPLETO")
    print("="*60)
    
    # Atualizar configurações
    config.update_from_args(args)
    
    # 1. Inicializar modelos
    if not inicializar_modelos():
        print("❌ Falha na inicialização dos modelos. Abortando.")
        return False
    
    # 2. Extrair imagens de PDFs (se solicitado)
    if args.extract_pdf:
        print(f"\n📄 EXTRAINDO IMAGENS DE PDFs...")
        print("="*50)
        
        # Verificar quantas imagens temos atualmente
        current_images = len([f for f in os.listdir(config.IMAGE_SAVE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
        print(f"📊 Imagens atuais na pasta: {current_images}")
        
        if current_images <= 1:
            print("🔄 Extraindo imagens do PDF para ter mais dados...")
            
            # Extrair do map.pdf se existir
            if os.path.exists(os.path.join(config.PDF_FOLDER_PATH, "map.pdf")):
                imagens_extraidas = extrair_imagens_do_pdf(
                    os.path.join(config.PDF_FOLDER_PATH, "map.pdf"), 
                    config.IMAGE_SAVE_DIR, 
                    "map"
                )
                
                if imagens_extraidas:
                    print(f"\n✅ {len(imagens_extraidas)} novas imagens adicionadas!")
                else:
                    print("❌ Nenhuma imagem foi extraída do PDF")
            else:
                print("❌ Arquivo map/map.pdf não encontrado")
                
                # Verificar outros PDFs disponíveis
                print("\n🔍 Procurando outros PDFs...")
                pdf_paths = []
                for root, dirs, files in os.walk("."):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_paths.append(os.path.join(root, file))
                
                if pdf_paths:
                    print("📋 PDFs encontrados:")
                    for i, pdf_path in enumerate(pdf_paths[:3], 1):
                        print(f"  {i}. {pdf_path}")
                    
                    # Processar o primeiro PDF encontrado
                    if pdf_paths:
                        primeiro_pdf = pdf_paths[0]
                        print(f"\n🔄 Processando: {primeiro_pdf}")
                        imagens_extraidas = extrair_imagens_do_pdf(primeiro_pdf, config.IMAGE_SAVE_DIR, "doc")
                        
                        if imagens_extraidas:
                            print(f"\n✅ {len(imagens_extraidas)} imagens extraídas de {primeiro_pdf}!")
                else:
                    print("❌ Nenhum PDF encontrado para extrair imagens")
        else:
            print("✅ Já há múltiplas imagens na pasta")
    
    # 3. Processar imagens da pasta
    print(f"\n📂 PROCESSANDO IMAGENS DA PASTA...")
    print("="*50)
    
    image_metadata_df = processar_imagens_da_pasta(
        pasta_imagens=config.IMAGE_SAVE_DIR,
        embedding_size=config.EMBEDDING_SIZE,
        gerar_descricoes=True,
        formatos_suportados=['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    )
    
    if image_metadata_df.empty:
        print("❌ FALHA: Nenhuma imagem foi processada")
        return False
    
    # Salvar DataFrame para uso futuro
    try:
        image_metadata_df.to_pickle("image_metadata_from_folder.pkl")
        print(f"\n💾 DataFrame salvo em 'image_metadata_from_folder.pkl'")
    except Exception as save_error:
        print(f"\n⚠️  Não foi possível salvar: {save_error}")
    
    # 4. Validação de busca por similaridade
    print(f"\n🔍 VALIDAÇÃO DE BUSCA POR SIMILARIDADE...")
    print("="*50)
    
    matching_results = validar_busca_similaridade(image_metadata_df, args.target_image)
    
    # 5. Análise contextual (se temos resultados)
    if matching_results:
        print(f"\n🤖 ANÁLISE CONTEXTUAL...")
        print("="*50)
        
        # Encontrar imagem alvo para análise
        target_image_path = None
        for idx, row in image_metadata_df.iterrows():
            if args.target_image.lower() in row['original_filename'].lower():
                target_image_path = row['img_path']
                break
        
        if target_image_path:
            analise_contextual_com_gemini(target_image_path, matching_results, multimodal_model_2_0_flash)
        else:
            print(f"❌ Imagem alvo '{args.target_image}' não encontrada para análise contextual")
    
    # 6. Análise direta (se solicitado)
    if args.direct_analysis:
        print(f"\n🔍 ANÁLISE DIRETA...")
        print("="*50)
        
        # Encontrar imagem para análise direta
        target_image_path = None
        for idx, row in image_metadata_df.iterrows():
            if args.target_image.lower() in row['original_filename'].lower():
                target_image_path = row['img_path']
                break
        
        if target_image_path:
            analise_direta_com_gemini(target_image_path, multimodal_model_2_0_flash)
        else:
            print(f"❌ Imagem alvo '{args.target_image}' não encontrada para análise direta")
    
    print(f"\n🎉 SISTEMA RAG MULTIMODAL EXECUTADO COM SUCESSO!")
    print("="*60)
    
    return True

# =============================================================================
# INTERFACE DE LINHA DE COMANDO
# =============================================================================

def criar_parser():
    """Cria o parser de argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description="Sistema Completo de RAG Multimodal com Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Execução básica
  python multimodal_rag_complete.py

  # Com extração de PDF
  python multimodal_rag_complete.py --extract-pdf

  # Com análise direta
  python multimodal_rag_complete.py --direct-analysis

  # Com configurações personalizadas
  python multimodal_rag_complete.py --project-id meu-projeto --location us-east1 --embedding-size 256

  # Buscar por imagem específica
  python multimodal_rag_complete.py --target-image B2_room.jpeg
        """
    )
    
    # Configurações do projeto
    parser.add_argument("--project-id", type=str, help="ID do projeto Google Cloud")
    parser.add_argument("--location", type=str, default="us-central1", help="Localização do Vertex AI")
    
    # Configurações de processamento
    parser.add_argument("--embedding-size", type=int, default=512, choices=[128, 256, 512, 1408], help="Tamanho do embedding")
    parser.add_argument("--image-dir", type=str, default="images/", help="Diretório das imagens")
    parser.add_argument("--pdf-dir", type=str, default="map/", help="Diretório dos PDFs")
    
    # Opções de execução
    parser.add_argument("--extract-pdf", action="store_true", help="Extrair imagens de PDFs antes do processamento")
    parser.add_argument("--direct-analysis", action="store_true", help="Executar análise direta com Gemini")
    parser.add_argument("--target-image", type=str, default="M3.jpeg", help="Nome da imagem alvo para análise")
    
    # Opções de debug
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    parser.add_argument("--dry-run", action="store_true", help="Executar sem fazer alterações")
    
    return parser

def main():
    """Função principal"""
    parser = criar_parser()
    args = parser.parse_args()
    
    # Modo dry-run
    if args.dry_run:
        print("🔍 MODO DRY-RUN: Nenhuma alteração será feita")
        print(f"Configurações que seriam usadas:")
        print(f"  Project ID: {args.project_id or config.PROJECT_ID}")
        print(f"  Location: {args.location}")
        print(f"  Embedding Size: {args.embedding_size}")
        print(f"  Image Directory: {args.image_dir}")
        print(f"  PDF Directory: {args.pdf_dir}")
        print(f"  Extract PDF: {args.extract_pdf}")
        print(f"  Direct Analysis: {args.direct_analysis}")
        print(f"  Target Image: {args.target_image}")
        return
    
    # Executar fluxo principal
    try:
        sucesso = executar_fluxo_completo(args)
        if sucesso:
            print("\n✅ Execução concluída com sucesso!")
            sys.exit(0)
        else:
            print("\n❌ Execução falhou!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Execução interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
