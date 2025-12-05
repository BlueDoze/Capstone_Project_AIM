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
from src.services.navigation_service import get_navigation_service
from src.services.direction_service import get_direction_service

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
    
    # Configure safety settings to allow campus navigation queries
    # These settings prevent blocking of legitimate queries containing words like "bathroom", "room", etc.
    safety_settings = {
        genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
    }
    
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    print("✅ Gemini AI model configured with safety settings")
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
    user_position = request.json.get("user_position")  # New: GPS or manual position
    
    if not user_message:
        return jsonify({"reply": "Please provide a message."}), 400

    try:
        intent_result = classify_user_intent(user_message)
        intent_type = intent_result['intent']

        print(f"🎯 Intent: {intent_type} (confidence: {intent_result['confidence']:.2f})")
        if user_position:
            print(f"📍 User position: {user_position}")

        if intent_type == "NAVIGATION":
            # Simplified: Just direct user to interactive map
            return jsonify({
                "reply": "To find routes and navigate the campus, please use the Fanshawe Map. Click the 'Show Map' button below chatbar to access the complete map navigation.\n\nOn the map you'll be able to:\n• View all buildings and rooms\n• Select starting point and destination\n• Get detailed step-by-step routes\n• Visualize routes between different buildings",
                "mapAction": {
                    "type": "OPEN_MAP",
                    "message": "Use the interactive map for navigation"
                }
            })

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
    """Serve the interactive Leaflet navigation map (set_start_end.html)"""
    leaflet_dir = project_root / 'LeafletJS'
    return send_from_directory(str(leaflet_dir), 'set_start_end.html')

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
