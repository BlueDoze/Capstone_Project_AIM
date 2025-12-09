import os
import sys
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import re
import uuid
from datetime import datetime, timedelta
import threading
import time

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import local modules
from src.api.utils.text_cleaner import clean_html_to_text
from src.services.navigation_service import get_navigation_service
from src.services.direction_service import get_direction_service
from src.config.paths import ANNOUNCEMENTS_FILE, ANNOUNCEMENTS_DIR

load_dotenv()

# Global emoji dictionary for chatbot responses
CHATBOT_EMOJIS = {
    # Navigation & Location
    'navigation': '🗺️',
    'location': '📍',
    'building': '🏢',
    'direction': '➡️',
    'stairs': '🪜',
    'elevator': '🛗',
    
    # Calendar & Time
    'calendar': '📅',
    'deadline': '⏰',
    'urgent': '⚠️',
    'date': '📆',
    'time': '🕐',
    'reminder': '🔔',
    
    # Academic & Grades
    'grades': '📊',
    'success': '✅',
    'achievement': '🎯',
    'feedback': '💬',
    'progress': '📈',
    'warning': '⚠️',
    'excellent': '⭐',
    
    # Events & Activities
    'event': '🎉',
    'workshop': '🎓',
    'meeting': '👥',
    'registration': '📝',
    
    # Food & Dining
    'food': '🍽️',
    'restaurant': '🍴',
    'cafe': '☕',
    'menu': '📋',
    
    # Information & Help
    'announcement': '📢',
    'news': '📰',
    'info': 'ℹ️',
    'tip': '💡',
    'help': '❓',
    'link': '🔗',
    
    # Career Services
    'career': '💼',
    'job': '👔',
    'resume': '📄',
    'interview': '🤝',
    'mentor': '👨‍🏫',
    
    # General
    'highlight': '🧠',
    'next_step': '▶️',
    'check': '✓',
    'important': '❗'
}

# Configure Flask to serve React build from frontend/dist
react_build_dir = project_root / 'Frontend_Data' / 'frontend' / 'dist'

app = Flask(__name__,
            static_folder=str(react_build_dir),
            static_url_path='')

# Load Building M room configuration
try:
    config_path = Path('config/building_m_rooms.json')
    with open(config_path, 'r') as f:
        building_m_config = json.load(f)['Building M']
    print("✅ Building M room configuration loaded")
except Exception as e:
    print(f"⚠️ Failed to load room configuration: {e}")
    building_m_config = {}

# Configure the generative AI client and model
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise KeyError("GEMINI_API_KEY environment variable not set.")
    
    # Configure standard genai with API key for all operations
    genai.configure(api_key=api_key)
    
    # Configure generation settings
    generation_config = genai.types.GenerationConfig(
        temperature=0.3,
        max_output_tokens=2048,
        top_p=0.95,
        top_k=40
    )
    
    # Configure safety settings to allow campus navigation queries
    # These settings prevent blocking of legitimate queries containing words like "bathroom", "room", etc.
    safety_settings = {
        genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
    }
    
    # Create model for chat operations
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    print("✅ Gemini AI model configured with safety settings")
except KeyError as e:
    print(f"❌ {e}")
    model = None

# Session storage and cache management
sessions = {}  # {session_id: {"messages": [], "archived_messages": [], "created_at": datetime, "last_accessed": datetime}}
session_lock = threading.Lock()

# Building info cache
building_info_data = None

# ============== SESSION CACHE MANAGER ==============

class SessionCacheManager:
    """Manages session-based conversation caching with 10-message limit"""
    
    MAX_ACTIVE_MESSAGES = 10
    SESSION_TTL_HOURS = 24
    ARCHIVE_DIR = project_root / 'data' / 'sessions'
    
    def __init__(self):
        self.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    def create_session(self) -> str:
        """Create a new session with unique ID"""
        session_id = str(uuid.uuid4())
        with session_lock:
            sessions[session_id] = {
                "messages": [],
                "archived_messages": [],
                "created_at": datetime.now(),
                "last_accessed": datetime.now()
            }
        print(f"📝 Created session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data, create if doesn't exist"""
        with session_lock:
            if session_id not in sessions:
                # Try to load from archive
                self._load_session_from_archive(session_id)
            
            if session_id in sessions:
                sessions[session_id]["last_accessed"] = datetime.now()
                return sessions[session_id]
        
        return None
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add message to session, archive if limit exceeded"""
        with session_lock:
            if session_id not in sessions:
                sessions[session_id] = {
                    "messages": [],
                    "archived_messages": [],
                    "created_at": datetime.now(),
                    "last_accessed": datetime.now()
                }
            
            session = sessions[session_id]
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
            session["messages"].append(message)
            
            # If exceeded limit, archive oldest pair (user + assistant)
            if len(session["messages"]) > self.MAX_ACTIVE_MESSAGES:
                archived = session["messages"][:2]  # Remove oldest 2 messages
                session["messages"] = session["messages"][2:]
                session["archived_messages"].extend(archived)
                
                # Save archived messages to disk
                self._save_archived_messages(session_id, session["archived_messages"])
                print(f"📦 Archived 2 messages for session {session_id[:8]}... (total archived: {len(session['archived_messages'])})")
    
    def get_active_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get active messages (last 10) for session"""
        session = self.get_session(session_id)
        if session:
            return session["messages"]
        return []
    
    def get_message_count(self, session_id: str) -> Dict[str, int]:
        """Get message counts for session"""
        session = self.get_session(session_id)
        if session:
            return {
                "active": len(session["messages"]),
                "archived": len(session["archived_messages"]),
                "total": len(session["messages"]) + len(session["archived_messages"])
            }
        return {"active": 0, "archived": 0, "total": 0}
    
    def clear_session(self, session_id: str, keep_archive: bool = True):
        """Clear session messages"""
        with session_lock:
            if session_id in sessions:
                if not keep_archive:
                    sessions[session_id]["archived_messages"] = []
                    # Delete archive file
                    archive_file = self.ARCHIVE_DIR / f"{session_id}_archive.json"
                    if archive_file.exists():
                        archive_file.unlink()
                sessions[session_id]["messages"] = []
                print(f"🗑️ Cleared session {session_id[:8]}...")
    
    def _save_archived_messages(self, session_id: str, archived_messages: List[Dict[str, str]]):
        """Save archived messages to disk"""
        try:
            archive_file = self.ARCHIVE_DIR / f"{session_id}_archive.json"
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "session_id": session_id,
                    "archived_at": datetime.now().isoformat(),
                    "message_count": len(archived_messages),
                    "messages": archived_messages
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving archived messages: {e}")
    
    def _load_session_from_archive(self, session_id: str):
        """Load session from archive file"""
        try:
            archive_file = self.ARCHIVE_DIR / f"{session_id}_archive.json"
            if archive_file.exists():
                with open(archive_file, 'r', encoding='utf-8') as f:
                    archive_data = json.load(f)
                sessions[session_id] = {
                    "messages": [],
                    "archived_messages": archive_data.get("messages", []),
                    "created_at": datetime.now(),
                    "last_accessed": datetime.now()
                }
                print(f"📂 Loaded session {session_id[:8]}... from archive")
        except Exception as e:
            print(f"⚠️ Error loading session from archive: {e}")
    
    def cleanup_expired_sessions(self):
        """Remove sessions older than TTL"""
        with session_lock:
            now = datetime.now()
            expired = []
            for session_id, session in sessions.items():
                if (now - session["last_accessed"]).total_seconds() > (self.SESSION_TTL_HOURS * 3600):
                    expired.append(session_id)
            
            for session_id in expired:
                del sessions[session_id]
                print(f"🧹 Cleaned up expired session: {session_id[:8]}...")
            
            return len(expired)

# Initialize session manager
session_manager = SessionCacheManager()

# Background cleanup task
def cleanup_sessions_task():
    """Background task to cleanup expired sessions"""
    while True:
        time.sleep(3600)  # Run every hour
        try:
            session_manager.cleanup_expired_sessions()
        except Exception as e:
            print(f"⚠️ Error in cleanup task: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_sessions_task, daemon=True)
cleanup_thread.start()

# ============== HELPER FUNCTIONS ==============

def safe_get_response_text(response, default_message="I apologize, but I couldn't generate a proper response. Please try rephrasing your question."):
    """
    Safely extract text from Gemini API response, handling various error cases.
    """
    try:
        return response.text
    except ValueError as e:
        print(f"⚠️ Gemini response error: {e}")
        
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            finish_reason = getattr(candidate, 'finish_reason', None)
            print(f"   Finish reason: {finish_reason}")
            
            if finish_reason == 2:  # SAFETY
                return "I apologize, but I couldn't generate a response due to content safety policies. Please rephrase your question."
            elif finish_reason == 3:  # RECITATION
                return "I apologize, but I couldn't generate an original response. Please try asking in a different way."
        
        return default_message
    except Exception as e:
        print(f"⚠️ Unexpected error extracting response text: {e}")
        return default_message

# ============== AI PROMPTS ==============

map_info = '''You are the Fanshawe Navigator for the Campus. Provide step-by-step walking directions based on the information you have.

You will provide directions in a clear and concise manner. Tell the user putting yourself in the map's perspective where to go. 

#Invert the instructions about right and left, e.g "turn right" becomes "turn left" and vice versa.

Provide easy instructions like "turn left", "turn right", "go straight", "take the stairs", "take the elevator", etc.

Suggest the best route to take, which means the shortest one, mentioning landmarks or notable features along the way to help with navigation.

** Some detailed information about the campus layout: **
        - Where you have for example 1063-C it means that is a corridor near room 1063.
        - Corridors are marked with blue color path, the user must walk through these blue paths to get into destination.
        - -3, -2, -1 indicate inner space inside a room or area and it must not be considered for walking directions.
        - The chatbot will get information about the building, for example: A Building First Floor, and it must use that to give directions.

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

events_prompt = '''You are the Fanshawe Events Assistant. You help students discover campus events, activities, and schedules.

You have access to information about campus events including:
- Event names, dates, and times
- Event locations (buildings and rooms)
- Event descriptions and organizers
- Registration requirements
- Links to more information

When answering about events:
- Use emojis for visual appeal: 🎉 for events sections, 📅 for dates, 📍 for locations, 📝 for registration requirements, 🔗 for links
- Provide clear, concise information about the events
- Include relevant details like date, time, location, and organizer
- If multiple events match the query, list them clearly with emoji headers
- Suggest relevant events based on the user's interests
- If an event requires registration, mention it with 📝
- Include links when available with 🔗
- Format with clear section headers using emojis

Be helpful, friendly, and enthusiastic about campus events!
'''

restaurants_prompt = '''You are the Fanshawe Dining Guide. You help students find food and dining options on campus.

You have access to information about campus dining including:
- Restaurant and cafe names and locations
- Operating hours for each day
- Cuisine types and menu highlights
- Payment methods accepted
- Building and floor locations

When answering about dining:
- Use emojis for visual appeal: 🍽️ for dining sections, ☕ for cafes, 📋 for menus, 🕐 for hours, 📍 for locations
- Provide clear information about location and hours
- Mention what type of food is available
- Include operating hours, especially for today
- Suggest options based on the user's needs (quick snack, full meal, coffee, etc.)
- Mention payment methods if relevant
- Be aware of current day/time when suggesting options
- Format with clear section headers using emojis

Be helpful, friendly, and make it easy for students to find what they're looking for!
'''

announcements_prompt = '''You are the Fanshawe Announcements Assistant. You help students stay informed about course announcements and important updates from D2L.

You have access to information about:
- Recent course announcements from instructors
- Important class updates and reminders
- Assignment and exam notifications
- Course-related news and changes
- Posted dates and content of announcements

When answering about announcements:
- Use emojis for visual appeal: 📢 for announcements header, 📆 for dates, ⚠️ for urgent items, 💡 for action items, 🔗 for links
- Provide clear, concise summaries of announcements
- Include dates when announcements were posted
- Highlight action items (deadlines, required attendance, submissions, etc.) with appropriate emojis
- Prioritize recent and urgent announcements
- Mention the instructor or source when relevant
- If multiple announcements match, list them chronologically (most recent first)
- Be aware of deadlines and time-sensitive information
- Format with clear section headers using emojis

Be helpful, organized, and ensure students don't miss important information!
'''

career_services_prompt = '''You are the Fanshawe Career Services Assistant. You help students access career development resources, job search support, and professional development opportunities.

You have access to information about:
- Career Services portal and online resources
- Resume and cover letter assistance
- Interview preparation and mock interviews
- Job search strategies and employer connections
- Co-op and internship support
- Career counseling and guidance
- Mentorship programs (industry and peer)
- Career workshops and events
- Professional headshot services
- Career fairs and networking opportunities

When answering about Career Services:
- Provide direct links to the main Career Services portal and specific resources
- Explain what services are available (workshops, one-on-one appointments, etc.)
- Mention relevant programs like mentorship opportunities
- Include information about upcoming events when relevant
- Be encouraging and supportive about career development
- Suggest specific next steps (visit portal, book appointment, attend workshop)

Be helpful, professional, and empower students to take charge of their career development!
'''

building_info_prompt = '''You are the Fanshawe Building Information Assistant. You help students learn about campus buildings, facilities, and structures.

You have access to information about:
- Building names, codes, and locations
- Building descriptions and purposes
- Facilities and departments housed in each building
- Accessibility features
- Operating hours and general information
- Special features or notable areas in buildings

When answering about buildings:
- Use emojis for visual appeal: 🏢 for building headers, 📍 for locations, 🚪 for entrances, ♿ for accessibility, 🕐 for hours, ℹ️ for info
- Provide clear, informative descriptions of buildings
- Mention key departments or facilities within the building
- Include accessibility information when relevant
- Highlight any unique features or services
- If asked about multiple buildings, organize information clearly with headers
- Format with clear section headers using emojis
- Be descriptive about building layout and what students can find there

Note: This is for general building information, not navigation directions. For wayfinding, that's a separate NAVIGATION intent.

Be helpful, informative, and help students understand the campus infrastructure!
data/courses_info/courses_summary.json'''

courses_prompt = '''You are the Fanshawe Courses Assistant. You help students get information about their enrolled courses.

You have access to information about:
- Course titles and codes
- Course widgets (Announcements, Calendar, Professor Information, Updates)
- Important links (Content, Profile, Notifications, Account Settings)
- Recent announcements from instructors
- Calendar events and deadlines
- Course content overview

When answering about courses:
- Use emojis for visual appeal: 📚 for courses, 👨‍🏫 for professors, 📢 for announcements, 📅 for calendar, 🔗 for links, 📝 for content
- Provide clear, organized information about the requested courses
- List course titles with their codes when showing multiple courses
- Highlight important announcements or upcoming deadlines
- Include relevant links when appropriate
- Format with clear section headers using emojis
- Be specific about which course information belongs to

Be helpful, organized, and make it easy for students to find their course information!
'''

# ============== NAVIGATION HELPER FUNCTIONS ==============

def resolve_room_name(room_name: str) -> Optional[str]:
    """
    Resolve a user-provided room name to the official room ID
    Handles aliases like "1003", "bathroom men", etc.
    """
    if not building_m_config:
        return None

    normalized = room_name.lower().strip()
    aliases = building_m_config.get('aliases', {})
    
    if normalized in aliases:
        return aliases[normalized]

    room_to_node = building_m_config.get('roomToNode', {})
    if room_name in room_to_node:
        return room_name

    return None

def parse_navigation_request(user_message: str, user_position: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Parse navigation request from user message
    Uses Gemini to extract start and end locations with building/floor info
    
    Args:
        user_message: User's navigation query
        user_position: Optional dict with {"lat": float, "lng": float, "floor": str, "building": str}
    """
    print(f"\n🔍 PARSING NAVIGATION REQUEST: '{user_message}'")
    
    if not model:
        print("❌ Model not initialized")
        return {'is_navigation': False}

    nav_keywords = ['how', 'get', 'go', 'navigate', 'path', 'way', 'direction',
                    'from', 'to', 'reach', 'find', 'como', 'ir', 'chegar', 'where']
    message_lower = user_message.lower()
    is_likely_nav = any(keyword in message_lower for keyword in nav_keywords)

    if not is_likely_nav:
        print(f"❌ No navigation keywords found in: {message_lower}")
        return {'is_navigation': False}
    
    print(f"✅ Detected navigation keywords")

    try:
        nav_service = get_navigation_service()
        use_gps_start = False
        start_location = None
        start_node = None
        start_building = 'M'
        start_floor = '1'
        
        # If user position is provided, use it as start point
        if user_position and user_position.get('lat') and user_position.get('lng'):
            print(f"📍 User position provided: {user_position}")
            # Find nearest node to GPS position
            user_building = user_position.get('building', 'M')
            user_floor = str(user_position.get('floor', '1'))
            
            # Get navigation graph for user's building/floor
            nav_data = nav_service.navigation_data.get(user_building, {})
            floor_data = nav_data.get('floors', {}).get(user_floor, {})
            nodes = floor_data.get('nodes', {})
            
            # Find nearest node to user position
            nearest_node = None
            min_distance = float('inf')
            
            for node_id, node_data in nodes.items():
                node_pos = node_data.get('position')
                if node_pos and len(node_pos) >= 2:
                    # Calculate simple distance (could use haversine for accuracy)
                    dist = ((node_pos[0] - user_position['lat'])**2 + 
                           (node_pos[1] - user_position['lng'])**2)**0.5
                    if dist < min_distance:
                        min_distance = dist
                        nearest_node = node_id
            
            if nearest_node:
                print(f"✅ Using GPS position - nearest node: {nearest_node}")
                start_location = "your current location"
                start_node = nearest_node
                start_building = user_building
                start_floor = user_floor
                use_gps_start = True
            else:
                print(f"⚠️ Could not find nearest node to GPS position")
        
        # PATTERN-BASED PARSING: Try to extract locations directly using regex
        # This bypasses AI content safety issues for simple queries
        room_number_pattern = r'\b(\d{4})\b'  # Match 4-digit room numbers
        building_pattern = r'building\s+([A-Z])\b'  # Match "building M", "building H", etc.
        floor_pattern = r'floor\s+(\d+)\b'  # Match "floor 1", "floor 2", etc.
        
        # Match common location keywords
        location_keywords = r'\b(bathroom|restroom|washroom|toilet|elevator|lift|stairs|stairwell|staircase|exit|entrance|lobby)\b'
        keyword_match = re.search(location_keywords, user_message, re.IGNORECASE)
        
        room_matches = re.findall(room_number_pattern, user_message)
        building_match = re.search(building_pattern, user_message, re.IGNORECASE)
        floor_match = re.search(floor_pattern, user_message, re.IGNORECASE)
        
        # Extract building and floor with defaults
        default_building = 'M'
        default_floor = '1'
        target_building = building_match.group(1).upper() if building_match else default_building
        target_floor = floor_match.group(1) if floor_match else default_floor
        
        # Determine destination location from patterns
        destination_found = False
        end_location = None
        end_node = None
        
        # Priority 1: Room number pattern
        if len(room_matches) == 1:
            room_number = room_matches[0]
            print(f"🔍 Pattern match found: Room {room_number} in Building {target_building}, Floor {target_floor}")
            
            # Resolve room to node using building_m_rooms.json aliases
            end_location = room_number
            end_node = nav_service.resolve_room_to_node(
                target_building, target_floor, room_number
            )
            
            # Try with "Room_" prefix if direct match fails
            if not end_node:
                end_node = nav_service.resolve_room_to_node(
                    target_building, target_floor, f"Room_{room_number}"
                )
                if end_node:
                    end_location = f"Room_{room_number}"
            
            # Check if it's a direct node ID
            if not end_node:
                node_info = nav_service.get_node_info(target_building, target_floor, room_number)
                if node_info:
                    end_node = room_number
                    end_location = room_number
            
            if end_node:
                destination_found = True
                print(f"🔍 Room number pattern matched: {end_location} -> {end_node}")
        
        # Priority 2: Location keyword pattern (bathroom, elevator, etc.)
        if not destination_found and keyword_match:
            keyword = keyword_match.group(1).lower()
            print(f"🔍 Location keyword found: {keyword}")
            
            # Map keywords to room aliases based on common naming patterns
            keyword_mappings = {
                'bathroom': ['Bathroom-Men', 'Bathroom-Women', 'Bathroom'],
                'restroom': ['Bathroom-Men', 'Bathroom-Women', 'Bathroom'],
                'washroom': ['Bathroom-Men', 'Bathroom-Women', 'Bathroom'],
                'toilet': ['Bathroom-Men', 'Bathroom-Women', 'Bathroom'],
                'elevator': ['Elevator-M', 'Elevator'],
                'lift': ['Elevator-M', 'Elevator'],
                'stairs': ['Stairs', 'Stairwell'],
                'stairwell': ['Stairs', 'Stairwell'],
                'staircase': ['Stairs', 'Stairwell'],
                'exit': ['Exit', 'Main-Exit'],
                'entrance': ['Entrance', 'Main-Entrance'],
                'lobby': ['Lobby', 'Main-Lobby']
            }
            
            # Check for gender-specific bathroom terms
            if keyword in ['bathroom', 'restroom', 'washroom', 'toilet']:
                if re.search(r"\b(men|men's|male|boys?)\b", user_message, re.IGNORECASE):
                    keyword_mappings[keyword] = ['Bathroom-Men']
                elif re.search(r"\b(women|women's|female|girls?|ladies)\b", user_message, re.IGNORECASE):
                    keyword_mappings[keyword] = ['Bathroom-Women']
            
            # Try to resolve keyword to a node
            possible_rooms = keyword_mappings.get(keyword, [keyword.title()])
            for room_name in possible_rooms:
                end_node = nav_service.resolve_room_to_node(target_building, target_floor, room_name)
                if end_node:
                    end_location = room_name
                    destination_found = True
                    print(f"✅ Keyword matched to room: {room_name} -> {end_node}")
                    break
        
        # If pattern matching found destination
        if destination_found and end_node:
            # If using GPS start, we already have start info
            if use_gps_start:
                return {
                    'is_navigation': True,
                    'start': {
                        'location': start_location,
                        'building': start_building,
                        'floor': start_floor,
                        'node': start_node,
                        'from_gps': True
                    },
                    'end': {
                        'location': end_location,
                        'building': target_building,
                        'floor': target_floor,
                        'node': end_node
                    }
                }
            else:
                # Pattern matched destination but no GPS start - fall through to AI for start location
                print(f"✅ Destination found via pattern matching: {end_location} -> {end_node}")
                # Will use AI below to extract start location
        
        # If pattern matching didn't work or we need start location, use AI
        print(f"🤖 Pattern matching incomplete, using AI to parse navigation request")
        
        parse_prompt = f"""You are parsing a campus navigation request. Extract the start and destination locations.
        Return ONLY valid JSON (no markdown, no explanation, no code blocks):
        {{
            "is_navigation": true,
            "start": {{
                "location": "Main Entrance",
                "building": "M",
                "floor": "1"
            }},
            "end": {{
                "location": "room number or name",
                "building": "M or H or A or B or F",
                "floor": "1 or 2 or 3"
            }}
        }}

        User message: {user_message}

        IMPORTANT:
        - For room numbers, use format like "M1003" (building + 4 digits)
        - Default building is M if not specified
        - Default floor is the first digit of the room number
        - If no start location is mentioned, use "Main Entrance" in Building M, Floor 1
        - Always set is_navigation to true for navigation requests
        - Return ONLY the JSON, no markdown formatting
        
        Example: "How do I get to room 1018?" → {{"is_navigation": true, "start": {{"location": "Main Entrance", "building": "M", "floor": "1"}}, "end": {{"location": "M1018", "building": "M", "floor": "1"}}}}"""

        try:
            response = model.generate_content(parse_prompt)
            response_text = safe_get_response_text(response, "{}").strip()
            print(f"🤖 AI Response: {response_text[:200]}...")
            
            # Check if response was blocked by safety filter
            if "content safety policies" in response_text or response_text == "{}":
                print("⚠️ AI response blocked by safety filter, attempting pattern-based fallback")
                # If we have any pattern-matched destination, use it with default start
                if destination_found and end_node:
                    print(f"✅ Using pattern-matched destination with default start location")
                    return {
                        'is_navigation': True,
                        'start': {
                            'location': 'Main Entrance',
                            'building': 'M',
                            'floor': '1',
                            'node': 'M1_1'
                        },
                        'end': {
                            'location': end_location,
                            'building': target_building,
                            'floor': target_floor,
                            'node': end_node
                        }
                    }
                else:
                    print("❌ Safety filter triggered with no pattern match")
                    return {'is_navigation': False, 'error': 'safety_filter', 'message': user_message}
        except Exception as e:
            print(f"❌ Error calling Gemini API: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to pattern matching if available
            if destination_found and end_node:
                print(f"✅ Falling back to pattern match result")
                return {
                    'is_navigation': True,
                    'start': {'location': 'Main Entrance', 'building': 'M', 'floor': '1', 'node': 'M1_1'},
                    'end': {'location': end_location, 'building': target_building, 'floor': target_floor, 'node': end_node}
                }
            print(f"❌ No fallback available, returning is_navigation=False")
            return {'is_navigation': False}
        
        response_text = response_text.strip()
        # Remove markdown code blocks if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        response_text = response_text.strip()

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                print(f"✅ Parsed JSON: {json.dumps(parsed, indent=2)}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"Raw text: {json_match.group()[:200]}")
                return {'is_navigation': False}

            if parsed.get('is_navigation'):
                # Handle start location
                if use_gps_start:
                    print(f"✅ Using GPS start location")
                    # Already set from GPS position
                    pass
                else:
                    start_data = parsed.get('start', {})
                    start_building = start_data.get('building', 'M')
                    start_floor = str(start_data.get('floor', '1'))
                    start_location = start_data.get('location', 'Main Entrance')
                    
                    if not start_location:
                        print(f"⚠️ No start location in AI response, using default")
                        start_location = 'Main Entrance'
                    
                    print(f"🔍 Resolving start location: {start_location} in {start_building}/{start_floor}")
                    # Resolve start location to node
                    start_node = nav_service.resolve_room_to_node(
                        start_building, start_floor, start_location
                    )
                    
                    if not start_node:
                        print(f"⚠️ Could not resolve start location, trying node info lookup")
                        node_info = nav_service.get_node_info(start_building, start_floor, start_location)
                        if node_info:
                            start_node = start_location
                            print(f"✅ Found node via get_node_info: {start_node}")
                    
                    if not start_node:
                        print(f"⚠️ Using default start node M1_1")
                        start_node = 'M1_1'
                        start_location = 'Main Entrance'
                
                # Handle end location
                end_data = parsed.get('end', {})
                end_building = end_data.get('building', 'M')
                end_floor = str(end_data.get('floor', '1'))
                end_location = end_data.get('location')
                
                if not end_location:
                    print(f"❌ No end location in AI response")
                    return {'is_navigation': False}
                
                print(f"🔍 Resolving end location: {end_location} in {end_building}/{end_floor}")
                # Resolve end location to node
                end_node = nav_service.resolve_room_to_node(
                    end_building, end_floor, end_location
                )
                
                if not end_node:
                    print(f"⚠️ Could not resolve end location, trying node info lookup")
                    node_info = nav_service.get_node_info(end_building, end_floor, end_location)
                    if node_info:
                        end_node = end_location
                        print(f"✅ Found node via get_node_info: {end_node}")
                
                if end_node:
                    print(f"✅ NAVIGATION REQUEST SUCCESSFUL")
                    print(f"   Start: {start_location} ({start_building}/{start_floor}) → {start_node}")
                    print(f"   End: {end_location} ({end_building}/{end_floor}) → {end_node}")
                    return {
                        'is_navigation': True,
                        'start': {
                            'location': start_location,
                            'building': start_building,
                            'floor': start_floor,
                            'node': start_node,
                            'from_gps': use_gps_start
                        },
                        'end': {
                            'location': end_location,
                            'building': end_building,
                            'floor': end_floor,
                            'node': end_node
                        }
                    }
                else:
                    print(f"❌ Could not resolve end location to node: {end_location}")
            else:
                print(f"❌ AI returned is_navigation=False")
        else:
            print(f"❌ No JSON found in AI response")

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
    Classifies user intent using AI-only classification with Gemini.
    Categories: NAVIGATION, EVENTS, RESTAURANTS, ANNOUNCEMENTS, CAREER_SERVICES, OUT_OF_SCOPE
    """
    if not model:
        return {'intent': 'OUT_OF_SCOPE', 'confidence': 0.0, 'entities': {}}

    try:
        # AI-only classification using Gemini
        classify_prompt = f"""Classify this user query into ONE of these categories:
        - NAVIGATION: Questions about directions, finding locations, wayfinding, how to get somewhere on campus
        - BUILDING_INFO: Questions about building information, what's inside buildings, building facilities, structure, departments in buildings (NOT directions)
        - EVENTS: Questions about campus events, activities, schedules, workshops
        - RESTAURANTS: Questions about food, dining, cafeterias, restaurants on campus
        - ANNOUNCEMENTS: Questions about course announcements, D2L news, class updates, reminders
        - COURSES: Questions about course information, what courses student is enrolled in, course titles, course codes (NOT about assignments or deadlines)
        - CAREER_SERVICES: Questions about career services, job search, resumes, interviews
        - CALENDAR: Questions about academic calendar, important dates, deadlines, assignments to submit, reports to submit, when things are due
        - GRADES: Questions about grades, assessments, evaluations
        - OUT_OF_SCOPE: Anything else not related to the above categories

        Examples to help distinguish CALENDAR vs COURSES:
        - CALENDAR: "What are the assignments for social media?", "When are my assignments due?", "Show me upcoming deadlines", "What do I need to submit this week?"
        - COURSES: "What courses am I enrolled in?", "Tell me about my courses", "Show me my course list", "What is the course code for web development?"

        Return ONLY a JSON response with this format (no other text):
        {{"intent": "NAVIGATION|BUILDING_INFO|EVENTS|RESTAURANTS|ANNOUNCEMENTS|CAREER_SERVICES|CALENDAR|GRADES|OUT_OF_SCOPE", "confidence": 0.0-1.0}}
        User query: {user_message}"""

        response = model.generate_content(classify_prompt)
        response_text = safe_get_response_text(response, "{}").strip()

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                'intent': parsed.get('intent', 'OUT_OF_SCOPE'),
                'confidence': parsed.get('confidence', 0.5),
                'entities': {}
            }

        return {'intent': 'OUT_OF_SCOPE', 'confidence': 0.5, 'entities': {}}

    except Exception as e:
        print(f"⚠️ Error classifying intent: {e}")
        return {'intent': 'OUT_OF_SCOPE', 'confidence': 0.0, 'entities': {}}

# ============== QUERY HANDLERS ==============

def handle_event_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles event-related queries"""
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        events_path = Path('data/campus_events.json')
        if not events_path.exists():
            return {'reply': 'Event information is currently unavailable.'}

        with open(events_path, 'r') as f:
            events_data = json.load(f)

        events = events_data.get('events', [])
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

        prompt = f"{events_prompt}\n{events_context}\n\nUser: {user_message}\nAI:"
        response = model.generate_content(prompt)
        response_text = safe_get_response_text(response)
        clean_response = clean_html_to_text(response_text, keep_emojis=True)

        return {'reply': clean_response}

    except Exception as e:
        print(f"⚠️ Error handling event query: {e}")
        return {'reply': 'Sorry, I encountered an error while searching for events.'}

def handle_restaurant_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles restaurant/dining queries"""
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        restaurants_path = Path('data/campus_restaurants.json')
        if not restaurants_path.exists():
            return {'reply': 'Restaurant information is currently unavailable.'}

        with open(restaurants_path, 'r') as f:
            restaurants_data = json.load(f)

        restaurants = restaurants_data.get('restaurants', [])
        
        from datetime import datetime
        today = datetime.now().strftime('%A').lower()

        restaurants_context = "\n\n** Campus Dining Options: **\n"
        for restaurant in restaurants:
            restaurants_context += f"\n- **{restaurant['name']}**\n"
            restaurants_context += f"  Location: {restaurant['location']}\n"
            restaurants_context += f"  Type: {restaurant['cuisine_type']}\n"

            hours = restaurant.get('hours', {})
            if today in hours:
                restaurants_context += f"  Hours Today ({today.capitalize()}): {hours[today]}\n"

            menu = restaurant.get('menu_highlights', [])
            if menu:
                restaurants_context += f"  Menu: {', '.join(menu)}\n"

            restaurants_context += f"  Payment: {', '.join(restaurant.get('payment_methods', []))}\n"

        current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
        prompt = f"{restaurants_prompt}\n\nCurrent time: {current_time}\n{restaurants_context}\n\nUser: {user_message}\nAI:"

        response = model.generate_content(prompt)
        response_text = safe_get_response_text(response)
        clean_response = clean_html_to_text(response_text, keep_emojis=True)

        return {'reply': clean_response}

    except Exception as e:
        print(f"⚠️ Error handling restaurant query: {e}")
        return {'reply': 'Sorry, I encountered an error while searching for restaurants.'}

def parse_announcement_date(date_string: str) -> Optional[datetime]:
    """Parse announcement date string to datetime object

    Handles formats like "Dec 7, 2025 1:37 PM"
    Returns None for empty or unparseable dates
    """
    if not date_string or date_string.strip() == "":
        return None

    try:
        # Format: "Dec 7, 2025 1:37 PM"
        return datetime.strptime(date_string, "%b %d, %Y %I:%M %p")
    except ValueError:
        # Try without time if format differs
        try:
            return datetime.strptime(date_string, "%b %d, %Y")
        except ValueError:
            return None

def load_announcement_content(course_id: str) -> dict:
    """Load full announcement content for a specific course from individual course file"""
    try:
        announcements_dir = ANNOUNCEMENTS_DIR
        course_file = announcements_dir / f'course_{course_id}_announcements.json'

        if not course_file.exists():
            return {}

        with open(course_file, 'r', encoding='utf-8') as f:
            course_data = json.load(f)

        # Return announcements indexed by title for easy lookup
        announcements_by_title = {}
        for announcement in course_data.get('announcements', []):
            title = announcement.get('title')
            if title:
                announcements_by_title[title] = announcement

        return announcements_by_title
    except Exception as e:
        print(f"⚠️ Error loading announcement content for course {course_id}: {e}")
        return {}

def handle_announcement_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles announcement-related queries using multi-course aggregated data"""
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        announcements_path = ANNOUNCEMENTS_FILE
        if not announcements_path.exists():
            return {'reply': 'Announcement information is currently unavailable. Please run the announcements extraction pipeline to collect D2L announcements.'}

        with open(announcements_path, 'r', encoding='utf-8') as f:
            courses_data = json.load(f)

        # Handle both array format (multi-course) and single object format (legacy)
        if isinstance(courses_data, dict):
            courses_data = [courses_data]

        if not courses_data:
            return {'reply': 'No courses with announcements found.'}

        # Extract course context from entities if available
        target_course_id = None
        if entities and 'course' in entities:
            target_course_id = entities['course']

        # Detect if user is asking for recent announcements
        recency_keywords = ['recent', 'latest', 'new', 'this week', 'last week', 'past week']
        filter_recent = any(keyword in user_message.lower() for keyword in recency_keywords)

        # Detect course from user message by keywords
        course_keywords = {
            'capstone': '2001542',
            'nlp': '2001539',
            'natural language processing': '2001539',
            'social media': '2001541',
            'homeroom': '2014765',
            'aim': '2014765',
            'machine learning': '2001540',
            'machine learning optimization': '2001540',
            'tensorflow': '2001538',
            'keras': '2001538',
            'tensorflow & keras': '2001538',
            'tensorflow and keras': '2001538'
        }

        # Check user message for course keywords
        detected_course_id = None
        user_msg_lower = user_message.lower()
        for keyword, course_id in course_keywords.items():
            if keyword in user_msg_lower:
                detected_course_id = course_id
                break

        # Override entity-based course detection if we found one in message
        if detected_course_id:
            target_course_id = detected_course_id

        # Collect and filter announcements
        all_announcements = []
        for course in courses_data:
            course_id = course.get('course_id')

            # Filter by course if specified
            if target_course_id and str(course_id) != str(target_course_id):
                continue

            for announcement in course.get('announcements', []):
                all_announcements.append({
                    'title': announcement.get('title', 'Untitled'),
                    'date': announcement.get('date', 'Unknown date'),
                    'url': announcement.get('url', ''),
                    'course_id': course_id,
                    'content_length': announcement.get('content_length', 0)
                })

        if not all_announcements:
            return {'reply': 'No announcements found for your request.'}

        # Sort by date (most recent first) - parse dates properly for correct chronological order
        def get_sort_key(announcement):
            parsed = parse_announcement_date(announcement['date'])
            # Return datetime if parseable, otherwise return minimum datetime for sorting to end
            return parsed if parsed else datetime.min

        all_announcements.sort(key=get_sort_key, reverse=True)

        # Apply recency filter if user asked for recent announcements
        is_filtered_recent = False

        if filter_recent:
            # Take top 5 most recent announcements (already sorted by date, newest first)
            if len(all_announcements) > 5:
                all_announcements = all_announcements[:5]
                is_filtered_recent = True
            elif all_announcements:
                # Less than 5 available, show all available
                is_filtered_recent = True

        # Build context with announcements
        if is_filtered_recent:
            announcements_context = "\n\n** D2L Announcements (Top 5 Recent): **\n"
        else:
            announcements_context = "\n\n** Recent D2L Announcements: **\n"

        announcements_context += f"Total: {len(all_announcements)} announcements found\n"

        # Cache loaded course content to avoid repeated file reads
        loaded_content_cache = {}

        # Include top announcements (up to 15 for better context)
        for announcement in all_announcements[:15]:
            announcements_context += f"\n- **{announcement['title']}**\n"
            announcements_context += f"  Course: {announcement['course_id']} | Posted: {announcement['date']}\n"
            if announcement['url']:
                announcements_context += f"  Link: {announcement['url']}\n"

            # Try to load full content for top announcements
            course_id = announcement['course_id']
            if course_id not in loaded_content_cache:
                loaded_content_cache[course_id] = load_announcement_content(course_id)

            course_content = loaded_content_cache[course_id]
            if announcement['title'] in course_content:
                full_content = course_content[announcement['title']].get('content', '')
                if full_content:
                    # Include first 300 chars of full content if available
                    preview = full_content[:300] + '...' if len(full_content) > 300 else full_content
                    announcements_context += f"  Content Preview: {preview}\n"

        prompt = f"{announcements_prompt}\n{announcements_context}\n\nUser: {user_message}\nAI:"
        response = model.generate_content(prompt)
        response_text = safe_get_response_text(response)
        clean_response = clean_html_to_text(response_text, keep_emojis=True)

        return {'reply': clean_response}

    except Exception as e:
        print(f"⚠️ Error handling announcement query: {e}")
        return {'reply': 'Sorry, I encountered an error while searching for announcements.'}

def handle_career_services_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles career services queries"""
    standard_message = """💼 Career Services

I can help you with career services!

Fanshawe Career Services provides comprehensive support for your career development, including:

📄 Resume and cover letter assistance
🤝 Interview preparation and mock interviews
👔 Job search strategies and employer connections
🎓 Co-op and internship support
💬 Career counseling and guidance
👨‍🏫 Mentorship programs (industry and peer)
🎉 Career workshops and networking events
📸 Professional headshot services

🔗 Visit the Career Services portal to access all resources and book appointments:
https://www.fanshaweonline.ca/d2l/home/906769

💡 For more information, you can also visit: www.fanshawec.ca/student-life-services/career-services"""

    clean_response = clean_html_to_text(standard_message, keep_emojis=True)
    return {'reply': clean_response}

def handle_calendar_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles calendar and deadline queries"""
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        calendar_path = Path('data/calendar/calendar.json')
        if not calendar_path.exists():
            return {'reply': 'Calendar information is currently unavailable.'}

        with open(calendar_path, 'r') as f:
            calendar_data = json.load(f)

        deadlines = calendar_data.get('academic_schedule', {}).get('deadlines', [])
        semester = calendar_data.get('academic_schedule', {}).get('semester', 'Current Semester')
        
        calendar_context = f"\n\n**Academic Calendar - {semester}**\n\nUpcoming Deadlines:\n"
        
        for deadline in deadlines:
            calendar_context += f"\n- **{deadline.get('task_name', 'Task')}**\n"
            calendar_context += f"  Date: {deadline.get('date')} ({deadline.get('day')})\n"
            calendar_context += f"  Time: {deadline.get('time', 'Not specified')}\n"
            if deadline.get('course_code'):
                calendar_context += f"  Course: {deadline.get('course_code')}\n"
            if deadline.get('description'):
                calendar_context += f"  Description: {deadline.get('description')}\n"
        
        course = deadline.get('course_code')
        print(f"📅 Handling calendar query for course: {course}")

        chat_prompt = f"""You are Fanshawe Navigator, a helpful campus assistant.

Context: {calendar_context}

User question: {user_message}

Filter by course or date if specified.

Use emojis for visual appeal: 📅 for calendar sections, ⏰ for deadlines, ⚠️ for urgent items, 💡 for tips. Format with clear section headers using emojis.

Include a 'Next Step' section with 💡 suggesting practical actions like exporting to .ics format for calendar apps.

Provide a clear, helpful response about the academic calendar and deadlines. Format dates naturally and highlight urgent deadlines."""

        response = model.generate_content(chat_prompt)
        response_text = safe_get_response_text(response, 'Unable to process calendar information.')
        clean_response = clean_html_to_text(response_text, keep_emojis=True)

        return {'reply': clean_response}

    except Exception as e:
        print(f"⚠️ Error handling calendar query: {e}")
        return {'reply': 'Sorry, I encountered an error retrieving calendar information.'}

def handle_grades_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles grades and assessment queries"""
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        grades_path = Path('data/grades/grades.json')
        if not grades_path.exists():
            return {'reply': 'Grades information is currently unavailable.'}

        with open(grades_path, 'r') as f:
            grades_data = json.load(f)

        student_log = grades_data.get('student_performance_log', {})
        semester = student_log.get('semester', 'Current Semester')
        courses = student_log.get('courses', [])
        
        grades_context = f"\n\n**Student Performance - {semester}**\n\n"
        
        for course in courses:
            course_id = course.get('course_id', 'Unknown Course')
            grades_context += f"\n**{course_id}**\n"
            
            assessments = course.get('assessments', [])
            for assessment in assessments:
                activity = assessment.get('activity', 'Assessment')
                points_earned = assessment.get('points_earned', 0)
                points_possible = assessment.get('points_possible', 0)
                weight = assessment.get('weight_achieved', '')
                feedback = assessment.get('feedback', '')
                
                grades_context += f"  - {activity}: {points_earned}/{points_possible}"
                if weight:
                    grades_context += f" (Weight: {weight})"
                if feedback:
                    grades_context += f"\n    Feedback: {feedback}"
                grades_context += "\n"

        chat_prompt = f"""You are Fanshawe Navigator, a helpful campus assistant.

Context: {grades_context}

User question: {user_message}

Use emojis for visual appeal: 📊 for grades overview, ✅ for completed work, ⭐ for excellent performance, ⚠️ for areas needing attention, 💡 for tips. Be encouraging and specific.

Start with '📊 Academic Performance' header and include performance insights with appropriate emojis.

Provide a clear, helpful response about grades and assessments. Be encouraging and specific. If asked about overall performance, calculate percentages or provide summaries."""

        response = model.generate_content(chat_prompt)
        response_text = safe_get_response_text(response, 'Unable to process grades information.')
        clean_response = clean_html_to_text(response_text, keep_emojis=True)

        return {'reply': clean_response}

    except Exception as e:
        print(f"⚠️ Error handling grades query: {e}")
        return {'reply': 'Sorry, I encountered an error retrieving grades information.'}

def handle_out_of_scope_query(user_message: str) -> Dict[str, Any]:
    """Handles out-of-scope queries"""
    fallback_message = """I'm Fanshawe Navigator, your campus assistant! I specialize in helping you with:

🗺️ Navigation & Directions - Finding your way around campus
🏢 Building Information - Learn about campus buildings and facilities
📚 Course Information - Your enrolled courses and details
🎉 Campus Events - Discovering activities and schedules
🍽️ Dining & Restaurants - Locating food services on campus
📢 Course Announcements - D2L updates and class news
💼 Career Services - Job search, resume help, interviews, co-op support
📅 Academic Calendar - Deadlines and important dates
📊 Grades & Assessments - Your academic performance

Your question seems to be outside these areas. For other assistance, please visit:
🔗 Student Services: www.fanshawec.ca/student-services
🔗 Academic Support: Contact your program coordinator
ℹ️ General Inquiries: Visit the Information Desk at the Student Centre

How else can I help you?"""

    clean_response = clean_html_to_text(fallback_message, keep_emojis=True)
    return {'reply': clean_response}

def handle_building_info_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles building information queries"""
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        building_data = load_building_info()
        
        if not building_data:
            return {'reply': 'Building information is currently unavailable.'}

        # Build context from building data
        buildings_context = "\n\n** Fanshawe Campus Buildings Information: **\n"
        
        for building_code, building_info in building_data.items():
            buildings_context += f"\n**Building {building_code}**\n"
            
            if building_info.get('name'):
                buildings_context += f"Name: {building_info['name']}\n"
            
            if building_info.get('description'):
                buildings_context += f"Description: {building_info['description']}\n"
            
            if building_info.get('facilities'):
                facilities = building_info['facilities']
                if isinstance(facilities, list):
                    buildings_context += f"Facilities: {', '.join(facilities)}\n"
                elif isinstance(facilities, str):
                    buildings_context += f"Facilities: {facilities}\n"
            
            if building_info.get('departments'):
                departments = building_info['departments']
                if isinstance(departments, list):
                    buildings_context += f"Departments: {', '.join(departments)}\n"
                elif isinstance(departments, str):
                    buildings_context += f"Departments: {departments}\n"
            
            if building_info.get('floors'):
                buildings_context += f"Floors: {building_info['floors']}\n"
            
            if building_info.get('accessibility'):
                buildings_context += f"Accessibility: {building_info['accessibility']}\n"
            
            buildings_context += "\n"

        prompt = f"{building_info_prompt}\n{buildings_context}\n\nUser: {user_message}\nAI:"
        response = model.generate_content(prompt)
        response_text = safe_get_response_text(response)
        clean_response = clean_html_to_text(response_text, keep_emojis=True)

        return {'reply': clean_response}

    except Exception as e:
        print(f"⚠️ Error handling building info query: {e}")
        return {'reply': 'Sorry, I encountered an error while searching for building information.'}

def handle_courses_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles course information queries"""
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        courses_data = load_courses_info()
        
        if not courses_data:
            return {'reply': 'Course information is currently unavailable.'}

        # Build context from courses data
        courses_context = "\n\n** Your Enrolled Courses: **\n"
        
        courses_list = courses_data.get('courses', [])
        
        # Filter out non-course entries (Homeroom, Career Services, etc.)
        excluded_keywords = [
            'homeroom',
            'career services online resources',
            'welcome',
        ]
        
        actual_courses = []
        for course in courses_list:
            title = course.get('title', '').lower()
            code = course.get('code', '')
            
            # Skip if title contains excluded keywords
            is_excluded = any(keyword in title for keyword in excluded_keywords)
            
            # Skip if no course code (non-academic entries typically don't have codes)
            if not is_excluded and code:
                actual_courses.append(course)
        
        total_courses = len(actual_courses)
        courses_context += f"Total Enrolled Courses: {total_courses}\n\n"
        
        for course in actual_courses:
            title = course.get('title', 'Unknown Course')
            code = course.get('code', 'N/A')
            course_id = course.get('course_id', '')
            url = course.get('url', '')
            
            courses_context += f"\n**{title}**\n"
            if code:
                courses_context += f"Code: {code}\n"
            courses_context += f"Course ID: {course_id}\n"
            courses_context += f"URL: {url}\n"
            
            # Add widgets information
            widgets = course.get('widgets', [])
            if widgets:
                widget_titles = [w.get('title', '') for w in widgets]
                courses_context += f"Available Sections: {', '.join(widget_titles)}\n"
            
            # Add recent announcements from links
            links = course.get('links', [])
            announcement_links = [link for link in links if 'announcement' in link.get('text', '').lower()]
            if announcement_links:
                courses_context += f"Recent Announcements:\n"
                for ann in announcement_links[:3]:  # Limit to 3 most recent
                    courses_context += f"  - {ann.get('text', 'Unknown')}\n"
            
            # Add content info
            content = course.get('content', {})
            if content:
                courses_context += f"Content: {content.get('total_links', 0)} links, {content.get('total_images', 0)} images\n"
            
            courses_context += "\n"

        prompt = f"{courses_prompt}\n{courses_context}\n\nUser: {user_message}\nAI:"
        response = model.generate_content(prompt)
        response_text = safe_get_response_text(response)
        clean_response = clean_html_to_text(response_text, keep_emojis=True)

        return {'reply': clean_response}

    except Exception as e:
        print(f"⚠️ Error handling courses query: {e}")
        return {'reply': 'Sorry, I encountered an error while searching for course information.'}

def load_building_info():
    """Load building information from JSON file"""
    global building_info_data

    if building_info_data is not None:
        return building_info_data

    possible_paths = [
        project_root / 'data' / 'map_data' / 'predios_info_english.json',
        project_root / 'src' / 'config' / 'predios_info_english.json',
    ]

    for json_path in possible_paths:
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                building_info_data = json.load(f)
                print(f"✅ Building info loaded from {json_path}")
                return building_info_data

    print("⚠️ Building info JSON not found")
    return {}

def load_courses_info():
    """Load courses information from JSON file"""
    courses_path = project_root / 'data' / 'courses_info' / 'courses_summary.json'
    
    if courses_path.exists():
        try:
            with open(courses_path, 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
                print(f"✅ Courses info loaded from {courses_path}")
                return courses_data
        except Exception as e:
            print(f"⚠️ Error loading courses info: {e}")
            return {}
    else:
        print(f"⚠️ Courses info JSON not found at {courses_path}")
        return {}

# ============== FLASK ROUTES ==============

@app.route("/")
def index():
    """Serve React app entry point"""
    return send_from_directory(str(react_build_dir), 'index.html')

@app.route("/api/chat", methods=['POST'])
def api_chat():
    """Main chat endpoint compatible with React frontend"""
    if model is None:
        return jsonify({"reply": "The AI model is not configured. Please set the GEMINI_API_KEY environment variable."}), 500

    user_message = request.json.get("mensagem") or request.json.get("message")
    user_position = request.json.get("user_position")  # New: GPS or manual position
    session_id = request.json.get("session_id")  # Session ID from frontend
    
    if not user_message:
        return jsonify({"reply": "Please provide a message."}), 400

    try:
        # Get or create session
        if not session_id or session_id not in sessions:
            session_id = session_manager.create_session()
        
        # Add user message to session
        session_manager.add_message(session_id, "user", user_message)
        
        intent_result = classify_user_intent(user_message)
        intent_type = intent_result['intent']

        print(f"🎯 Intent: {intent_type} (confidence: {intent_result['confidence']:.2f}) [Session: {session_id[:8]}...]")
        if user_position:
            print(f"📍 User position: {user_position}")

        # Route to appropriate handler
        if intent_type == "NAVIGATION":
            # Simplified: Just direct user to interactive map
            reply_message = "To navigate inside buildings and find routes between rooms:\n• Click the 'Interactive Map' button below the chatbar\n• Select your starting point and destination\n• Get detailed step-by-step indoor directions\n\nFor general campus overview and building locations:\n• Click the 'Show Campus Map' button to view all buildings and campus layout"
            response_data = {
                "reply": reply_message,
                "session_id": session_id,
                "message_count": session_manager.get_message_count(session_id),
                "mapAction": {
                    "type": "OPEN_MAP",
                    "message": "Use the interactive map for navigation"
                }
            }
        elif intent_type == "BUILDING_INFO":
            result = handle_building_info_query(user_message, intent_result['entities'])
            response_data = {**result, "session_id": session_id, "message_count": session_manager.get_message_count(session_id)}
        elif intent_type == "COURSES":
            result = handle_courses_query(user_message, intent_result['entities'])
            response_data = {**result, "session_id": session_id, "message_count": session_manager.get_message_count(session_id)}
        elif intent_type == "EVENTS":
            result = handle_event_query(user_message, intent_result['entities'])
            response_data = {**result, "session_id": session_id, "message_count": session_manager.get_message_count(session_id)}
        elif intent_type == "RESTAURANTS":
            result = handle_restaurant_query(user_message, intent_result['entities'])
            response_data = {**result, "session_id": session_id, "message_count": session_manager.get_message_count(session_id)}
        elif intent_type == "ANNOUNCEMENTS":
            result = handle_announcement_query(user_message, intent_result['entities'])
            response_data = {**result, "session_id": session_id, "message_count": session_manager.get_message_count(session_id)}
        elif intent_type == "CAREER_SERVICES":
            result = handle_career_services_query(user_message, intent_result['entities'])
            response_data = {**result, "session_id": session_id, "message_count": session_manager.get_message_count(session_id)}
        elif intent_type == "CALENDAR":
            result = handle_calendar_query(user_message, intent_result['entities'])
            response_data = {**result, "session_id": session_id, "message_count": session_manager.get_message_count(session_id)}
        elif intent_type == "GRADES":
            result = handle_grades_query(user_message, intent_result['entities'])
            response_data = {**result, "session_id": session_id, "message_count": session_manager.get_message_count(session_id)}
        else:
            result = handle_out_of_scope_query(user_message)
            response_data = {**result, "session_id": session_id, "message_count": session_manager.get_message_count(session_id)}
        
        # Add assistant response to session
        session_manager.add_message(session_id, "assistant", response_data.get("reply", ""))
        
        return jsonify(response_data)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return jsonify({"reply": f"An error occurred: {e}"}), 500

@app.route("/chat", methods=['POST'])
def chat():
    """Legacy chat endpoint"""
    return api_chat()

# ============== SESSION MANAGEMENT ENDPOINTS ==============

@app.route("/api/session/new", methods=['POST'])
def api_session_new():
    """Create a new session"""
    try:
        session_id = session_manager.create_session()
        return jsonify({
            "session_id": session_id,
            "message_count": session_manager.get_message_count(session_id),
            "created_at": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/session/<session_id>/info", methods=['GET'])
def api_session_info(session_id):
    """Get session information"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({
            "session_id": session_id,
            "message_count": session_manager.get_message_count(session_id),
            "created_at": session["created_at"].isoformat(),
            "last_accessed": session["last_accessed"].isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/session/<session_id>/history", methods=['GET'])
def api_session_history(session_id):
    """Get full session history (active + archived)"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({
            "session_id": session_id,
            "active_messages": session["messages"],
            "archived_messages": session["archived_messages"],
            "message_count": session_manager.get_message_count(session_id)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/session/<session_id>/clear", methods=['DELETE'])
def api_session_clear(session_id):
    """Clear session messages"""
    try:
        keep_archive = request.args.get('keep_archive', 'true').lower() == 'true'
        session_manager.clear_session(session_id, keep_archive=keep_archive)
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": f"Session cleared (archive {'kept' if keep_archive else 'deleted'})"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/session/stats", methods=['GET'])
def api_session_stats():
    """Get overall session statistics"""
    try:
        with session_lock:
            total_sessions = len(sessions)
            total_active_messages = sum(len(s["messages"]) for s in sessions.values())
            total_archived_messages = sum(len(s["archived_messages"]) for s in sessions.values())
        
        return jsonify({
            "total_sessions": total_sessions,
            "total_active_messages": total_active_messages,
            "total_archived_messages": total_archived_messages,
            "max_active_messages_per_session": SessionCacheManager.MAX_ACTIVE_MESSAGES,
            "session_ttl_hours": SessionCacheManager.SESSION_TTL_HOURS
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============== EXISTING ROUTES ==============

@app.route("/api/geojson", methods=['GET'])
def api_geojson():
    """Returns campus buildings GeoJSON data"""
    try:
        possible_paths = [
            project_root / 'data' / 'map_data' / 'campus.geojson',
            project_root / 'data' / 'campus.geojson',
        ]

        for geojson_path in possible_paths:
            if geojson_path.exists():
                with open(geojson_path, 'r', encoding='utf-8') as f:
                    return jsonify(json.load(f))

        return jsonify({
            "type": "FeatureCollection",
            "features": []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/calcular-rota", methods=['POST'])
def api_calcular_rota():
    """Calculate route between two buildings"""
    try:
        data = request.json
        return jsonify({
            "origem": data.get('origem'),
            "destino": data.get('destino'),
            "rota": {
                "type": "LineString",
                "coordinates": []
            },
            "distancia": 0,
            "tempo_estimado": 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/predios/<predio_ref>/info", methods=['GET'])
def api_predio_info(predio_ref):
    """Returns detailed building information"""
    try:
        building_data = load_building_info()

        if predio_ref.upper() in building_data:
            return jsonify({
                "success": True,
                "info": building_data[predio_ref.upper()]
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Building {predio_ref} not found"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/system/status", methods=['GET'])
def system_status():
    """Returns system status"""
    return jsonify({
        "gemini_model": "configured" if model is not None else "not_configured",
        "environment": {
            "gemini_api_key": "set" if os.getenv("GEMINI_API_KEY") else "not_set"
        }
    })

@app.route("/api/announcements/status", methods=['GET'])
def announcements_status():
    """Returns announcements data status"""
    try:
        announcements_path = ANNOUNCEMENTS_FILE
        if not announcements_path.exists():
            return jsonify({
                "status": "no_data",
                "file_exists": False
            })

        with open(announcements_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return jsonify({
            "status": "available",
            "file_exists": True,
            "total_announcements": data.get('total_announcements', 0),
            "course": data.get('course', 'Unknown')
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/professor/<course_id>", methods=['GET'])
def get_professor_info(course_id):
    """Get cached professor information for a course"""
    try:
        prof_file = Path(f'data/course_{course_id}/professor_info.json')
        
        if not prof_file.exists():
            return jsonify({
                "status": "not_found",
                "course_id": course_id
            }), 404
        
        with open(prof_file, 'r', encoding='utf-8') as f:
            prof_data = json.load(f)
        
        return jsonify({
            "status": "success",
            "course_id": course_id,
            "professor": {
                "name": prof_data.get('name'),
                "email": prof_data.get('email'),
                "office": prof_data.get('office'),
                "office_hours": prof_data.get('office_hours')
            }
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
    """Handle navigation request from map clicks"""
    if model is None:
        return jsonify({"error": "AI model not configured"}), 500

    try:
        data = request.json
        if not data or not data.get('startRoom') or not data.get('endRoom'):
            return jsonify({"error": "startRoom and endRoom required"}), 400

        start_room = data.get('startRoom')
        end_room = data.get('endRoom')

        start_friendly = get_room_friendly_name(start_room)
        end_friendly = get_room_friendly_name(end_room)

        nav_message = f"Give me walking directions from {start_friendly} to {end_friendly} in Building M Floor 1."
        prompt = f'{map_info}\n\nUser: {nav_message}\nAI:'

        response = model.generate_content(prompt)
        response_text = safe_get_response_text(response)
        clean_response = clean_html_to_text(response_text, keep_emojis=True)

        room_to_node = building_m_config.get('roomToNode', {})

        return jsonify({
            "reply": clean_response,
            "startRoom": start_room,
            "endRoom": end_room,
            "startNode": room_to_node.get(start_room),
            "endNode": room_to_node.get(end_room)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/navigation/rooms", methods=['GET'])
def api_get_rooms():
    """Get list of all rooms in Building M"""
    if not building_m_config:
        return jsonify({"error": "Configuration not loaded"}), 500

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
    """Get manual room center coordinates"""
    if not building_m_config:
        return jsonify({"error": "Configuration not loaded"}), 500

    room_centers = building_m_config.get('roomCentersSVG', {})
    filtered_centers = {k: v for k, v in room_centers.items() if not k.startswith('_')}

    return jsonify(filtered_centers)

@app.route("/api/navigation/data", methods=['GET'])
def api_get_navigation_data():
    """Get navigation graph data for a specific building and floor"""
    building = request.args.get('building', 'M')
    floor = request.args.get('floor', '1')
    
    nav_service = get_navigation_service()
    floor_data = nav_service.get_building_data(building, floor)
    
    if not floor_data:
        return jsonify({"error": f"No data for Building {building}, Floor {floor}"}), 404
    
    return jsonify(floor_data)

@app.route("/api/navigation/buildings", methods=['GET'])
def api_get_buildings():
    """Get list of all buildings with navigation data"""
    nav_service = get_navigation_service()
    buildings = nav_service.get_available_buildings()
    
    return jsonify({"buildings": buildings})

@app.route("/api/navigation/floors/<building>", methods=['GET'])
def api_get_floors(building):
    """Get list of all floors for a building"""
    nav_service = get_navigation_service()
    floors = nav_service.get_available_floors(building)
    
    if not floors:
        return jsonify({"error": f"No data for Building {building}"}), 404
    
    # Convert string array to object array with level property for frontend compatibility
    floors_data = [{"level": floor} for floor in floors]
    
    return jsonify({"building": building, "floors": floors_data})

@app.route("/api/navigation/building-connections", methods=['GET'])
def api_get_building_connections():
    """Get building-to-building connections for multi-building navigation"""
    try:
        connections_path = project_root / 'LeafletJS' / 'building_connections.JSON'
        
        if not connections_path.exists():
            return jsonify({"error": "Building connections file not found"}), 404
        
        with open(connections_path, 'r') as f:
            connections = json.load(f)
        
        return jsonify(connections)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/navigation/all-node-data", methods=['GET'])
def api_get_all_node_data():
    """Get complete all_node_data.json for client-side navigation"""
    try:
        all_node_data_path = project_root / 'LeafletJS' / 'all_node_data.json'
        
        if not all_node_data_path.exists():
            return jsonify({"error": "all_node_data.json not found"}), 404
        
        with open(all_node_data_path, 'r') as f:
            all_data = json.load(f)
        
        return jsonify(all_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/navigation/svg-content/<building>/<floor>", methods=['GET'])
def api_get_svg_content(building, floor):
    """Get SVG floor plan content for node parsing"""
    try:
        svg_path = project_root / 'LeafletJS' / 'Floorplans' / f'Building {building}' / f'{building}{floor}.svg'
        
        if not svg_path.exists():
            return jsonify({"error": f"SVG not found for Building {building} Floor {floor}"}), 404
        
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        return jsonify({"svgContent": svg_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/navigation/calculate", methods=['POST'])
def api_calculate_path():
    """
    Calculate navigation path between two locations
    
    Request JSON:
    {
        "start": {"building": "M", "floor": "1", "node": "M1_1"},
        "end": {"building": "H", "floor": "1", "node": "H1_20"}
    }
    
    Or:
    {
        "start": {"building": "M", "floor": "1", "room": "1003"},
        "end": {"building": "M", "floor": "1", "room": "1018"}
    }
    """
    data = request.json
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    start = data.get('start')
    end = data.get('end')
    
    if not start or not end:
        return jsonify({"error": "start and end locations required"}), 400
    
    nav_service = get_navigation_service()
    
    # Resolve room IDs to nodes if provided
    start_node = start.get('node')
    if not start_node and start.get('room'):
        start_node = nav_service.resolve_room_to_node(
            start['building'], start['floor'], start['room']
        )
        if not start_node:
            return jsonify({"error": f"Could not find node for room {start['room']}"}), 400
    
    end_node = end.get('node')
    if not end_node and end.get('room'):
        end_node = nav_service.resolve_room_to_node(
            end['building'], end['floor'], end['room']
        )
        if not end_node:
            return jsonify({"error": f"Could not find node for room {end['room']}"}), 400
    
    if not start_node or not end_node:
        return jsonify({"error": "Could not resolve start or end node"}), 400
    
    # Calculate path
    path = nav_service.find_path(
        start['building'], start['floor'], start_node,
        end['building'], end['floor'], end_node
    )
    
    if not path:
        return jsonify({"error": "No path found"}), 404
    
    # Generate directions
    dir_service = get_direction_service()
    directions = dir_service.generate_directions(path)
    
    return jsonify({
        "path": path,
        "directions": directions,
        "text_summary": dir_service.generate_text_summary(directions)
    })

@app.route("/api/navigation/room-lookup", methods=['POST'])
def api_room_lookup():
    """
    Look up node for a room ID
    
    Request JSON:
    {
        "building": "M",
        "floor": "1",
        "room": "1003"
    }
    """
    data = request.json
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    building = data.get('building')
    floor = data.get('floor')
    room = data.get('room')
    
    if not all([building, floor, room]):
        return jsonify({"error": "building, floor, and room required"}), 400
    
    nav_service = get_navigation_service()
    node = nav_service.resolve_room_to_node(building, floor, room)
    
    if not node:
        return jsonify({"error": f"Room {room} not found"}), 404
    
    node_info = nav_service.get_node_info(building, floor, node)
    
    return jsonify({
        "room": room,
        "node": node,
        "node_info": node_info
    })

@app.route("/api/navigation/all-rooms", methods=['GET'])
def api_get_all_rooms():
    """Get all rooms for a building and floor"""
    building = request.args.get('building', 'M')
    floor = request.args.get('floor', '1')
    
    nav_service = get_navigation_service()
    rooms = nav_service.get_all_rooms(building, floor)
    
    if not rooms:
        return jsonify({"error": f"No rooms found for Building {building}, Floor {floor}"}), 404
    
    return jsonify({
        "building": building,
        "floor": floor,
        "rooms": rooms
    })

@app.route('/leaflet-assets/<path:path>')
def serve_leaflet_assets(path):
    """Serve LeafletJS floor plans, navigation data, and plugins"""
    leaflet_dir = project_root / 'LeafletJS'
    return send_from_directory(str(leaflet_dir), path)

@app.route('/interactive-map')
def serve_interactive_map():
    """Serve the integrated Leaflet navigation map (interactiveMap.html)"""
    leaflet_dir = project_root / 'LeafletJS'
    print(f"🗺️ Serving interactive map from: {leaflet_dir / 'interactiveMap.html'}")
    return send_from_directory(str(leaflet_dir), 'interactiveMap.html')

@app.route('/<path:path>')
def catch_all(path):
    """Serve React app for client-side routing"""
    # Don't intercept the interactive-map route
    if path == 'interactive-map':
        return serve_interactive_map()
    
    file_path = os.path.join(react_build_dir, path)

    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(str(react_build_dir), path)

    return send_from_directory(str(react_build_dir), 'index.html')

def main():
    load_building_info()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081)))

if __name__ == "__main__":
    main()
