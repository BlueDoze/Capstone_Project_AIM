import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, send_from_directory
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
import json
import re

# Import functions from the multimodal RAG system
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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

# Load Building M room configuration
try:
    config_path = Path('config/building_m_rooms.json')
    with open(config_path, 'r') as f:
        building_m_config = json.load(f)['Building M']
    print("✅ Building M room configuration loaded")
except Exception as e:
    print(f"⚠️ Failed to load room configuration: {e}")
    building_m_config = {}

# Configure the generative AI model
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise KeyError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    
    # Configure generation settings with temperature 0.5 for balanced navigation instructions
    generation_config = genai.types.GenerationConfig(
        temperature=0.5,
        max_output_tokens=2048,
        top_p=0.95,
        top_k=40
    )
    
    # Use a model name confirmed to be available
    model = genai.GenerativeModel(
        'gemini-pro-latest',
        generation_config=generation_config
    )
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

You will provide directions in a clear and concise manner. Tell the user putting yourself in the map's perspective where to go. 

#Invert the instructions about right and left, e.g "turn right" becomes "turn left" and vice versa.

Provide easy instructions like "turn left", "turn right", "go straight", "take the stairs", "take the elevator", etc.

Suggest the best route to take, which means the shortest one, mentioning landmarks or notable features along the way to help with navigation.

** Some detailed information about the campus layout: **
        - Where you have for example 1063-C it means that is a corridor near room 1063.
        - Corridors are marked with blue color path, the user must walk through these blue paths to get into destination.
        - -3, -2, -1 indicate inner space inside a room or area and it must not be considered for walking directions.
        - The chatbot will get information about the building, for example: A Building First Floor, and it must use that to give directions.
** Campus

** DO not use any information outside the campus map context. For example**
        - Continue straight down this hall, passing rooms A1010, A1012, and A1014 on your left.
        - Near the center of the building.
        - You will pass rooms 1012, 1014, and 1016 on your left-hand side.

** Example of good walking directions: **
        **Walking Directions: Room A1010 to A1018**

            #1. Exit room 1010 into the main hallway.
            #2. Turn right and walk down the corridor.
            #3. Continue straight for a short distance.
            #4. Turn right on the corridor.
            #5. Cross the corridor and the room 1018 will be on your left-hand side. 

'''

# Events information prompt for AI model
events_prompt = '''You are the Fanshawe Events Assistant. You help students discover campus events, activities, and schedules.

You have access to information about campus events including:
- Event names, dates, and times
- Event locations (buildings and rooms)
- Event descriptions and organizers
- Registration requirements
- Links to more information

When answering about events:
- Provide clear, concise information about the events
- Include relevant details like date, time, location, and organizer
- If multiple events match the query, list them clearly
- Suggest relevant events based on the user's interests
- If an event requires registration, mention it
- Include links when available

Be helpful, friendly, and enthusiastic about campus events!
'''

# Restaurant information prompt for AI model
restaurants_prompt = '''You are the Fanshawe Dining Guide. You help students find food and dining options on campus.

You have access to information about campus dining including:
- Restaurant and cafe names and locations
- Operating hours for each day
- Cuisine types and menu highlights
- Payment methods accepted
- Building and floor locations

When answering about dining:
- Provide clear information about location and hours
- Mention what type of food is available
- Include operating hours, especially for today
- Suggest options based on the user's needs (quick snack, full meal, coffee, etc.)
- Mention payment methods if relevant
- Be aware of current day/time when suggesting options

Be helpful, friendly, and make it easy for students to find what they're looking for!
'''

# Announcements information prompt for AI model
announcements_prompt = '''You are the Fanshawe Announcements Assistant. You help students stay informed about course announcements and important updates from D2L.

You have access to information about:
- Recent course announcements from instructors
- Important class updates and reminders
- Assignment and exam notifications
- Course-related news and changes
- Posted dates and content of announcements

When answering about announcements:
- Provide clear, concise summaries of announcements
- Include dates when announcements were posted
- Highlight action items (deadlines, required attendance, submissions, etc.)
- Prioritize recent and urgent announcements
- Mention the instructor or source when relevant
- If multiple announcements match, list them chronologically (most recent first)
- Be aware of deadlines and time-sensitive information

Be helpful, organized, and ensure students don't miss important information!
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

# ============== NAVIGATION HELPER FUNCTIONS ==============

def resolve_room_name(room_name: str) -> Optional[str]:
    """
    Resolve a user-provided room name to the official room ID
    Handles aliases like "1003", "bathroom men", etc.
    """
    if not building_m_config:
        return None

    # Normalize input
    normalized = room_name.lower().strip()

    # Check aliases
    aliases = building_m_config.get('aliases', {})
    if normalized in aliases:
        return aliases[normalized]

    # Try to match room ID directly
    room_to_node = building_m_config.get('roomToNode', {})
    if room_name in room_to_node:
        return room_name

    return None

def parse_navigation_request(user_message: str) -> Dict[str, Any]:
    """
    Parse navigation request from user message
    Uses Gemini to extract start and end locations
    Returns dict with: {is_navigation, start, end, startNode, endNode, building, floor}
    """
    if not model:
        return {'is_navigation': False}

    # Check if message looks like a navigation request
    nav_keywords = ['how', 'get', 'go', 'navigate', 'path', 'way', 'direction',
                    'from', 'to', 'reach', 'find', 'como', 'ir', 'chegar']
    message_lower = user_message.lower()
    is_likely_nav = any(keyword in message_lower for keyword in nav_keywords)

    if not is_likely_nav:
        return {'is_navigation': False}

    try:
        # Use Gemini to parse the navigation request
        parse_prompt = f"""Extract the start location and destination from this message.
        Return ONLY a JSON response with this format (no other text):
        {{"is_navigation": true/false, "start": "location or null", "end": "location or null"}}

        Message: {user_message}

        For "location", use room numbers like "1003" or common names like "bathroom men", "elevator", "exit".
        If no navigation intent, set is_navigation to false."""

        response = model.generate_content(parse_prompt)
        response_text = response.text.strip()

        # Try to extract JSON
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())

            if parsed.get('is_navigation'):
                start_name = parsed.get('start')
                end_name = parsed.get('end')

                # Resolve room names
                start_room = resolve_room_name(start_name) if start_name else None
                end_room = resolve_room_name(end_name) if end_name else None

                if start_room and end_room:
                    # Get node IDs
                    room_to_node = building_m_config.get('roomToNode', {})
                    start_node = room_to_node.get(start_room)
                    end_node = room_to_node.get(end_room)

                    if start_node and end_node:
                        return {
                            'is_navigation': True,
                            'start': start_room,
                            'end': end_room,
                            'startNode': start_node,
                            'endNode': end_node,
                            'building': 'M',
                            'floor': 1,
                            'start_original': start_name,
                            'end_original': end_name
                        }

        return {'is_navigation': False}

    except Exception as e:
        print(f"⚠️ Error parsing navigation request: {e}")
        return {'is_navigation': False}

def get_room_friendly_name(room_id: str) -> str:
    """Get human-friendly name for a room ID"""
    if not building_m_config:
        return room_id

    descriptions = building_m_config.get('roomDescriptions', {})
    return descriptions.get(room_id, room_id)

def classify_user_intent(user_message: str) -> Dict[str, Any]:
    """
    Classifies user intent into one of four categories:
    - NAVIGATION: Directions, wayfinding, localization
    - EVENTS: Campus events, schedules, activities
    - RESTAURANTS: Food services, dining halls, cafeterias
    - OUT_OF_SCOPE: Everything else

    Returns dict with: {intent: str, confidence: float, entities: dict}
    """
    if not model:
        return {'intent': 'OUT_OF_SCOPE', 'confidence': 0.0, 'entities': {}}

    try:
        # Use keyword pre-filtering for faster classification
        message_lower = user_message.lower()

        # Navigation keywords
        nav_keywords = ['how', 'get', 'go', 'navigate', 'path', 'way', 'direction',
                        'from', 'to', 'reach', 'find', 'where', 'location', 'room',
                        'como', 'ir', 'chegar', 'onde']

        # Event keywords
        event_keywords = ['event', 'activity', 'happening', 'schedule', 'workshop',
                          'seminar', 'fair', 'meeting', 'conference', 'talk', 'when',
                          'evento', 'atividade', 'quando']

        # Restaurant keywords
        restaurant_keywords = ['food', 'eat', 'restaurant', 'cafe', 'coffee', 'lunch',
                               'dinner', 'breakfast', 'hungry', 'menu', 'dining',
                               'comida', 'comer', 'restaurante', 'lanche']

        # Announcement keywords
        announcement_keywords = ['announcement', 'anuncio', 'news', 'notice', 'update',
                                'd2l', 'brightspace', 'message', 'aviso', 'noticia',
                                'posted', 'instructor', 'professor', 'class update']

        # Count keyword matches
        nav_score = sum(1 for kw in nav_keywords if kw in message_lower)
        event_score = sum(1 for kw in event_keywords if kw in message_lower)
        restaurant_score = sum(1 for kw in restaurant_keywords if kw in message_lower)
        announcement_score = sum(1 for kw in announcement_keywords if kw in message_lower)

        # If clear winner from keywords, use it
        max_score = max(nav_score, event_score, restaurant_score, announcement_score)
        if max_score >= 2:
            if nav_score == max_score:
                return {'intent': 'NAVIGATION', 'confidence': 0.8, 'entities': {}}
            elif event_score == max_score:
                return {'intent': 'EVENTS', 'confidence': 0.8, 'entities': {}}
            elif restaurant_score == max_score:
                return {'intent': 'RESTAURANTS', 'confidence': 0.8, 'entities': {}}
            elif announcement_score == max_score:
                return {'intent': 'ANNOUNCEMENTS', 'confidence': 0.8, 'entities': {}}

        # Use Gemini for more nuanced classification
        classify_prompt = f"""Classify this user query into ONE of these categories:
        - NAVIGATION: Questions about directions, finding locations, wayfinding on campus
        - EVENTS: Questions about campus events, activities, schedules, workshops
        - RESTAURANTS: Questions about food, dining, cafeterias, restaurants on campus
        - ANNOUNCEMENTS: Questions about course announcements, D2L news, class updates, instructor messages
        - OUT_OF_SCOPE: Anything else not related to the above categories

        Return ONLY a JSON response with this format (no other text):
        {{"intent": "NAVIGATION|EVENTS|RESTAURANTS|ANNOUNCEMENTS|OUT_OF_SCOPE", "confidence": 0.0-1.0}}

        User query: {user_message}"""

        response = model.generate_content(classify_prompt)
        response_text = response.text.strip()

        # Extract JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            intent = parsed.get('intent', 'OUT_OF_SCOPE')
            confidence = parsed.get('confidence', 0.5)

            return {
                'intent': intent,
                'confidence': confidence,
                'entities': {}
            }

        return {'intent': 'OUT_OF_SCOPE', 'confidence': 0.5, 'entities': {}}

    except Exception as e:
        print(f"⚠️ Error classifying intent: {e}")
        return {'intent': 'OUT_OF_SCOPE', 'confidence': 0.0, 'entities': {}}

def handle_event_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles event-related queries by searching the events database
    and generating AI-powered responses about campus events
    """
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        # Load events data
        events_path = Path('data/campus_events.json')
        if not events_path.exists():
            return {'reply': 'Event information is currently unavailable. Please check back later.'}

        with open(events_path, 'r') as f:
            events_data = json.load(f)

        events = events_data.get('events', [])

        # Format events data as context
        events_context = "\n\n** Available Campus Events: **\n"
        for event in events:
            events_context += f"\n- **{event['name']}**\n"
            events_context += f"  Date: {event['date']}\n"
            events_context += f"  Time: {event['time']}\n"
            events_context += f"  Location: {event['location']}\n"
            events_context += f"  Organizer: {event['organizer']}\n"
            events_context += f"  Description: {event['description']}\n"
            if event.get('registration_required'):
                events_context += f"  Registration: Required\n"
            if event.get('link'):
                events_context += f"  Link: {event['link']}\n"

        # Combine events prompt + context + user query
        prompt = f"{events_prompt}\n{events_context}\n\nUser: {user_message}\nAI:"

        # Generate response
        response = model.generate_content(prompt)
        html_response = markdown2.markdown(response.text)

        print(f"📅 Event query handled: {user_message[:50]}...")

        return {'reply': html_response}

    except Exception as e:
        print(f"⚠️ Error handling event query: {e}")
        return {'reply': 'Sorry, I encountered an error while searching for events. Please try again.'}

def handle_restaurant_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles restaurant/dining queries by searching the restaurants database
    and generating AI-powered responses about campus dining options
    """
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        # Load restaurants data
        restaurants_path = Path('data/campus_restaurants.json')
        if not restaurants_path.exists():
            return {'reply': 'Restaurant information is currently unavailable. Please check back later.'}

        with open(restaurants_path, 'r') as f:
            restaurants_data = json.load(f)

        restaurants = restaurants_data.get('restaurants', [])

        # Format restaurants data as context
        from datetime import datetime
        today = datetime.now().strftime('%A').lower()

        restaurants_context = "\n\n** Campus Dining Options: **\n"
        for restaurant in restaurants:
            restaurants_context += f"\n- **{restaurant['name']}**\n"
            restaurants_context += f"  Location: {restaurant['location']}\n"
            restaurants_context += f"  Type: {restaurant['cuisine_type']}\n"

            # Show today's hours prominently
            hours = restaurant.get('hours', {})
            if today in hours:
                restaurants_context += f"  Hours Today ({today.capitalize()}): {hours[today]}\n"

            # Show menu highlights
            menu = restaurant.get('menu_highlights', [])
            if menu:
                restaurants_context += f"  Menu: {', '.join(menu)}\n"

            restaurants_context += f"  Payment: {', '.join(restaurant.get('payment_methods', []))}\n"
            restaurants_context += f"  Description: {restaurant['description']}\n"

        # Combine restaurants prompt + context + user query
        current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
        prompt = f"{restaurants_prompt}\n\nCurrent time: {current_time}\n{restaurants_context}\n\nUser: {user_message}\nAI:"

        # Generate response
        response = model.generate_content(prompt)
        html_response = markdown2.markdown(response.text)

        print(f"🍽️ Restaurant query handled: {user_message[:50]}...")

        return {'reply': html_response}

    except Exception as e:
        print(f"⚠️ Error handling restaurant query: {e}")
        return {'reply': 'Sorry, I encountered an error while searching for restaurants. Please try again.'}

def handle_announcement_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles announcement-related queries by reading directly from all_announcements.json
    (raw D2L scraper output - no transformation needed)
    """
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        # Load announcements data directly from scraper output
        announcements_path = Path('all_announcements.json')
        if not announcements_path.exists():
            return {'reply': 'Announcement information is currently unavailable. Please run extract_all_announcements.py to collect D2L announcements.'}

        with open(announcements_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        announcements = raw_data.get('announcements', [])

        if not announcements:
            return {'reply': 'No announcements found. Please run extract_all_announcements.py to collect D2L announcements.'}

        # Format announcements data as context
        from datetime import datetime

        announcements_context = "\n\n** Recent D2L Announcements: **\n"
        announcements_context += f"Course: {raw_data.get('course', 'Unknown')}\n"
        announcements_context += f"Total: {raw_data.get('total_announcements', 0)} announcements\n"
        announcements_context += f"Extracted: {raw_data.get('extracted_at', 'Unknown')}\n\n"

        for announcement in announcements:
            announcements_context += f"\n- **{announcement.get('title', 'Untitled')}**\n"
            announcements_context += f"  Posted: {announcement.get('date', 'Unknown date')}\n"

            # Limit content length for context
            content = announcement.get('content', '')
            if len(content) > 500:
                announcements_context += f"  Content: {content[:500]}...\n"
            else:
                announcements_context += f"  Content: {content}\n"

            if announcement.get('url'):
                announcements_context += f"  Link: {announcement['url']}\n"

        # Combine announcements prompt + context + user query
        prompt = f"{announcements_prompt}\n{announcements_context}\n\nUser: {user_message}\nAI:"

        # Generate response
        response = model.generate_content(prompt)
        html_response = markdown2.markdown(response.text)

        print(f"📢 Announcement query handled: {user_message[:50]}...")

        return {'reply': html_response}

    except Exception as e:
        print(f"⚠️ Error handling announcement query: {e}")
        import traceback
        traceback.print_exc()
        return {'reply': 'Sorry, I encountered an error while searching for announcements. Please try again.'}

def handle_out_of_scope_query(user_message: str) -> Dict[str, Any]:
    """
    Provides a standard response for queries outside the supported categories
    """
    fallback_message = """I'm Fanshawe Navigator, your campus assistant! I specialize in helping you with:

- 🗺️ **Navigation & Directions** - Finding your way around campus
- 📅 **Campus Events** - Discovering activities and schedules
- 🍽️ **Dining & Restaurants** - Locating food services on campus
- 📢 **Course Announcements** - D2L updates and class news

Your question seems to be outside these areas. For other assistance, please visit:
- **Student Services**: [www.fanshawec.ca/student-services](https://www.fanshawec.ca/student-services)
- **Academic Support**: Contact your program coordinator
- **General Inquiries**: Visit the Information Desk at the Student Centre

How else can I help you with navigation, events, dining, or announcements?"""

    html_response = markdown2.markdown(fallback_message)
    print(f"❌ Out-of-scope query: {user_message[:50]}...")

    return {'reply': html_response}

def parse_docx_event(docx_path: str) -> Dict[str, Any]:
    """
    Parse event information from a DOCX file
    Extracts text and uses Gemini to structure the event data

    Args:
        docx_path: Path to the DOCX file

    Returns:
        Dict with event information (name, date, time, location, description, etc.)
    """
    try:
        from docx import Document

        # Read the DOCX file
        doc = Document(docx_path)

        # Extract all text from paragraphs
        full_text = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])

        if not full_text.strip():
            return {'error': 'No text found in document'}

        # Use Gemini to extract structured event information
        if not model:
            return {'error': 'AI model not configured'}

        extract_prompt = f"""Extract event information from this text and return ONLY a JSON response with this format (no other text):

{{
    "name": "event name",
    "date": "YYYY-MM-DD format",
    "time": "event time",
    "location": "full location description",
    "building": "building code (e.g., SC, F, H)",
    "room": "room number",
    "organizer": "organizer name",
    "description": "event description",
    "link": "event link if available",
    "registration_required": true/false
}}

Event text:
{full_text}"""

        response = model.generate_content(extract_prompt)
        response_text = response.text.strip()

        # Extract JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            event_data = json.loads(json_match.group())
            print(f"📄 Parsed DOCX event: {event_data.get('name', 'Unknown')}")
            return event_data

        return {'error': 'Could not parse event information'}

    except ImportError:
        return {'error': 'python-docx library not installed. Run: pip install python-docx'}
    except Exception as e:
        print(f"⚠️ Error parsing DOCX: {e}")
        return {'error': str(e)}

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

@app.route('/LeafletJS/<path:path>')
def send_leaflet(path):
    return send_from_directory('LeafletJS', path)

@app.route('/tools/<path:path>')
def send_tools(path):
    return send_from_directory('tools', path)

@app.route('/map/<path:path>')
def send_map(path):
    return send_from_directory('map', path)

@app.route("/chat", methods=['POST'])
def chat():
    if model is None:
        return jsonify({"reply": "The AI model is not configured. Please set the GEMINI_API_KEY environment variable."}), 500

    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Please provide a message."}), 400

    try:
        # Step 1: Classify user intent
        intent_result = classify_user_intent(user_message)
        intent_type = intent_result['intent']

        print(f"🎯 Intent classified: {intent_type} (confidence: {intent_result['confidence']:.2f})")

        # Step 2: Route to appropriate handler based on intent
        if intent_type == "NAVIGATION":
            # Handle navigation queries
            nav_result = parse_navigation_request(user_message)

            # Get image context if available
            image_context = image_manager.get_image_context_for_prompt(user_message)

            # Combine map info + image context + user message
            if image_context:
                prompt = f'{map_info}{image_context}\n\nUser: {user_message}\nAI:'
                print(f"🔍 Using visual information for navigation: {user_message[:50]}...")
            else:
                prompt = f'{map_info}\n\nUser: {user_message}\nAI:'
                print(f"📝 Using only textual information for navigation: {user_message[:50]}...")

            # Generate a response from the AI model
            response = model.generate_content(prompt)

            # Convert Markdown to HTML
            html_response = markdown2.markdown(response.text)

            # If navigation request detected, include map action
            if nav_result.get('is_navigation'):
                print(f"🗺️ Navigation route: {nav_result['start']} → {nav_result['end']}")
                return jsonify({
                    "reply": html_response,
                    "mapAction": {
                        "type": "SHOW_ROUTE",
                        "building": "M",
                        "floor": 1,
                        "startRoom": nav_result['start'],
                        "endRoom": nav_result['end'],
                        "startNode": nav_result['startNode'],
                        "endNode": nav_result['endNode']
                    }
                })
            else:
                return jsonify({"reply": html_response})

        elif intent_type == "EVENTS":
            # Handle event queries
            result = handle_event_query(user_message, intent_result['entities'])
            return jsonify(result)

        elif intent_type == "RESTAURANTS":
            # Handle restaurant queries
            result = handle_restaurant_query(user_message, intent_result['entities'])
            return jsonify(result)

        elif intent_type == "ANNOUNCEMENTS":
            # Handle announcement queries
            result = handle_announcement_query(user_message, intent_result['entities'])
            return jsonify(result)

        else:  # OUT_OF_SCOPE
            # Handle out-of-scope queries with fallback message
            result = handle_out_of_scope_query(user_message)
            return jsonify(result)

    except Exception as e:
        print(f"⚠️ Error generating content: {e}")
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

# ============== ANNOUNCEMENTS API ENDPOINTS ==============

@app.route("/api/announcements/refresh", methods=['POST'])
def refresh_announcements():
    """
    Transform all_announcements.json to d2l_announcements.json cache.
    Note: You must run extract_all_announcements.py manually first.
    """
    try:
        # Check if raw scraper output exists
        raw_file = Path('all_announcements.json')
        if not raw_file.exists():
            return jsonify({
                "status": "error",
                "message": "all_announcements.json not found. Please run extract_all_announcements.py first."
            }), 404

        print("🔄 Transforming announcements from all_announcements.json...")

        # Load raw scraper output
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # Transform to standardized format
        from src.services.announcement_transformer import transform_announcements
        standardized = transform_announcements(raw_data)

        # Save to cache
        cache_path = Path('data/d2l_announcements.json')
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(standardized, f, indent=2, ensure_ascii=False)

        print(f"✅ Announcements transformed: {len(standardized['announcements'])} announcements")

        return jsonify({
            "status": "success",
            "message": f"Transformed {len(standardized['announcements'])} announcements",
            "last_updated": standardized['last_updated'],
            "total_announcements": len(standardized['announcements']),
            "source_file": str(raw_file)
        })

    except Exception as e:
        print(f"❌ Error transforming announcements: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/announcements/status", methods=['GET'])
def announcements_status():
    """Returns announcements data status (reads directly from all_announcements.json)"""
    try:
        announcements_path = Path('all_announcements.json')

        if not announcements_path.exists():
            return jsonify({
                "status": "no_data",
                "message": "No announcements found. Please run extract_all_announcements.py",
                "file_exists": False
            })

        with open(announcements_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        from datetime import datetime
        extracted_at = data.get('extracted_at', 'Unknown')

        # Calculate data age
        try:
            extracted_dt = datetime.fromisoformat(extracted_at)
            age_seconds = (datetime.now() - extracted_dt).total_seconds()
            age_hours = age_seconds / 3600
            age_str = f"{age_hours:.1f} hours ago"
        except:
            age_str = "Unknown"

        return jsonify({
            "status": "available",
            "file_exists": True,
            "total_announcements": data.get('total_announcements', 0),
            "successful": data.get('successful', 0),
            "failed": data.get('failed', 0),
            "extracted_at": extracted_at,
            "data_age": age_str,
            "course": data.get('course', 'Unknown'),
            "source_file": "all_announcements.json"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ============== PROFESSOR INFO API ENDPOINTS ==============

@app.route("/api/professor/<course_id>", methods=['GET'])
def get_professor_info(course_id):
    """
    Get cached professor information for a course.
    Returns professor data from data/course_{COURSE_ID}/professor_info.json
    """
    try:
        prof_file = Path(f'data/course_{course_id}/professor_info.json')
        
        if not prof_file.exists():
            return jsonify({
                "status": "not_found",
                "message": f"Professor info not found for course {course_id}. Run extract_professor_info.py first.",
                "course_id": course_id
            }), 404
        
        with open(prof_file, 'r', encoding='utf-8') as f:
            prof_data = json.load(f)
        
        # Calculate data age
        from datetime import datetime
        try:
            extracted_dt = datetime.fromisoformat(prof_data.get('extracted_at', ''))
            age_seconds = (datetime.now() - extracted_dt).total_seconds()
            age_days = age_seconds / 86400
            age_str = f"{age_days:.1f} days ago"
        except:
            age_str = "Unknown"
        
        return jsonify({
            "status": "success",
            "course_id": course_id,
            "professor": {
                "name": prof_data.get('name'),
                "email": prof_data.get('email'),
                "office": prof_data.get('office'),
                "office_hours": prof_data.get('office_hours')
            },
            "metadata": {
                "extracted_at": prof_data.get('extracted_at'),
                "data_age": age_str,
                "extraction_method": prof_data.get('extraction_method'),
                "source_url": prof_data.get('source_url')
            }
        })
    
    except Exception as e:
        print(f"❌ Error getting professor info: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/professor/status", methods=['GET'])
def professor_info_status():
    """
    Returns status of all cached professor information.
    Lists all courses with professor data available.
    """
    try:
        data_dir = Path('data')
        professor_files = list(data_dir.glob('course_*/professor_info.json'))
        
        courses = []
        for prof_file in professor_files:
            try:
                with open(prof_file, 'r', encoding='utf-8') as f:
                    prof_data = json.load(f)
                
                course_id = prof_data.get('course_id')
                
                # Calculate data age
                from datetime import datetime
                try:
                    extracted_dt = datetime.fromisoformat(prof_data.get('extracted_at', ''))
                    age_seconds = (datetime.now() - extracted_dt).total_seconds()
                    age_days = age_seconds / 86400
                    age_str = f"{age_days:.1f} days ago"
                except:
                    age_str = "Unknown"
                
                courses.append({
                    "course_id": course_id,
                    "name": prof_data.get('name'),
                    "email": prof_data.get('email'),
                    "extracted_at": prof_data.get('extracted_at'),
                    "data_age": age_str,
                    "has_name": prof_data.get('name') is not None,
                    "has_email": prof_data.get('email') is not None
                })
            except Exception as e:
                print(f"⚠️ Error reading {prof_file}: {e}")
                continue
        
        return jsonify({
            "status": "success",
            "total_courses": len(courses),
            "courses": courses
        })
    
    except Exception as e:
        print(f"❌ Error getting professor status: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ============== NAVIGATION API ENDPOINTS ==============

@app.route("/api/navigation/parse", methods=['POST'])
def api_parse_navigation():
    """Parse navigation request from user message"""
    data = request.json
    if not data or not data.get('message'):
        return jsonify({"error": "message required"}), 400

    result = parse_navigation_request(data['message'])
    return jsonify(result)

@app.route("/api/navigation/from-clicks", methods=['POST'])
def api_navigation_from_clicks():
    """
    Handle navigation request from map clicks
    Receives: {startRoom, endRoom, building, floor}
    Returns: {reply, path}
    """
    if model is None:
        return jsonify({"error": "AI model not configured"}), 500

    try:
        data = request.json
        if not data or not data.get('startRoom') or not data.get('endRoom'):
            return jsonify({"error": "startRoom and endRoom required"}), 400

        start_room = data.get('startRoom')
        end_room = data.get('endRoom')

        # Get friendly names
        start_friendly = get_room_friendly_name(start_room)
        end_friendly = get_room_friendly_name(end_room)

        # Create navigation message for Gemini
        nav_message = f"Give me walking directions from {start_friendly} to {end_friendly} in Building M Floor 1."

        # Parse to get path nodes (optional, for reference)
        room_to_node = building_m_config.get('roomToNode', {})
        start_node = room_to_node.get(start_room)
        end_node = room_to_node.get(end_room)

        # Get image context if available
        image_context = image_manager.get_image_context_for_prompt(nav_message)

        # Generate response from Gemini
        if image_context:
            prompt = f'{map_info}{image_context}\n\nUser: {nav_message}\nAI:'
            print(f"🔍 Using visual information for navigation...")
        else:
            prompt = f'{map_info}\n\nUser: {nav_message}\nAI:'
            print(f"📝 Using textual information for navigation...")

        response = model.generate_content(prompt)
        html_response = markdown2.markdown(response.text)

        return jsonify({
            "reply": html_response,
            "startRoom": start_room,
            "endRoom": end_room,
            "startNode": start_node,
            "endNode": end_node
        })

    except Exception as e:
        print(f"Error in navigation from clicks: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/navigation/rooms", methods=['GET'])
def api_get_rooms():
    """Get list of all rooms in Building M with descriptions"""
    if not building_m_config:
        return jsonify({"error": "Building M configuration not loaded"}), 500

    rooms_data = {}
    room_to_node = building_m_config.get('roomToNode', {})
    descriptions = building_m_config.get('roomDescriptions', {})

    for room_id, node_id in room_to_node.items():
        rooms_data[room_id] = {
            "node": node_id,
            "description": descriptions.get(room_id, room_id)
        }

    return jsonify(rooms_data)

@app.route("/api/navigation/room-centers", methods=['GET'])
def api_get_room_centers():
    """Get manual room center coordinates for Building M"""
    if not building_m_config:
        return jsonify({"error": "Building M configuration not loaded"}), 500

    room_centers = building_m_config.get('roomCentersSVG', {})

    # Filter out comment fields
    filtered_centers = {k: v for k, v in room_centers.items() if not k.startswith('_')}

    return jsonify(filtered_centers)

@app.route("/api/navigation/room-centers/reload", methods=['POST'])
def reload_room_centers():
    """Reload room centers from config file without restarting server"""
    global building_m_config
    try:
        config_path = Path('config/building_m_rooms.json')
        with open(config_path, 'r') as f:
            building_m_config = json.load(f)['Building M']

        room_count = len(building_m_config.get('roomCentersSVG', {}))
        print(f"✅ Room centers reloaded: {room_count} coordinates loaded")

        return jsonify({
            "status": "success",
            "message": "Room centers reloaded successfully",
            "room_count": room_count
        })
    except Exception as e:
        print(f"❌ Error reloading room centers: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/navigation/room-centers/update", methods=['POST'])
def update_room_centers():
    """Update room center coordinates in the configuration file"""
    global building_m_config
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        # Validate coordinate bounds (safe SVG space with padding)
        MIN_COORD = -1000
        MAX_COORD = 2000
        invalid_rooms = []

        for room_id, coords in data.items():
            if not isinstance(coords, dict) or 'x' not in coords or 'y' not in coords:
                invalid_rooms.append(f"{room_id}: Invalid format")
                continue

            x = coords.get('x')
            y = coords.get('y')

            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                invalid_rooms.append(f"{room_id}: Coordinates must be numbers")
                continue

            if not (MIN_COORD <= x <= MAX_COORD and MIN_COORD <= y <= MAX_COORD):
                invalid_rooms.append(f"{room_id}: Out of bounds ({x}, {y})")
                continue

        # If there are validation errors, return them
        if invalid_rooms:
            return jsonify({
                "status": "error",
                "message": "Validation failed",
                "invalid_rooms": invalid_rooms
            }), 400

        # Update in-memory config
        if 'roomCentersSVG' not in building_m_config:
            building_m_config['roomCentersSVG'] = {}

        for room_id, coords in data.items():
            building_m_config['roomCentersSVG'][room_id] = {
                'x': coords['x'],
                'y': coords['y']
            }

        # Write to file
        config_path = Path('config/building_m_rooms.json')
        with open(config_path, 'r') as f:
            full_config = json.load(f)

        full_config['Building M']['roomCentersSVG'].update(data)

        with open(config_path, 'w') as f:
            json.dump(full_config, f, indent=2)

        updated_count = len(data)
        print(f"✅ Updated {updated_count} room coordinates successfully")

        return jsonify({
            "status": "success",
            "message": f"Updated {updated_count} room coordinates",
            "updated_count": updated_count
        })

    except Exception as e:
        print(f"❌ Error updating room centers: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def main():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081)))


if __name__ == "__main__":
    main()
