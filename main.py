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
import markdown2

# Import functions from the multimodal RAG system
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
    print("✅ Multimodal RAG system available")
except ImportError as e:
    print(f"⚠️ Multimodal RAG system not available: {e}")
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
        print("🔄 Initializing RAG models...")
        rag_models_initialized = inicializar_modelos()

        if rag_models_initialized:
            print("✅ RAG components initialized")
        else:
            print("⚠️ Failed to initialize RAG models")
            RAG_SYSTEM_AVAILABLE = False

    except Exception as e:
        print(f"⚠️ Error initializing RAG components: {e}")
        RAG_SYSTEM_AVAILABLE = False
        rag_models_initialized = False

# Store the map information for the AI model

map_info ='''You are the Fanshawe Navigator for the Campus. Provide step-by-step walking directions based on the information you have.

You will provide directions in a clear and concise manner. Tell the user puuting yourself in the map's perspective where to go.

Provide easy instructions like "turn left", "turn right", "go straight", "take the stairs", "take the elevator", etc.

Suggest the best route to take, which means the shortest one, mentioning landmarks or notable features along the way to help with navigation.

** Some detailed information about the campus layout: **
        - Where you have for example 1063-C it means that is a corridor near room 1063.
        - -3, -2, -1 indicate inner space inside a room or area and it must not be considered for walking directions.
        - The chatbot will get information about the building, for example: A Building First Floor, and it must use that to give directions.
** Campus

** DO not use any information outside the campus map context. For example**
        - Continue straight down this hall, passing rooms A1010, A1012, and A1014 on your left.
        - Near the center of the building.
        - You will pass rooms 1012, 1014, and 1016 on your left-hand side.

** Example of good walking directions: **
        **Walking Directions: Room A1010 to A1018**

            1. Exit room 1010 into the main hallway.
            2. Turn right and walk down the corridor.
            3. Continue straight for a short distance.
            4. Turn right on the corridor.
            5. Cross the corridor and the room 1018 will be on your left-hand side. 

'''

class ImageFileHandler(FileSystemEventHandler):
    """Handler to monitor changes in the images folder"""

    def __init__(self, image_manager):
        self.image_manager = image_manager
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        self.last_update = 0
        self.update_delay = 5  # 5-second delay to avoid multiple updates

    def on_created(self, event):
        """Called when a file is created"""
        if not event.is_directory and self._is_image_file(event.src_path):
            self._schedule_update("created", event.src_path)

    def on_deleted(self, event):
        """Called when a file is deleted"""
        if not event.is_directory and self._is_image_file(event.src_path):
            self._schedule_update("deleted", event.src_path)

    def on_modified(self, event):
        """Called when a file is modified"""
        if not event.is_directory and self._is_image_file(event.src_path):
            self._schedule_update("modified", event.src_path)

    def _is_image_file(self, file_path):
        """Checks if the file is a supported image format"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_formats)

    def _schedule_update(self, action, file_path):
        """Schedules an update with delay to avoid multiple updates"""
        current_time = time.time()
        if current_time - self.last_update > self.update_delay:
            self.last_update = current_time
            print(f"🔄 File {action}: {os.path.basename(file_path)}")
            print("⏰ Scheduling automatic embeddings update...")

            # Execute update in separate thread to avoid blocking
            threading.Thread(
                target=self._update_embeddings_async,
                daemon=True
            ).start()

    def _update_embeddings_async(self):
        """Updates embeddings asynchronously"""
        try:
            time.sleep(2)  # Wait a bit to ensure the file was completely written
            success = self.image_manager.update_embeddings(force_reprocess=False)
            if success:
                print("✅ Embeddings updated automatically")
            else:
                print("⚠️ Failed to automatically update embeddings")
        except Exception as e:
            print(f"❌ Error in automatic update: {e}")

class AutoImageUpdater:
    """Automatic image update manager"""

    def __init__(self, image_manager, images_folder="images/"):
        self.image_manager = image_manager
        self.images_folder = images_folder
        self.observer = None
        self.is_running = False

    def start_monitoring(self):
        """Starts automatic monitoring of the images folder"""
        if self.is_running:
            print("⚠️ Monitoring is already active")
            return

        try:
            if not os.path.exists(self.images_folder):
                print(f"⚠️ Folder {self.images_folder} does not exist")
                return

            # Create observer and handler
            self.observer = Observer()
            event_handler = ImageFileHandler(self.image_manager)

            # Configure monitoring
            self.observer.schedule(
                event_handler,
                self.images_folder,
                recursive=False
            )

            # Start monitoring
            self.observer.start()
            self.is_running = True

            print(f"✅ Automatic monitoring started for: {self.images_folder}")
            print("🔄 System will automatically detect new images and update embeddings")

        except Exception as e:
            print(f"❌ Error starting monitoring: {e}")

    def stop_monitoring(self):
        """Stops automatic monitoring"""
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            print("✅ Automatic monitoring stopped")

    def get_status(self):
        """Returns monitoring status"""
        return {
            "is_running": self.is_running,
            "images_folder": self.images_folder,
            "observer_active": self.observer is not None and self.observer.is_alive()
        }

class AdvancedImageManager:
    """Advanced image manager with embeddings for navigation"""

    def __init__(self, images_folder: str = "images/"):
        self.images_folder = images_folder
        self.image_metadata_df = None
        self.is_initialized = False
        self.cache_file = "image_metadata_cache.pkl"
        self.initialize()

    def initialize(self):
        """Initializes the image processing system"""
        if not RAG_SYSTEM_AVAILABLE:
            print("⚠️ RAG system not available - using simple mode")
            return

        # Check if RAG models were initialized
        if not rag_models_initialized:
            print("⚠️ RAG models not initialized - using simple mode")
            return

        try:
            # Try to load cache first
            if self.load_cache():
                print("✅ Image cache loaded successfully")
                self.is_initialized = True
                return

            # If there's no cache, process images
            print("🔄 Processing images from folder...")
            self.process_images()

            if self.image_metadata_df is not None and not self.image_metadata_df.empty:
                self.save_cache()
                self.is_initialized = True
                print(f"✅ {len(self.image_metadata_df)} images processed with embeddings")
            else:
                print("⚠️ No images were processed")

        except Exception as e:
            print(f"❌ Error initializing image manager: {e}")

    def process_images(self):
        """Processes images using the complete embeddings system"""
        try:
            self.image_metadata_df = processar_imagens_da_pasta(
                pasta_imagens=self.images_folder,
                embedding_size=512,
                gerar_descricoes=True,
                formatos_suportados=['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
            )
        except Exception as e:
            print(f"❌ Error processing images: {e}")
            self.image_metadata_df = None

    def load_cache(self) -> bool:
        """Loads processed images cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    self.image_metadata_df = pickle.load(f)
                return True
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
        return False

    def save_cache(self):
        """Saves processed images cache"""
        try:
            if self.image_metadata_df is not None:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.image_metadata_df, f)
                print("💾 Image cache saved")
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
    
    def find_relevant_images(self, user_message: str, top_n: int = 3) -> List[Dict]:
        """Finds relevant images based on user message"""
        if not self.is_initialized or self.image_metadata_df is None or self.image_metadata_df.empty:
            return []

        try:
            # Generate embedding from user message
            user_embedding = get_text_embedding_from_text_embedding_model(user_message)
            user_embedding = np.array(user_embedding)

            # Search for similar images using text embeddings from descriptions
            similar_images = buscar_imagens_similares_com_embedding(
                user_embedding,
                self.image_metadata_df,
                top_n=top_n,
                column_name="text_embedding_from_image_description"
            )

            return similar_images
        except Exception as e:
            print(f"❌ Error finding relevant images: {e}")
            return []

    def get_image_context_for_prompt(self, user_message: str) -> str:
        """Generates context from relevant images to include in the prompt"""
        if not self.is_initialized:
            return ""

        relevant_images = self.find_relevant_images(user_message, top_n=2)

        if not relevant_images:
            return ""

        context = "\n\nRELEVANT VISUAL INFORMATION:\n"
        context += "Based on your query, I found the following relevant visual information:\n\n"

        for i, img_info in enumerate(relevant_images, 1):
            context += f"**Image {i} ({img_info.get('original_filename', 'N/A')}):**\n"
            context += f"Description: {img_info.get('img_desc', 'N/A')}\n"
            context += f"Relevance: {img_info.get('cosine_score', 0):.3f}\n\n"

        context += "Use this visual information to provide more precise and detailed directions."
        return context
    
    def update_embeddings(self, force_reprocess: bool = False) -> bool:
        """Updates image embeddings"""
        if not RAG_SYSTEM_AVAILABLE or not rag_models_initialized:
            print("⚠️ RAG system not available for update")
            return False

        try:
            print("🔄 Updating image embeddings...")

            # Check for new images
            current_images = set()
            if self.image_metadata_df is not None:
                current_images = set(self.image_metadata_df['original_filename'].tolist())

            # List current images in folder
            if os.path.exists(self.images_folder):
                folder_images = set()
                for filename in os.listdir(self.images_folder):
                    if any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']):
                        folder_images.add(filename)

                new_images = folder_images - current_images
                removed_images = current_images - folder_images

                if new_images:
                    print(f"📊 New images found: {list(new_images)}")
                if removed_images:
                    print(f"📊 Removed images: {list(removed_images)}")

                if not new_images and not removed_images and not force_reprocess:
                    print("✅ No update needed")
                    return True

            # Reprocess all images
            print("🔄 Reprocessing all images...")
            self.process_images()

            if self.image_metadata_df is not None and not self.image_metadata_df.empty:
                self.save_cache()
                self.is_initialized = True
                print(f"✅ {len(self.image_metadata_df)} images processed with updated embeddings")
                return True
            else:
                print("⚠️ No images were processed")
                return False

        except Exception as e:
            print(f"❌ Error updating embeddings: {e}")
            return False

    def clear_cache(self) -> bool:
        """Clears the embeddings cache"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                print(f"✅ Cache removed: {self.cache_file}")
            self.image_metadata_df = None
            self.is_initialized = False
            return True
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Returns image manager status"""
        # Count images in folder
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
            print(f"🔍 Using visual information for: {user_message[:50]}...")
        else:
            prompt = f'{map_info}\n\nUser: {user_message}\nAI:'
            print(f"📝 Using only textual information for: {user_message[:50]}...")

        # Generate a response from the AI model
        response = model.generate_content(prompt)

        # Convert Markdown to HTML
        html_response = markdown2.markdown(response.text)

        return jsonify({"reply": html_response})
        
    except Exception as e:
        print(f"Error generating content: {e}") # Added for debugging
        return jsonify({"reply": f"An error occurred: {e}"}), 500

@app.route("/images/status", methods=['GET'])
def images_status():
    """Returns image system and embeddings status"""
    status = image_manager.get_status()
    return jsonify(status)

@app.route("/system/status", methods=['GET'])
def system_status():
    """Returns complete system status"""
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
    """Updates image embeddings"""
    try:
        force = request.json.get('force', False) if request.json else False
        success = image_manager.update_embeddings(force_reprocess=force)

        if success:
            return jsonify({
                "status": "success",
                "message": "Embeddings updated successfully",
                "data": image_manager.get_status()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to update embeddings"
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error updating embeddings: {str(e)}"
        }), 500

@app.route("/images/clear-cache", methods=['POST'])
def clear_image_cache():
    """Clears image embeddings cache"""
    try:
        success = image_manager.clear_cache()

        if success:
            return jsonify({
                "status": "success",
                "message": "Cache cleared successfully",
                "data": image_manager.get_status()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to clear cache"
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error clearing cache: {str(e)}"
        }), 500

@app.route("/images/auto-monitor/start", methods=['POST'])
def start_auto_monitoring():
    """Starts automatic image monitoring"""
    try:
        auto_updater.start_monitoring()
        return jsonify({
            "status": "success",
            "message": "Automatic monitoring started",
            "data": auto_updater.get_status()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error starting monitoring: {str(e)}"
        }), 500

@app.route("/images/auto-monitor/stop", methods=['POST'])
def stop_auto_monitoring():
    """Stops automatic image monitoring"""
    try:
        auto_updater.stop_monitoring()
        return jsonify({
            "status": "success",
            "message": "Automatic monitoring stopped",
            "data": auto_updater.get_status()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error stopping monitoring: {str(e)}"
        }), 500

@app.route("/images/auto-monitor/status", methods=['GET'])
def auto_monitoring_status():
    """Returns automatic monitoring status"""
    return jsonify(auto_updater.get_status())

def main():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081)))


if __name__ == "__main__":
    main()
