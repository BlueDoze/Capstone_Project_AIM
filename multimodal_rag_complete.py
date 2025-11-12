#!/usr/bin/env python3
"""
Complete Multimodal RAG System with Gemini
==========================================

This script implements a complete Retrieval-Augmented Generation (RAG) multimodal system
that processes PDF documents, extracts images, generates embeddings and performs contextual
analysis using Google Cloud Vertex AI Gemini models.

Features:
- PDF processing and text/image extraction
- Embedding generation for text and images
- Similarity search using embeddings
- Contextual analysis with Gemini models
- Citation and reference system
- Direct processing of images from folders

Author: Multimodal RAG System
Date: 2025
"""

import os
import sys
import glob
import time
import argparse
import subprocess
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from pathlib import Path

# Main imports
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

# Formatting and utilities
from rich import print as rich_print
from rich.markdown import Markdown as rich_Markdown
from IPython.display import Markdown, display

# =============================================================================
# CONFIGURATION AND INITIALIZATION
# =============================================================================

class Config:
    """System configurations"""
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
        """Updates configurations from command line arguments"""
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

# Global configuration instance
config = Config()

# =============================================================================
# UTILITY FUNCTIONS (from multimodal_qa_with_rag_utils.py)
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

    # Returns 768 dimensional array
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

    # Handle different response types based on stream parameter
    try:
        if stream:
            # Streaming response - iterate through chunks
            response_list = []
            try:
                for chunk in response:
                    try:
                        if hasattr(chunk, 'text') and chunk.text:
                            response_list.append(chunk.text)
                    except Exception as e:
                        if print_exception:
                            print(
                                "Exception occurred while processing chunk. Something is blocked. Lower the safety thresholds [safety_settings: BLOCK_NONE ] if not already done. -----",
                                e,
                            )
                        else:
                            print("Exception occurred while processing chunk. Something is blocked. Lower the safety thresholds [safety_settings: BLOCK_NONE ] if not already done. -----")
                        response_list.append("**Something blocked.**")
                        continue
                return "".join(response_list)
            except TypeError as te:
                # If response is not iterable, treat as non-streaming
                if print_exception:
                    print(f"Response not iterable, treating as non-streaming: {te}")
                if hasattr(response, 'text') and response.text:
                    return response.text
                else:
                    return "**No response generated.**"
        else:
            # Non-streaming response - direct access to text
            if hasattr(response, 'text') and response.text:
                return response.text
            else:
                return "**No response generated.**"
    except Exception as e:
        if print_exception:
            print(
                "Exception occurred while calling gemini. Something is blocked. Lower the safety thresholds [safety_settings: BLOCK_NONE ] if not already done. -----",
                e,
            )
        else:
            print("Exception occurred while calling gemini. Something is blocked. Lower the safety thresholds [safety_settings: BLOCK_NONE ] if not already done. -----")
        return "**Something blocked.**"

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
# MISSING FUNCTION: buscar_imagens_similares_com_embedding
# =============================================================================

def buscar_imagens_similares_com_embedding(
    image_embedding: np.ndarray,
    image_metadata_df: pd.DataFrame,
    top_n: int = 5,
    column_name: str = "mm_embedding_from_img_only"
) -> List[Dict[str, Any]]:
    """
    Searches for similar images using image embedding as input.

    Args:
        image_embedding: Query image embedding
        image_metadata_df: DataFrame with image metadata
        top_n: Number of similar images to return
        column_name: Name of column with image embeddings

    Returns:
        List of dictionaries with similar image information
    """
    print(f"🔍 Searching for {top_n} similar images using embedding...")

    # Calculate cosine similarity
    cosine_scores = image_metadata_df.apply(
        lambda x: get_cosine_score(x, column_name, image_embedding),
        axis=1,
    )

    # Remove perfect scores (same image)
    cosine_scores = cosine_scores[cosine_scores < 1.0]

    # Get top N scores
    if isinstance(cosine_scores, pd.DataFrame):
        cosine_scores = cosine_scores.iloc[:, 0]

    top_n_indices = cosine_scores.nlargest(top_n).index.tolist()
    top_n_scores = cosine_scores.nlargest(top_n).values.tolist()

    # Create results list
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

    print(f"✅ Found {len(similar_results)} similar images")
    return similar_results

# =============================================================================
# IMAGE PROCESSING FUNCTIONS
# =============================================================================

def extrair_imagens_do_pdf(pdf_path: str, output_dir: str = "images/", prefixo: str = "map") -> List[str]:
    """
    Extracts images from a PDF and saves them to the images folder

    Args:
        pdf_path: Path to the PDF file
        output_dir: Output directory
        prefixo: Prefix for the file names

    Returns:
        List of paths to extracted images
    """
    print(f"🔍 Processing PDF: {pdf_path}")

    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return []

    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Open PDF
    doc = fitz.open(pdf_path)
    imagens_extraidas = []

    print(f"📊 PDF has {len(doc)} pages")

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images()

        print(f"📄 Page {page_num + 1}: {len(images)} images found")

        for img_index, img in enumerate(images):
            try:
                # Extract image
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)

                # Convert to RGB if necessary
                if pix.colorspace and pix.colorspace.n > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                # File name
                img_filename = f"{prefixo}_page_{page_num + 1}_img_{img_index + 1}.png"
                img_path = os.path.join(output_dir, img_filename)

                # Save image
                pix.save(img_path)
                imagens_extraidas.append(img_path)

                print(f"  ✅ Extracted: {img_filename}")

                pix = None  # Free memory

            except Exception as e:
                print(f"  ❌ Error extracting image {img_index}: {e}")
                continue

    doc.close()
    print(f"\n🎉 Total of {len(imagens_extraidas)} images extracted!")
    return imagens_extraidas

def processar_imagens_da_pasta(
    pasta_imagens: str = "images/",
    embedding_size: int = 512,
    gerar_descricoes: bool = True,
    formatos_suportados: List[str] = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
) -> pd.DataFrame:
    """
    Processes all images from a folder, generating embeddings and descriptions for RAG

    Args:
        pasta_imagens: Path to folder with images
        embedding_size: Embedding size (128, 256, 512, 1408)
        gerar_descricoes: Whether to generate image descriptions with Gemini
        formatos_suportados: List of supported image formats

    Returns:
        pd.DataFrame: DataFrame compatible with existing RAG system
    """
    print(f"🔍 PROCESSING IMAGES FROM FOLDER: {pasta_imagens}")
    print("="*60)

    # Check if folder exists
    if not os.path.exists(pasta_imagens):
        print(f"❌ Folder '{pasta_imagens}' not found!")
        return pd.DataFrame()

    # Find all images in folder
    imagens_encontradas = []
    for formato in formatos_suportados:
        pattern = os.path.join(pasta_imagens, f"*{formato}")
        imagens_encontradas.extend(glob.glob(pattern))
        pattern = os.path.join(pasta_imagens, f"*{formato.upper()}")
        imagens_encontradas.extend(glob.glob(pattern))

    # Remove duplicates
    imagens_encontradas = list(set(imagens_encontradas))

    if not imagens_encontradas:
        print(f"❌ No images found in folder '{pasta_imagens}'")
        print(f"Supported formats: {formatos_suportados}")
        return pd.DataFrame()

    print(f"📊 Found {len(imagens_encontradas)} images:")
    for img in imagens_encontradas:
        print(f"  - {os.path.basename(img)}")
    
    # List to store processed data
    dados_imagens = []

    # Prompt for image description focused on navigation
    prompt_descricao = """Analyze this image in detail and provide a precise description focused on navigation.

    If it is a FLOOR PLAN or ARCHITECTURAL MAP:
    1. Identify ALL visible room numbers
    2. Describe the location of DOORS using simple directions (to the right, to the left, ahead, behind)
    3. Identify CORRIDORS and describe them as navigation paths
    4. Use practical instructions: "turn right", "turn left", "go straight", "go back"
    5. Describe relative positions between rooms (e.g., "room X is to the left of room Y")
    6. Identify navigation elements: stairs, elevators, main entrances
    7. Describe door colors when visible (e.g., "orange door of room 1001")
    8. Create a description from the perspective of someone navigating the space

    If it is ANOTHER TYPE OF IMAGE:
    - What you see in the image
    - Main elements and important details
    - Visible text (if any)
    - Image type (map, diagram, photo, etc.)
    - Relevant information for search and retrieval

    Be specific and detailed to facilitate navigation and future searches."""
    
    print(f"\n🚀 PROCESSING EACH IMAGE...")
    print("="*60)

    for i, caminho_imagem in enumerate(imagens_encontradas, 1):
        nome_arquivo = os.path.basename(caminho_imagem)
        print(f"\n📸 PROCESSING {i}/{len(imagens_encontradas)}: {nome_arquivo}")

        try:
            # 1. Generate image embedding
            print("  🔄 Generating embedding...")
            image_embedding = get_image_embedding_from_multimodal_embedding_model(
                image_uri=caminho_imagem,
                embedding_size=embedding_size,
                return_array=True
            )
            print(f"  ✅ Embedding generated: shape {image_embedding.shape}")

            # 2. Generate image description (if requested)
            descricao = ""
            if gerar_descricoes:
                print("  🤖 Generating description with Gemini...")
                try:
                    imagem_gemini = Image.load_from_file(caminho_imagem)

                    descricao = get_gemini_response(
                        multimodal_model_2_0_flash,
                        model_input=[prompt_descricao, imagem_gemini],
                        stream=False,
                    )
                    print(f"  ✅ Description generated: {len(descricao)} characters")

                except Exception as desc_error:
                    print(f"  ⚠️  Error generating description: {desc_error}")
                    descricao = f"Image: {nome_arquivo}"

            # 3. Generate description embedding (for RAG compatibility)
            text_embedding = None
            if descricao:
                try:
                    text_embedding = get_text_embedding_from_text_embedding_model(descricao)
                    print("  ✅ Text embedding of description generated")
                except Exception as text_emb_error:
                    print(f"  ⚠️  Error generating text embedding: {text_emb_error}")

            # 4. Create record compatible with existing system
            registro = {
                'file_name': f"pasta_images_{nome_arquivo}",  # Unique name
                'page_num': 1,  # Individual images = page 1
                'img_num': i,
                'img_path': caminho_imagem,
                'img_desc': descricao,
                'mm_embedding_from_img_only': image_embedding.tolist(),  # Compatibility
                'text_embedding_from_image_description': text_embedding if text_embedding else None,
                'source_type': 'pasta_imagens',  # Identify source
                'original_filename': nome_arquivo
            }
            
            dados_imagens.append(registro)
            print(f"  ✅ Processing completed for {nome_arquivo}")

        except Exception as e:
            print(f"  ❌ Error processing {nome_arquivo}: {e}")
            continue

    # Create DataFrame
    if dados_imagens:
        df_imagens = pd.DataFrame(dados_imagens)
        print(f"\n🎉 PROCESSING COMPLETED!")
        print(f"📊 DataFrame created with {len(df_imagens)} processed images")
        print(f"📋 Columns: {list(df_imagens.columns)}")

        return df_imagens
    else:
        print(f"\n❌ No images were successfully processed")
        return pd.DataFrame()

# =============================================================================
# ANALYSIS AND VALIDATION FUNCTIONS
# =============================================================================

def validar_busca_similaridade(image_metadata_df: pd.DataFrame, imagem_alvo: str = "M3.jpeg") -> List[Dict[str, Any]]:
    """
    Validates the similarity search system using a specific image

    Args:
        image_metadata_df: DataFrame with image metadata
        imagem_alvo: Name of target image for similarity search

    Returns:
        List of similarity results
    """
    print(f"=== SIMILARITY SEARCH VALIDATION ===")
    print(f"🎯 Target image: {imagem_alvo}")

    if image_metadata_df.empty:
        print("❌ Metadata DataFrame is empty!")
        return []

    print(f"📊 Dataset: {len(image_metadata_df)} processed images")

    # Show all images in dataset
    print(f"\n📋 IMAGES IN DATASET:")
    for idx, row in image_metadata_df.iterrows():
        print(f"  {idx + 1}. {row['original_filename']}")

    # Find target image
    alvo_rows = image_metadata_df[image_metadata_df['original_filename'].str.contains(imagem_alvo, case=False, na=False)]

    if alvo_rows.empty:
        print(f"\n❌ {imagem_alvo} not found in dataset!")
        print("Check if the image is in the 'images/' folder and run the processing again")
        return []

    print(f"\n✅ {imagem_alvo} found in dataset!")
    alvo_row = alvo_rows.iloc[0]
    print(f"  📁 File: {alvo_row['original_filename']}")
    print(f"  📂 Path: {alvo_row['img_path']}")

    # Extract target image embedding
    alvo_embedding = np.array(alvo_row['mm_embedding_from_img_only'])
    print(f"  📊 Embedding shape: {alvo_embedding.shape}")

    # Create dataset without target image for comparison
    outras_imagens_df = image_metadata_df[~image_metadata_df['original_filename'].str.contains(imagem_alvo, case=False, na=False)]

    if outras_imagens_df.empty:
        print(f"\n⚠️  Only {imagem_alvo} found in dataset")
        print("Run PDF image extraction first to have more data")
        return []

    print(f"\n🔍 RUNNING SIMILARITY SEARCH...")
    print(f"📊 Comparing {imagem_alvo} with {len(outras_imagens_df)} other images")

    # Use our similarity search function
    try:
        similar_results = buscar_imagens_similares_com_embedding(
            image_embedding=alvo_embedding,
            image_metadata_df=outras_imagens_df,
            top_n=min(5, len(outras_imagens_df))
        )

        if similar_results:
            print(f"\n🎉 SUCCESS! Found {len(similar_results)} similar images:")
            print("="*80)

            for i, result in enumerate(similar_results, 1):
                print(f"\n🖼️  RESULT {i}:")
                print(f"  📈 Similarity: {result['cosine_score']:.4f}")
                print(f"  📁 File: {result['file_name']}")
                print(f"  📂 Path: {result['img_path']}")

                # Show description if available
                desc = result['img_desc']
                if desc and desc != 'N/A' and len(str(desc)) > 10:
                    desc_str = str(desc)
                    print(f"  📝 Description: {desc_str[:200]}{'...' if len(desc_str) > 200 else ''}")

            # Score analysis
            scores = [r['cosine_score'] for r in similar_results]
            print(f"\n📊 SCORE ANALYSIS:")
            print(f"  - Maximum score: {max(scores):.4f}")
            print(f"  - Minimum score: {min(scores):.4f}")
            print(f"  - Average score: {sum(scores)/len(scores):.4f}")

            print(f"\n✅ VALIDATION COMPLETED SUCCESSFULLY!")
            return similar_results

        else:
            print("❌ No similar images found.")
            print("This may indicate problems with embeddings or very different data.")
            return []

    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()
        return []

def analise_contextual_com_gemini(
    imagem_caminho: str,
    matching_results: List[Dict[str, Any]],
    modelo_gemini=None
) -> None:
    """
    Performs contextual analysis using Gemini based on similar images

    Args:
        imagem_caminho: Path to the image to be analyzed
        matching_results: Similarity search results
        modelo_gemini: Gemini model for analysis
    """
    print(f"=== CONTEXTUAL ANALYSIS WITH GEMINI ===")

    if not matching_results:
        print("❌ No similarity search results found.")
        print("Run the similarity search validation first.")
        return

    print(f"✅ We have {len(matching_results)} similarity search results!")

    # Prepare context based on similar results
    contexto_descricoes = []

    for i, result in enumerate(matching_results):
        desc = result.get('img_desc', '')
        score = result.get('cosine_score', 0)

        if desc and desc != 'N/A' and len(str(desc)) > 10:
            contexto_descricoes.append(f"Similar image {i+1} (similarity: {score:.3f}): {desc}")

    print(f"📝 Collected {len(contexto_descricoes)} descriptions of similar images")

    # Specific questions about the image
    perguntas_contextualizadas = [
        "Based on the similar images found, what can you tell me about this image?",
        "What common elements exist between this image and the similar images?",
        "If this image is a map or floor plan, what specific information can I extract?",
        "Is there any architectural or layout pattern visible in this image?",
        "What are the rooms in this floor? (based on the context of similar images)"
    ]

    print("\n🤖 CONTEXTUAL ANALYSIS WITH GEMINI:")
    
    try:
        # Load the image
        imagem_gemini = Image.load_from_file(imagem_caminho)
        print(f"✅ Image loaded: {imagem_caminho}")

        # Prepare context from similar images
        contexto_texto = "\n".join(contexto_descricoes[:3])  # Top 3 descriptions

        for i, pergunta in enumerate(perguntas_contextualizadas, 1):
            print(f"\n" + "="*70)
            print(f"📋 QUESTION {i}: {pergunta}")
            print("="*70)

            # Create contextualized prompt
            prompt_contextualizado = f"""
            Analyze the provided image considering the following context of similar images:

            CONTEXT OF SIMILAR IMAGES FOUND:
            {contexto_texto}

            SPECIFIC QUESTION:
            {pergunta}

            Please provide a detailed answer based on both the visual analysis of the image
            and the context of similar images provided above.
            """

            try:
                resposta = get_gemini_response(
                    modelo_gemini,
                    model_input=[prompt_contextualizado, imagem_gemini],
                    stream=False,
                )

                print(f"🤖 CONTEXTUALIZED RESPONSE:")
                print(f"{resposta}")

            except Exception as gemini_error:
                print(f"❌ Error in contextual analysis: {gemini_error}")

                # Fallback: simple analysis without context
                try:
                    resposta_simples = get_gemini_response(
                        modelo_gemini,
                        model_input=[pergunta, imagem_gemini],
                        stream=False,
                    )
                    print(f"🤖 SIMPLE RESPONSE (without context):")
                    print(f"{resposta_simples}")

                except Exception as simple_error:
                    print(f"❌ Error in simple analysis: {simple_error}")

    except Exception as e:
        print(f"❌ Error loading image: {e}")

    # Show final summary
    print(f"\n" + "="*70)
    print("📊 SIMILARITY RESULTS SUMMARY:")
    print("="*70)

    for i, result in enumerate(matching_results, 1):
        print(f"\n🖼️  Similar Image {i}:")
        print(f"  📈 Similarity: {result.get('cosine_score', 0):.4f}")
        print(f"  📁 File: {result.get('file_name', 'N/A')}")
        print(f"  📄 Page: {result.get('page_num', 'N/A')}")
        print(f"  📂 Path: {result.get('img_path', 'N/A')}")

def analise_direta_com_gemini(imagem_caminho: str, modelo_gemini=None) -> None:
    """
    Performs direct analysis of an image using Gemini

    Args:
        imagem_caminho: Path to the image
        modelo_gemini: Gemini model for analysis
    """
    print(f"=== DIRECT ANALYSIS WITH GEMINI ===")

    if not modelo_gemini:
        print("❌ Gemini model not provided!")
        return

    print("🔍 Analyzing image with Gemini...")

    # Specific questions about the image
    perguntas = [
        "What are the rooms or areas shown in this floor plan?",
        "How can I go from room 2001 to room 2037?"
    ]

    try:
        # Load the image
        imagem_gemini = Image.load_from_file(imagem_caminho)
        print(f"✅ Image loaded: {imagem_caminho}")

        # Ask each question
        for i, pergunta in enumerate(perguntas, 1):
            print(f"\n📋 QUESTION {i}: {pergunta}")
            print("-" * 60)

            try:
                # Use model directly (most reliable method)
                response = modelo_gemini.generate_content([pergunta, imagem_gemini])
                response_text = response.text if hasattr(response, 'text') else str(response)

                print(f"🤖 RESPONSE:")
                print(f"{response_text}")

            except Exception as question_error:
                print(f"❌ Error in question {i}: {question_error}")

                # Try alternative method with get_gemini_response
                try:
                    alt_response = get_gemini_response(
                        modelo_gemini,
                        model_input=[pergunta, imagem_gemini],
                        stream=False
                    )
                    print(f"🤖 RESPONSE (alternative method):")
                    print(f"{alt_response}")
                except Exception as alt_error:
                    print(f"❌ Alternative method also failed: {alt_error}")

    except Exception as e:
        print(f"❌ General error analyzing image: {e}")
        import traceback
        traceback.print_exc()

# =============================================================================
# MODEL INITIALIZATION
# =============================================================================

def inicializar_modelos():
    """Initializes all necessary models"""
    print("🚀 INITIALIZING MODELS...")
    print("="*50)

    try:
        # Configure project
        if "google.colab" not in sys.modules:
            try:
                PROJECT_ID = subprocess.check_output(
                    ["gcloud", "config", "get-value", "project"], text=True
                ).strip()
                config.PROJECT_ID = PROJECT_ID
                print(f"✅ Project ID obtained automatically: {PROJECT_ID}")
            except:
                print(f"⚠️  Using default Project ID: {config.PROJECT_ID}")

        print(f"📋 Project ID: {config.PROJECT_ID}")
        print(f"📍 Location: {config.LOCATION}")

        # Initialize Vertex AI
        vertexai.init(project=config.PROJECT_ID, location=config.LOCATION)
        print("✅ Vertex AI initialized")

        # Load multimodal models
        global multimodal_model_2_0_flash, multimodal_model_15, multimodal_model_15_flash
        multimodal_model_2_0_flash = GenerativeModel("gemini-2.0-flash-001")
        multimodal_model_15 = GenerativeModel("gemini-1.5-pro-001")
        multimodal_model_15_flash = GenerativeModel("gemini-1.5-flash-001")
        print("✅ Multimodal models loaded")

        # Load embedding models
        global text_embedding_model, multimodal_embedding_model
        text_embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")
        multimodal_embedding_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
        print("✅ Embedding models loaded")

        # Configure global variables
        set_global_variable("text_embedding_model", text_embedding_model)
        set_global_variable("multimodal_embedding_model", multimodal_embedding_model)
        print("✅ Global variables configured")

        print("\n🎉 ALL MODELS INITIALIZED SUCCESSFULLY!")
        return True

    except Exception as e:
        print(f"❌ ERROR INITIALIZING MODELS: {e}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# MAIN FLOW
# =============================================================================

def executar_fluxo_completo(args):
    """Executes the complete multimodal RAG system flow"""
    print("🚀 STARTING COMPLETE MULTIMODAL RAG SYSTEM")
    print("="*60)

    # Update configurations
    config.update_from_args(args)

    # 1. Initialize models
    if not inicializar_modelos():
        print("❌ Model initialization failed. Aborting.")
        return False

    # 2. Extract images from PDFs (if requested)
    if args.extract_pdf:
        print(f"\n📄 EXTRACTING IMAGES FROM PDFs...")
        print("="*50)

        # Check how many images we currently have
        current_images = len([f for f in os.listdir(config.IMAGE_SAVE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
        print(f"📊 Current images in folder: {current_images}")

        if current_images <= 1:
            print("🔄 Extracting images from PDF to have more data...")

            # Extract from map.pdf if it exists
            if os.path.exists(os.path.join(config.PDF_FOLDER_PATH, "map.pdf")):
                imagens_extraidas = extrair_imagens_do_pdf(
                    os.path.join(config.PDF_FOLDER_PATH, "map.pdf"),
                    config.IMAGE_SAVE_DIR,
                    "map"
                )

                if imagens_extraidas:
                    print(f"\n✅ {len(imagens_extraidas)} new images added!")
                else:
                    print("❌ No images were extracted from PDF")
            else:
                print("❌ File map/map.pdf not found")

                # Check for other available PDFs
                print("\n🔍 Looking for other PDFs...")
                pdf_paths = []
                for root, dirs, files in os.walk("."):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_paths.append(os.path.join(root, file))

                if pdf_paths:
                    print("📋 PDFs found:")
                    for i, pdf_path in enumerate(pdf_paths[:3], 1):
                        print(f"  {i}. {pdf_path}")

                    # Process the first PDF found
                    if pdf_paths:
                        primeiro_pdf = pdf_paths[0]
                        print(f"\n🔄 Processing: {primeiro_pdf}")
                        imagens_extraidas = extrair_imagens_do_pdf(primeiro_pdf, config.IMAGE_SAVE_DIR, "doc")

                        if imagens_extraidas:
                            print(f"\n✅ {len(imagens_extraidas)} images extracted from {primeiro_pdf}!")
                else:
                    print("❌ No PDF found to extract images")
        else:
            print("✅ There are already multiple images in folder")
    
    # 3. Process images from folder
    print(f"\n📂 PROCESSING IMAGES FROM FOLDER...")
    print("="*50)

    image_metadata_df = processar_imagens_da_pasta(
        pasta_imagens=config.IMAGE_SAVE_DIR,
        embedding_size=config.EMBEDDING_SIZE,
        gerar_descricoes=True,
        formatos_suportados=['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    )

    if image_metadata_df.empty:
        print("❌ FAILED: No images were processed")
        return False

    # Save DataFrame for future use
    try:
        image_metadata_df.to_pickle("image_metadata_from_folder.pkl")
        print(f"\n💾 DataFrame saved to 'image_metadata_from_folder.pkl'")
    except Exception as save_error:
        print(f"\n⚠️  Could not save: {save_error}")

    # 4. Similarity search validation
    print(f"\n🔍 SIMILARITY SEARCH VALIDATION...")
    print("="*50)

    matching_results = validar_busca_similaridade(image_metadata_df, args.target_image)

    # 5. Contextual analysis (if we have results)
    if matching_results:
        print(f"\n🤖 CONTEXTUAL ANALYSIS...")
        print("="*50)

        # Find target image for analysis
        target_image_path = None
        for idx, row in image_metadata_df.iterrows():
            if args.target_image.lower() in row['original_filename'].lower():
                target_image_path = row['img_path']
                break

        if target_image_path:
            analise_contextual_com_gemini(target_image_path, matching_results, multimodal_model_2_0_flash)
        else:
            print(f"❌ Target image '{args.target_image}' not found for contextual analysis")

    # 6. Direct analysis (if requested)
    if args.direct_analysis:
        print(f"\n🔍 DIRECT ANALYSIS...")
        print("="*50)

        # Find image for direct analysis
        target_image_path = None
        for idx, row in image_metadata_df.iterrows():
            if args.target_image.lower() in row['original_filename'].lower():
                target_image_path = row['img_path']
                break

        if target_image_path:
            analise_direta_com_gemini(target_image_path, multimodal_model_2_0_flash)
        else:
            print(f"❌ Target image '{args.target_image}' not found for direct analysis")

    print(f"\n🎉 MULTIMODAL RAG SYSTEM EXECUTED SUCCESSFULLY!")
    print("="*60)

    return True

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def criar_parser():
    """Creates the command line argument parser"""
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
    
    # Project configuration
    parser.add_argument("--project-id", type=str, help="Google Cloud project ID")
    parser.add_argument("--location", type=str, default="us-central1", help="Vertex AI location")

    # Processing configuration
    parser.add_argument("--embedding-size", type=int, default=512, choices=[128, 256, 512, 1408], help="Embedding size")
    parser.add_argument("--image-dir", type=str, default="images/", help="Images directory")
    parser.add_argument("--pdf-dir", type=str, default="map/", help="PDFs directory")

    # Execution options
    parser.add_argument("--extract-pdf", action="store_true", help="Extract images from PDFs before processing")
    parser.add_argument("--direct-analysis", action="store_true", help="Run direct analysis with Gemini")
    parser.add_argument("--target-image", type=str, default="M3.jpeg", help="Target image name for analysis")

    # Debug options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose mode")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    
    return parser

def main():
    """Main function"""
    parser = criar_parser()
    args = parser.parse_args()

    # Dry-run mode
    if args.dry_run:
        print("🔍 DRY-RUN MODE: No changes will be made")
        print(f"Settings that would be used:")
        print(f"  Project ID: {args.project_id or config.PROJECT_ID}")
        print(f"  Location: {args.location}")
        print(f"  Embedding Size: {args.embedding_size}")
        print(f"  Image Directory: {args.image_dir}")
        print(f"  PDF Directory: {args.pdf_dir}")
        print(f"  Extract PDF: {args.extract_pdf}")
        print(f"  Direct Analysis: {args.direct_analysis}")
        print(f"  Target Image: {args.target_image}")
        return

    # Execute main flow
    try:
        sucesso = executar_fluxo_completo(args)
        if sucesso:
            print("\n✅ Execution completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Execution failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
