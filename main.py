import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import pickle
from pathlib import Path
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Importar funções do sistema RAG multimodal
try:
    from multimodal_rag_complete import (
        processar_imagens_da_pasta,
        buscar_imagens_similares_com_embedding,
        get_image_embedding_from_multimodal_embedding_model,
        get_text_embedding_from_text_embedding_model,
        get_gemini_response,
        get_cosine_score,
        inicializar_modelos
    )
    from src.models.embedding_models import EmbeddingModelManager
    from src.models.gemini_models import GeminiModelManager
    from src.config.settings import RAGConfig
    RAG_SYSTEM_AVAILABLE = True
    print("✅ Sistema RAG multimodal disponível")
except ImportError as e:
    print(f"⚠️ Sistema RAG multimodal não disponível: {e}")
    RAG_SYSTEM_AVAILABLE = False

load_dotenv()

# The 'templates' folder is the default for Flask, so we just need to tell it where the static files are.
app = Flask(__name__, static_folder='static')

# Configure the generative AI model
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise KeyError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    # Use a model name confirmed to be available
    model = genai.GenerativeModel('gemini-pro-latest')
except KeyError as e:
    print(e)
    model = None

# Initialize RAG system components
rag_config = None
embedding_manager = None
gemini_manager = None
multimodal_model = None
rag_models_initialized = False

if RAG_SYSTEM_AVAILABLE:
    try:
        # Initialize configuration
        rag_config = RAGConfig()
        rag_config.PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "")
        
        # Initialize embedding manager
        embedding_manager = EmbeddingModelManager(embedding_size=512)
        
        # Initialize Gemini manager
        gemini_manager = GeminiModelManager(
            project_id=rag_config.PROJECT_ID,
            location=rag_config.LOCATION
        )
        
        # Initialize RAG models (this sets up the global variables)
        print("🔄 Inicializando modelos RAG...")
        rag_models_initialized = inicializar_modelos()
        
        if rag_models_initialized:
            print("✅ Componentes RAG inicializados")
        else:
            print("⚠️ Falha na inicialização dos modelos RAG")
            RAG_SYSTEM_AVAILABLE = False
            
    except Exception as e:
        print(f"⚠️ Erro ao inicializar componentes RAG: {e}")
        RAG_SYSTEM_AVAILABLE = False
        rag_models_initialized = False

# Store the map information for the AI model
map_info = '''You are a map navigator for the M1 Blue Building. Provide step-by-step walking directions based on the information below.
Format your response using simple HTML tags for clarity. For example: use <strong> for emphasis, <ul> and <li> for lists, and <br> for line breaks.

**1. General Info**

*   The M1 Blue Building is located between Applied Arts Lane (west) and Campus Drive (east).
*   The main entrance is on the south side, near Rooms 1004 and 1006.
*   There are accessible entrances on both the south and east sides.
*   Nearby buildings: Building H (to the south-west, connected by a hallway) and Building K (to the north-west).
*   Nearby parking: Lot 2 (Assigned Parking, east) and P3 Meters (south-east).
*   A compass rose is provided on the map (North is up).

**2. Key Rooms**

*   **1003:** Large classroom, just inside the south entrance (west side).
*   **1004 & 1006:** Small classrooms right at the south entrance (east side).
*   **1013–14:** Midway up the main hall, east side.
*   **1015–16:** Across the hall from 1013–14, west side.
*   **1020, 1022, 1024, 1026:** Computer labs, west side of the main hall.
*   **1033:** Main office, in the north-east corner.
*   **Stairs:** Located at the north end of the main hall.
*   **Elevator:** Located just south of the stairs.
*   **Washrooms:** Two sets: one near the south entrance (across from 1003) and another at the north end, near the stairs.
*   **Connecting Hallway to Building H:** West side, between rooms 1015 and 1020.

**3. Example Directions**

*   **To Room 1033 (Main Office) from the South Entrance:**
    1.  Enter through the south doors.
    2.  Walk straight north, down the main hallway.
    3.  Continue past all the classrooms and labs.
    4.  The Main Office (1033) will be on your right in the north-east corner of the building.
*   **To the Elevator from the South Entrance:**
    1.  Enter through the south doors.
    2.  Walk straight north, down the main hallway.
    3.  The elevator is at the far north end of the hall, just before the stairs, on your right.
'''

class ImageFileHandler(FileSystemEventHandler):
    """Handler para monitorar mudanças na pasta de imagens"""
    
    def __init__(self, image_manager):
        self.image_manager = image_manager
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        self.last_update = 0
        self.update_delay = 5  # Delay de 5 segundos para evitar múltiplas atualizações
    
    def on_created(self, event):
        """Chamado quando um arquivo é criado"""
        if not event.is_directory and self._is_image_file(event.src_path):
            self._schedule_update("criado", event.src_path)
    
    def on_deleted(self, event):
        """Chamado quando um arquivo é deletado"""
        if not event.is_directory and self._is_image_file(event.src_path):
            self._schedule_update("deletado", event.src_path)
    
    def on_modified(self, event):
        """Chamado quando um arquivo é modificado"""
        if not event.is_directory and self._is_image_file(event.src_path):
            self._schedule_update("modificado", event.src_path)
    
    def _is_image_file(self, file_path):
        """Verifica se o arquivo é uma imagem suportada"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_formats)
    
    def _schedule_update(self, action, file_path):
        """Agenda uma atualização com delay para evitar múltiplas atualizações"""
        current_time = time.time()
        if current_time - self.last_update > self.update_delay:
            self.last_update = current_time
            print(f"🔄 Arquivo {action}: {os.path.basename(file_path)}")
            print("⏰ Agendando atualização automática de embeddings...")
            
            # Executar atualização em thread separada para não bloquear
            threading.Thread(
                target=self._update_embeddings_async,
                daemon=True
            ).start()
    
    def _update_embeddings_async(self):
        """Atualiza embeddings de forma assíncrona"""
        try:
            time.sleep(2)  # Aguardar um pouco para garantir que o arquivo foi completamente escrito
            success = self.image_manager.update_embeddings(force_reprocess=False)
            if success:
                print("✅ Embeddings atualizados automaticamente")
            else:
                print("⚠️ Falha na atualização automática de embeddings")
        except Exception as e:
            print(f"❌ Erro na atualização automática: {e}")

class AutoImageUpdater:
    """Gerenciador automático de atualização de imagens"""
    
    def __init__(self, image_manager, images_folder="images/"):
        self.image_manager = image_manager
        self.images_folder = images_folder
        self.observer = None
        self.is_running = False
    
    def start_monitoring(self):
        """Inicia o monitoramento automático da pasta de imagens"""
        if self.is_running:
            print("⚠️ Monitoramento já está ativo")
            return
        
        try:
            if not os.path.exists(self.images_folder):
                print(f"⚠️ Pasta {self.images_folder} não existe")
                return
            
            # Criar observer e handler
            self.observer = Observer()
            event_handler = ImageFileHandler(self.image_manager)
            
            # Configurar monitoramento
            self.observer.schedule(
                event_handler,
                self.images_folder,
                recursive=False
            )
            
            # Iniciar monitoramento
            self.observer.start()
            self.is_running = True
            
            print(f"✅ Monitoramento automático iniciado para: {self.images_folder}")
            print("🔄 Sistema detectará automaticamente novas imagens e atualizará embeddings")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar monitoramento: {e}")
    
    def stop_monitoring(self):
        """Para o monitoramento automático"""
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            print("✅ Monitoramento automático parado")
    
    def get_status(self):
        """Retorna status do monitoramento"""
        return {
            "is_running": self.is_running,
            "images_folder": self.images_folder,
            "observer_active": self.observer is not None and self.observer.is_alive()
        }

class AdvancedImageManager:
    """Gerenciador avançado de imagens com embeddings para navegação"""
    
    def __init__(self, images_folder: str = "images/"):
        self.images_folder = images_folder
        self.image_metadata_df = None
        self.is_initialized = False
        self.cache_file = "image_metadata_cache.pkl"
        self.initialize()
    
    def initialize(self):
        """Inicializa o sistema de processamento de imagens"""
        if not RAG_SYSTEM_AVAILABLE:
            print("⚠️ Sistema RAG não disponível - usando modo simples")
            return
        
        # Verificar se os modelos RAG foram inicializados
        if not rag_models_initialized:
            print("⚠️ Modelos RAG não inicializados - usando modo simples")
            return
        
        try:
            # Tentar carregar cache primeiro
            if self.load_cache():
                print("✅ Cache de imagens carregado com sucesso")
                self.is_initialized = True
                return
            
            # Se não há cache, processar imagens
            print("🔄 Processando imagens da pasta...")
            self.process_images()
            
            if self.image_metadata_df is not None and not self.image_metadata_df.empty:
                self.save_cache()
                self.is_initialized = True
                print(f"✅ {len(self.image_metadata_df)} imagens processadas com embeddings")
            else:
                print("⚠️ Nenhuma imagem foi processada")
                
        except Exception as e:
            print(f"❌ Erro ao inicializar gerenciador de imagens: {e}")
    
    def process_images(self):
        """Processa imagens usando o sistema completo de embeddings"""
        try:
            self.image_metadata_df = processar_imagens_da_pasta(
                pasta_imagens=self.images_folder,
                embedding_size=512,
                gerar_descricoes=True,
                formatos_suportados=['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
            )
        except Exception as e:
            print(f"❌ Erro ao processar imagens: {e}")
            self.image_metadata_df = None
    
    def load_cache(self) -> bool:
        """Carrega cache de imagens processadas"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    self.image_metadata_df = pickle.load(f)
                return True
        except Exception as e:
            print(f"⚠️ Erro ao carregar cache: {e}")
        return False
    
    def save_cache(self):
        """Salva cache de imagens processadas"""
        try:
            if self.image_metadata_df is not None:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.image_metadata_df, f)
                print("💾 Cache de imagens salvo")
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {e}")
    
    def find_relevant_images(self, user_message: str, top_n: int = 3) -> List[Dict]:
        """Encontra imagens relevantes baseado na mensagem do usuário"""
        if not self.is_initialized or self.image_metadata_df is None or self.image_metadata_df.empty:
            return []
        
        try:
            # Gerar embedding da mensagem do usuário
            user_embedding = get_text_embedding_from_text_embedding_model(user_message)
            user_embedding = np.array(user_embedding)
            
            # Buscar imagens similares usando embeddings de texto das descrições
            similar_images = buscar_imagens_similares_com_embedding(
                user_embedding,
                self.image_metadata_df,
                top_n=top_n,
                column_name="text_embedding_from_image_description"
            )
            
            return similar_images
        except Exception as e:
            print(f"❌ Erro ao buscar imagens relevantes: {e}")
            return []
    
    def get_image_context_for_prompt(self, user_message: str) -> str:
        """Gera contexto das imagens relevantes para incluir no prompt"""
        if not self.is_initialized:
            return ""
        
        relevant_images = self.find_relevant_images(user_message, top_n=2)
        
        if not relevant_images:
            return ""
        
        context = "\n\nINFORMAÇÕES VISUAIS RELEVANTES:\n"
        context += "Baseado na sua consulta, encontrei as seguintes informações visuais relevantes:\n\n"
        
        for i, img_info in enumerate(relevant_images, 1):
            context += f"**Imagem {i} ({img_info.get('original_filename', 'N/A')}):**\n"
            context += f"Descrição: {img_info.get('img_desc', 'N/A')}\n"
            context += f"Relevância: {img_info.get('cosine_score', 0):.3f}\n\n"
        
        context += "Use essas informações visuais para fornecer direções mais precisas e detalhadas."
        return context
    
    def update_embeddings(self, force_reprocess: bool = False) -> bool:
        """Atualiza embeddings das imagens"""
        if not RAG_SYSTEM_AVAILABLE or not rag_models_initialized:
            print("⚠️ Sistema RAG não disponível para atualização")
            return False
        
        try:
            print("🔄 Atualizando embeddings das imagens...")
            
            # Verificar se há novas imagens
            current_images = set()
            if self.image_metadata_df is not None:
                current_images = set(self.image_metadata_df['original_filename'].tolist())
            
            # Listar imagens atuais na pasta
            if os.path.exists(self.images_folder):
                folder_images = set()
                for filename in os.listdir(self.images_folder):
                    if any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']):
                        folder_images.add(filename)
                
                new_images = folder_images - current_images
                removed_images = current_images - folder_images
                
                if new_images:
                    print(f"📊 Novas imagens encontradas: {list(new_images)}")
                if removed_images:
                    print(f"📊 Imagens removidas: {list(removed_images)}")
                
                if not new_images and not removed_images and not force_reprocess:
                    print("✅ Nenhuma atualização necessária")
                    return True
            
            # Reprocessar todas as imagens
            print("🔄 Reprocessando todas as imagens...")
            self.process_images()
            
            if self.image_metadata_df is not None and not self.image_metadata_df.empty:
                self.save_cache()
                self.is_initialized = True
                print(f"✅ {len(self.image_metadata_df)} imagens processadas com embeddings atualizados")
                return True
            else:
                print("⚠️ Nenhuma imagem foi processada")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao atualizar embeddings: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """Limpa o cache de embeddings"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                print(f"✅ Cache removido: {self.cache_file}")
            self.image_metadata_df = None
            self.is_initialized = False
            return True
        except Exception as e:
            print(f"❌ Erro ao limpar cache: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do gerenciador de imagens"""
        # Contar imagens na pasta
        folder_image_count = 0
        if os.path.exists(self.images_folder):
            folder_image_count = len([f for f in os.listdir(self.images_folder) 
                                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'))])
        
        return {
            "initialized": self.is_initialized,
            "total_images": len(self.image_metadata_df) if self.image_metadata_df is not None else 0,
            "folder_image_count": folder_image_count,
            "images_folder": self.images_folder,
            "cache_file": self.cache_file,
            "cache_exists": os.path.exists(self.cache_file),
            "rag_available": RAG_SYSTEM_AVAILABLE,
            "rag_models_initialized": rag_models_initialized if 'rag_models_initialized' in globals() else False
        }

# Initialize image manager
image_manager = AdvancedImageManager("images/")

# Initialize automatic image updater
auto_updater = AutoImageUpdater(image_manager, "images/")

# Start automatic monitoring
auto_updater.start_monitoring()

@app.route("/")
def index():
    # Use render_template to serve the HTML file from the 'templates' directory
    return render_template('index.html')

@app.route("/chat", methods=['POST'])
def chat():
    if model is None:
        return jsonify({"reply": "The AI model is not configured. Please set the GEMINI_API_KEY environment variable."}), 500

    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Please provide a message."}), 400

    try:
        # Get image context if available
        image_context = image_manager.get_image_context_for_prompt(user_message)
        
        # Combine map info + image context + user message
        if image_context:
            prompt = f'{map_info}{image_context}\n\nUser: {user_message}\nAI:'
            print(f"🔍 Usando informações visuais para: {user_message[:50]}...")
        else:
            prompt = f'{map_info}\n\nUser: {user_message}\nAI:'
            print(f"📝 Usando apenas informações textuais para: {user_message[:50]}...")

        # Generate a response from the AI model
        response = model.generate_content(prompt)
        return jsonify({"reply": response.text})
        
    except Exception as e:
        print(f"Error generating content: {e}") # Added for debugging
        return jsonify({"reply": f"An error occurred: {e}"}), 500

@app.route("/images/status", methods=['GET'])
def images_status():
    """Retorna status do sistema de imagens e embeddings"""
    status = image_manager.get_status()
    return jsonify(status)

@app.route("/system/status", methods=['GET'])
def system_status():
    """Retorna status completo do sistema"""
    return jsonify({
        "gemini_model": "configured" if model is not None else "not_configured",
        "rag_system": "available" if RAG_SYSTEM_AVAILABLE else "not_available",
        "image_manager": image_manager.get_status(),
        "auto_monitoring": auto_updater.get_status(),
        "environment": {
            "gemini_api_key": "set" if os.getenv("GEMINI_API_KEY") else "not_set",
            "google_cloud_project": "set" if os.getenv("GOOGLE_CLOUD_PROJECT_ID") else "not_set"
        }
    })

@app.route("/images/update", methods=['POST'])
def update_images():
    """Atualiza embeddings das imagens"""
    try:
        force = request.json.get('force', False) if request.json else False
        success = image_manager.update_embeddings(force_reprocess=force)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Embeddings atualizados com sucesso",
                "data": image_manager.get_status()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Falha ao atualizar embeddings"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao atualizar embeddings: {str(e)}"
        }), 500

@app.route("/images/clear-cache", methods=['POST'])
def clear_image_cache():
    """Limpa o cache de embeddings das imagens"""
    try:
        success = image_manager.clear_cache()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Cache limpo com sucesso",
                "data": image_manager.get_status()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Falha ao limpar cache"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao limpar cache: {str(e)}"
        }), 500

@app.route("/images/auto-monitor/start", methods=['POST'])
def start_auto_monitoring():
    """Inicia o monitoramento automático de imagens"""
    try:
        auto_updater.start_monitoring()
        return jsonify({
            "status": "success",
            "message": "Monitoramento automático iniciado",
            "data": auto_updater.get_status()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao iniciar monitoramento: {str(e)}"
        }), 500

@app.route("/images/auto-monitor/stop", methods=['POST'])
def stop_auto_monitoring():
    """Para o monitoramento automático de imagens"""
    try:
        auto_updater.stop_monitoring()
        return jsonify({
            "status": "success",
            "message": "Monitoramento automático parado",
            "data": auto_updater.get_status()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao parar monitoramento: {str(e)}"
        }), 500

@app.route("/images/auto-monitor/status", methods=['GET'])
def auto_monitoring_status():
    """Retorna status do monitoramento automático"""
    return jsonify(auto_updater.get_status())

def main():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081)))


if __name__ == "__main__":
    main()
