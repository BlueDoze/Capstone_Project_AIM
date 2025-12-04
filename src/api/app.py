import os
import sys
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from pathlib import Path
import json
import re

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import local modules
from src.api.utils.text_cleaner import clean_html_to_text

load_dotenv()

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

# Configure the generative AI model
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise KeyError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    
    # Configure generation settings
    generation_config = genai.types.GenerationConfig(
        temperature=0.3,
        max_output_tokens=2048,
        top_p=0.95,
        top_k=40
    )
    
    model = genai.GenerativeModel(
        'gemini-pro-latest',
        generation_config=generation_config
    )
    print("✅ Gemini AI model configured")
except KeyError as e:
    print(f"❌ {e}")
    model = None

# Building info cache
building_info_data = None

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
- Provide clear, concise information about the events
- Include relevant details like date, time, location, and organizer
- If multiple events match the query, list them clearly
- Suggest relevant events based on the user's interests
- If an event requires registration, mention it
- Include links when available

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
- Provide clear information about location and hours
- Mention what type of food is available
- Include operating hours, especially for today
- Suggest options based on the user's needs (quick snack, full meal, coffee, etc.)
- Mention payment methods if relevant
- Be aware of current day/time when suggesting options

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
- Provide clear, concise summaries of announcements
- Include dates when announcements were posted
- Highlight action items (deadlines, required attendance, submissions, etc.)
- Prioritize recent and urgent announcements
- Mention the instructor or source when relevant
- If multiple announcements match, list them chronologically (most recent first)
- Be aware of deadlines and time-sensitive information

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

def parse_navigation_request(user_message: str) -> Dict[str, Any]:
    """
    Parse navigation request from user message
    Uses Gemini to extract start and end locations
    """
    if not model:
        return {'is_navigation': False}

    nav_keywords = ['how', 'get', 'go', 'navigate', 'path', 'way', 'direction',
                    'from', 'to', 'reach', 'find', 'como', 'ir', 'chegar']
    message_lower = user_message.lower()
    is_likely_nav = any(keyword in message_lower for keyword in nav_keywords)

    if not is_likely_nav:
        return {'is_navigation': False}

    try:
        parse_prompt = f"""Extract the start location and destination from this message.
        Return ONLY a JSON response with this format (no other text):
        {{"is_navigation": true/false, "start": "location or null", "end": "location or null"}}

        Message: {user_message}

        For "location", use room numbers like "1003" or common names like "bathroom men", "elevator", "exit".
        If no navigation intent, set is_navigation to false."""

        response = model.generate_content(parse_prompt)
        response_text = safe_get_response_text(response, "{}").strip()

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())

            if parsed.get('is_navigation'):
                start_name = parsed.get('start')
                end_name = parsed.get('end')

                start_room = resolve_room_name(start_name) if start_name else None
                end_room = resolve_room_name(end_name) if end_name else None

                if start_room and end_room:
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
                            'floor': 1
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
    Classifies user intent into categories:
    - NAVIGATION, EVENTS, RESTAURANTS, ANNOUNCEMENTS, CAREER_SERVICES, OUT_OF_SCOPE
    """
    if not model:
        return {'intent': 'OUT_OF_SCOPE', 'confidence': 0.0, 'entities': {}}

    try:
        message_lower = user_message.lower()

        # Keyword matching for fast classification
        nav_keywords = ['how', 'get', 'go', 'navigate', 'path', 'way', 'direction',
                        'from', 'to', 'reach', 'where', 'location', 'room']
        event_keywords = ['event', 'activity', 'happening', 'schedule', 'workshop',
                          'seminar', 'fair', 'meeting', 'conference', 'talk', 'when']
        restaurant_keywords = ['food', 'eat', 'restaurant', 'cafe', 'coffee', 'lunch',
                               'dinner', 'breakfast', 'hungry', 'menu', 'dining']
        announcement_keywords = ['announcement', 'news', 'notice', 'update',
                                'd2l', 'brightspace', 'message', 'posted', 'instructor']
        career_keywords = ['career', 'job', 'resume', 'cv', 'interview', 'co-op',
                          'internship', 'employment', 'hiring', 'mentorship']

        nav_score = sum(1 for kw in nav_keywords if kw in message_lower)
        event_score = sum(1 for kw in event_keywords if kw in message_lower)
        restaurant_score = sum(1 for kw in restaurant_keywords if kw in message_lower)
        announcement_score = sum(1 for kw in announcement_keywords if kw in message_lower)
        career_score = sum(1 for kw in career_keywords if kw in message_lower)

        max_score = max(nav_score, event_score, restaurant_score, announcement_score, career_score)
        
        if max_score >= 2:
            if nav_score == max_score:
                return {'intent': 'NAVIGATION', 'confidence': 0.8, 'entities': {}}
            elif event_score == max_score:
                return {'intent': 'EVENTS', 'confidence': 0.8, 'entities': {}}
            elif restaurant_score == max_score:
                return {'intent': 'RESTAURANTS', 'confidence': 0.8, 'entities': {}}
            elif announcement_score == max_score:
                return {'intent': 'ANNOUNCEMENTS', 'confidence': 0.8, 'entities': {}}
            elif career_score == max_score:
                return {'intent': 'CAREER_SERVICES', 'confidence': 0.8, 'entities': {}}

        # Use Gemini for nuanced classification
        classify_prompt = f"""Classify this user query into ONE of these categories:
        - NAVIGATION: Questions about directions, finding locations, wayfinding on campus
        - EVENTS: Questions about campus events, activities, schedules, workshops
        - RESTAURANTS: Questions about food, dining, cafeterias, restaurants on campus
        - ANNOUNCEMENTS: Questions about course announcements, D2L news, class updates
        - CAREER_SERVICES: Questions about career services, job search, resumes, interviews
        - OUT_OF_SCOPE: Anything else not related to the above categories

        Return ONLY a JSON response with this format (no other text):
        {{"intent": "NAVIGATION|EVENTS|RESTAURANTS|ANNOUNCEMENTS|CAREER_SERVICES|OUT_OF_SCOPE", "confidence": 0.0-1.0}}

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
        clean_response = clean_html_to_text(response_text, keep_emojis=False)

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
        clean_response = clean_html_to_text(response_text, keep_emojis=False)

        return {'reply': clean_response}

    except Exception as e:
        print(f"⚠️ Error handling restaurant query: {e}")
        return {'reply': 'Sorry, I encountered an error while searching for restaurants.'}

def handle_announcement_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles announcement-related queries"""
    if not model:
        return {'reply': 'The AI model is not configured.'}

    try:
        announcements_path = Path('all_announcements.json')
        if not announcements_path.exists():
            return {'reply': 'Announcement information is currently unavailable. Please run extract_all_announcements.py to collect D2L announcements.'}

        with open(announcements_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        announcements = raw_data.get('announcements', [])
        if not announcements:
            return {'reply': 'No announcements found.'}

        announcements_context = "\n\n** Recent D2L Announcements: **\n"
        announcements_context += f"Course: {raw_data.get('course', 'Unknown')}\n"
        announcements_context += f"Total: {raw_data.get('total_announcements', 0)} announcements\n\n"

        for announcement in announcements:
            announcements_context += f"\n- **{announcement.get('title', 'Untitled')}**\n"
            announcements_context += f"  Posted: {announcement.get('date', 'Unknown date')}\n"

            content = announcement.get('content', '')
            if len(content) > 500:
                announcements_context += f"  Content: {content[:500]}...\n"
            else:
                announcements_context += f"  Content: {content}\n"

        prompt = f"{announcements_prompt}\n{announcements_context}\n\nUser: {user_message}\nAI:"
        response = model.generate_content(prompt)
        response_text = safe_get_response_text(response)
        clean_response = clean_html_to_text(response_text, keep_emojis=False)

        return {'reply': clean_response}

    except Exception as e:
        print(f"⚠️ Error handling announcement query: {e}")
        return {'reply': 'Sorry, I encountered an error while searching for announcements.'}

def handle_career_services_query(user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handles career services queries"""
    standard_message = """I can help you with career services!

Fanshawe Career Services provides comprehensive support for your career development, including:

- Resume and cover letter assistance
- Interview preparation and mock interviews
- Job search strategies and employer connections
- Co-op and internship support
- Career counseling and guidance
- Mentorship programs (industry and peer)
- Career workshops and networking events
- Professional headshot services

Visit the Career Services portal to access all resources and book appointments:
https://www.fanshaweonline.ca/d2l/home/906769

For more information, you can also visit: www.fanshawec.ca/student-life-services/career-services"""

    clean_response = clean_html_to_text(standard_message, keep_emojis=False)
    return {'reply': clean_response}

def handle_out_of_scope_query(user_message: str) -> Dict[str, Any]:
    """Handles out-of-scope queries"""
    fallback_message = """I'm Fanshawe Navigator, your campus assistant! I specialize in helping you with:

- Navigation & Directions - Finding your way around campus
- Campus Events - Discovering activities and schedules
- Dining & Restaurants - Locating food services on campus
- Course Announcements - D2L updates and class news
- Career Services - Job search, resume help, interviews, co-op support

Your question seems to be outside these areas. For other assistance, please visit:
- Student Services: www.fanshawec.ca/student-services
- Academic Support: Contact your program coordinator
- General Inquiries: Visit the Information Desk at the Student Centre

How else can I help you with navigation, events, dining, announcements, or career services?"""

    clean_response = clean_html_to_text(fallback_message, keep_emojis=False)
    return {'reply': clean_response}

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
    if not user_message:
        return jsonify({"reply": "Please provide a message."}), 400

    try:
        intent_result = classify_user_intent(user_message)
        intent_type = intent_result['intent']

        print(f"🎯 Intent: {intent_type} (confidence: {intent_result['confidence']:.2f})")

        if intent_type == "NAVIGATION":
            nav_result = parse_navigation_request(user_message)
            prompt = f'{map_info}\n\nUser: {user_message}\nAI:'

            response = model.generate_content(prompt)
            response_text = safe_get_response_text(response)
            clean_response = clean_html_to_text(response_text, keep_emojis=False)

            if nav_result.get('is_navigation'):
                return jsonify({
                    "reply": clean_response,
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
                return jsonify({"reply": clean_response})

        elif intent_type == "EVENTS":
            return jsonify(handle_event_query(user_message, intent_result['entities']))
        elif intent_type == "RESTAURANTS":
            return jsonify(handle_restaurant_query(user_message, intent_result['entities']))
        elif intent_type == "ANNOUNCEMENTS":
            return jsonify(handle_announcement_query(user_message, intent_result['entities']))
        elif intent_type == "CAREER_SERVICES":
            return jsonify(handle_career_services_query(user_message, intent_result['entities']))
        else:
            return jsonify(handle_out_of_scope_query(user_message))

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return jsonify({"reply": f"An error occurred: {e}"}), 500

@app.route("/chat", methods=['POST'])
def chat():
    """Legacy chat endpoint"""
    return api_chat()

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
        announcements_path = Path('all_announcements.json')
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
        clean_response = clean_html_to_text(response_text, keep_emojis=False)

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

@app.route('/leaflet-assets/<path:path>')
def serve_leaflet_assets(path):
    """Serve LeafletJS floor plans, navigation data, and plugins"""
    leaflet_dir = project_root / 'LeafletJS'
    return send_from_directory(str(leaflet_dir), path)

@app.route('/<path:path>')
def catch_all(path):
    """Serve React app for client-side routing"""
    file_path = os.path.join(react_build_dir, path)

    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(str(react_build_dir), path)

    return send_from_directory(str(react_build_dir), 'index.html')

def main():
    load_building_info()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081)))

if __name__ == "__main__":
    main()
