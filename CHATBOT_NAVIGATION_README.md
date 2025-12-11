# Chatbot Navigation Integration - Implementation Guide

## Overview

This document provides a complete guide for implementing chatbot-triggered indoor navigation. The system enables users to ask the chatbot for directions (e.g., "Navigate from H1015 to H1019") and automatically trigger turn-by-turn navigation on the interactive map.

**Key Features:**
- Natural language room navigation requests
- Automatic room ID extraction and validation
- Two navigation modes: room-to-room and GPS/manual-to-room
- Seamless integration with existing interactive map
- Error handling and user feedback

---

## Architecture Overview

```
User Input (Chat)
    ↓
Chatbot Backend (Flask)
    ├─ Intent Classification
    ├─ Room ID Extraction & Validation
    └─ Return navigationAction
         ↓
React Frontend
    ├─ Receive navigationAction
    ├─ Open Interactive Map (if needed)
    └─ Trigger Navigation
         ↓
Navigation Functions (interactiveMap.html)
    ├─ objectDepartureNavigation(startRoom, destRoom)
    └─ coordDepartureNavigation(destRoom)
         ↓
User sees path on map with directions
```

---

## Files to Create

### 1. Frontend Service Layer
**File:** `Frontend_Data/frontend/src/services/navigationService.js`

This service bridges the chatbot responses to the navigation functions in interactiveMap.html.

**Key Functions:**
- `executeNavigation(navigationData)` - Calls appropriate navigation function
- `checkNavigationAvailability()` - Checks if map is loaded
- `formatNavigationMessage(result)` - Formats status for UI

**Usage:**
```javascript
const result = await executeNavigation({
  type: 'objectDeparture',
  startRoomId: 'H1015',
  destinationRoomId: 'H1019'
});
```

### 2. React Custom Hook
**File:** `Frontend_Data/frontend/src/hooks/useChatbotNavigation.js`

Custom React hook that manages navigation state and availability checking.

**Key Exports:**
- `useChatbotNavigation()` hook that returns:
  - `triggerNavigation(navigationData)` - Execute navigation
  - `navigationStatus` - Current status object
  - `navigationAvailability` - Is map loaded?
  - `isNavigating` - Loading state
  - `clearNavigationStatus()` - Clear status

**Usage in Component:**
```jsx
const { triggerNavigation, navigationStatus, navigationAvailability } = useChatbotNavigation();

// When chatbot provides navigation data
await triggerNavigation({
  type: 'objectDeparture',
  startRoomId: 'H1015',
  destinationRoomId: 'H1019'
});
```

### 3. Backend Utility
**File:** `src/api/utils/room_id_extraction.py`

Python utilities for extracting and validating room IDs from user messages.

**Key Functions:**
- `extract_room_ids(text)` - Find room IDs using regex
- `parse_navigation_intent(message, available_rooms)` - Parse "from X to Y" patterns
- `validate_room_ids(room_ids, available_rooms)` - Check if rooms exist
- `find_room_id_from_description(description, available_rooms)` - Match "library" → room ID
- `suggest_similar_rooms(room_id, available_rooms)` - Typo suggestions
- `format_room_info(room_id, room_info)` - Pretty-print room details

**Usage in Backend:**
```python
from src.api.utils.room_id_extraction import parse_navigation_intent, validate_room_ids

nav_intent = parse_navigation_intent(user_message, available_rooms)
is_valid, error = validate_room_ids({
    'startRoomId': nav_intent.get('startRoomId'),
    'destinationRoomId': nav_intent.get('destinationRoomId')
}, available_rooms)

if is_valid:
    # Build navigation action
    navigation_action = {
        'type': 'objectDeparture' if nav_intent.get('startRoomId') else 'coordDeparture',
        'startRoomId': nav_intent.get('startRoomId'),
        'destinationRoomId': nav_intent['destinationRoomId']
    }
```

### 4. Example Component (Reference)
**File:** `Frontend_Data/frontend/src/components/ChatbotNavigationExample.jsx`

Complete example showing how to integrate navigation into your chat component. Use this as a reference when modifying `App.jsx`.

---

## Implementation Steps

### Step 1: Create Frontend Service Files

**Create file:** `Frontend_Data/frontend/src/services/navigationService.js`

```javascript
/**
 * Navigation Service
 * Bridge between chatbot responses and indoor navigation functions.
 */

export async function executeNavigation(navigationData) {
    try {
        if (!navigationData.destinationRoomId) {
            return {
                success: false,
                error: 'Missing destination room ID'
            };
        }

        const { type, startRoomId, destinationRoomId } = navigationData;

        if (type === 'objectDeparture') {
            if (!startRoomId) {
                return {
                    success: false,
                    error: 'Missing start room ID for room-to-room navigation'
                };
            }

            if (window.objectDepartureNavigation) {
                const result = window.objectDepartureNavigation(startRoomId, destinationRoomId);
                return {
                    success: result,
                    type: 'objectDeparture',
                    startRoom: startRoomId,
                    destinationRoom: destinationRoomId,
                    message: result 
                        ? `Navigation from ${startRoomId} to ${destinationRoomId} started!`
                        : 'Failed to start navigation'
                };
            } else {
                return {
                    success: false,
                    error: 'Indoor navigation not loaded. Please open Interactive Map first.'
                };
            }

        } else if (type === 'coordDeparture') {
            if (window.coordDepartureNavigation) {
                const result = window.coordDepartureNavigation(destinationRoomId);
                return {
                    success: result,
                    type: 'coordDeparture',
                    destinationRoom: destinationRoomId,
                    message: result
                        ? `Navigation to ${destinationRoomId} from your current location started!`
                        : 'Failed to start navigation'
                };
            } else {
                return {
                    success: false,
                    error: 'Indoor navigation not loaded. Please open Interactive Map first.'
                };
            }

        } else {
            return {
                success: false,
                error: `Unknown navigation type: ${type}`
            };
        }

    } catch (error) {
        console.error('Navigation execution error:', error);
        return {
            success: false,
            error: `Navigation error: ${error.message}`
        };
    }
}

export function checkNavigationAvailability() {
    return {
        objectDepartureNavigation: typeof window.objectDepartureNavigation === 'function',
        coordDepartureNavigation: typeof window.coordDepartureNavigation === 'function',
        interactiveMapLoaded: !!(window.buildingSVGElements && window.floorPlans)
    };
}

export function formatNavigationMessage(result) {
    if (result.success) {
        if (result.type === 'objectDeparture') {
            return `🗺️ Routing you from **${result.startRoom}** to **${result.destinationRoom}**. Check the Interactive Map for directions!`;
        } else if (result.type === 'coordDeparture') {
            return `📍 Routing you to **${result.destinationRoom}** from your current location. Check the Interactive Map for directions!`;
        }
    } else {
        return `⚠️ Navigation error: ${result.error}`;
    }
}
```

**Create file:** `Frontend_Data/frontend/src/hooks/useChatbotNavigation.js`

```javascript
import { useEffect, useState } from 'react';
import { executeNavigation, checkNavigationAvailability, formatNavigationMessage } from '../services/navigationService';

export function useChatbotNavigation() {
    const [navigationStatus, setNavigationStatus] = useState(null);
    const [isNavigating, setIsNavigating] = useState(false);
    const [navigationAvailability, setNavigationAvailability] = useState({
        objectDepartureNavigation: false,
        coordDepartureNavigation: false,
        interactiveMapLoaded: false
    });

    useEffect(() => {
        const checkAvailability = () => {
            const availability = checkNavigationAvailability();
            setNavigationAvailability(availability);
        };

        checkAvailability();

        const timer = setTimeout(checkAvailability, 1000);
        const timer2 = setInterval(checkAvailability, 5000);

        return () => {
            clearTimeout(timer);
            clearInterval(timer2);
        };
    }, []);

    const triggerNavigation = async (navigationData) => {
        setIsNavigating(true);
        try {
            const result = await executeNavigation(navigationData);
            const formattedMessage = formatNavigationMessage(result);
            
            setNavigationStatus({
                success: result.success,
                message: formattedMessage,
                data: result,
                timestamp: new Date()
            });

            return result.success;
        } catch (error) {
            console.error('Navigation trigger error:', error);
            setNavigationStatus({
                success: false,
                message: `❌ Navigation error: ${error.message}`,
                timestamp: new Date()
            });
            return false;
        } finally {
            setIsNavigating(false);
        }
    };

    const clearNavigationStatus = () => {
        setNavigationStatus(null);
    };

    return {
        triggerNavigation,
        navigationStatus,
        isNavigating,
        navigationAvailability,
        clearNavigationStatus
    };
}
```

### Step 2: Create Backend Utility

**Create file:** `src/api/utils/room_id_extraction.py`

```python
"""
Room ID Extraction Utilities for Chatbot Navigation
"""

import re
from typing import Dict, Optional, List, Tuple

ROOM_ID_PATTERN = r'\b([A-Z])(\d{4})\b'


def extract_room_ids(text: str) -> List[str]:
    """Extract potential room IDs from text"""
    matches = re.findall(ROOM_ID_PATTERN, text)
    room_ids = [f'{building}{room_num}' for building, room_num in matches]
    return room_ids


def find_room_id_from_description(description: str, available_rooms: Dict) -> Optional[str]:
    """Find a room ID from natural language description"""
    description_lower = description.lower()
    
    for room_id, room_info in available_rooms.items():
        if 'type' in room_info:
            room_type = room_info['type'].lower()
            if room_type in description_lower:
                return room_id
    
    keywords = {
        'library': 'library',
        'cafeteria': 'eatery',
        'cafe': 'eatery',
        'coffee': 'eatery',
        'bathroom': 'bathroom',
        'washroom': 'bathroom',
        'classroom': 'classroom',
        'exit': 'exit',
        'stairs': 'stairs',
        'elevator': 'elevator',
    }
    
    for keyword, room_type in keywords.items():
        if keyword in description_lower:
            floor_match = re.search(r'floor\s*(\d)', description_lower)
            floor_num = floor_match.group(1) if floor_match else None
            
            for room_id, room_info in available_rooms.items():
                if room_info.get('type') == room_type:
                    if floor_num:
                        if str(room_info.get('floor')) == floor_num:
                            return room_id
                    else:
                        return room_id
    
    return None


def parse_navigation_intent(user_message: str, available_rooms: Dict) -> Dict:
    """Parse user message to extract navigation intent"""
    
    room_ids = extract_room_ids(user_message)
    
    from_to_match = re.search(
        r'from\s+([^to]+?)\s+to\s+(.+?)(?:\.|$)',
        user_message,
        re.IGNORECASE
    )
    
    start_room_id = None
    destination_room_id = None
    descriptions = {}
    
    if from_to_match:
        from_part = from_to_match.group(1).strip()
        to_part = from_to_match.group(2).strip()
        
        from_ids = extract_room_ids(from_part)
        to_ids = extract_room_ids(to_part)
        
        if from_ids:
            start_room_id = from_ids[0]
            descriptions['start'] = from_part
        else:
            found_id = find_room_id_from_description(from_part, available_rooms)
            if found_id:
                start_room_id = found_id
                descriptions['start'] = from_part
        
        if to_ids:
            destination_room_id = to_ids[0]
            descriptions['destination'] = to_part
        else:
            found_id = find_room_id_from_description(to_part, available_rooms)
            if found_id:
                destination_room_id = found_id
                descriptions['destination'] = to_part
    
    if not start_room_id and len(room_ids) >= 1:
        start_room_id = room_ids[0]
    if not destination_room_id and len(room_ids) >= 2:
        destination_room_id = room_ids[1]
    elif not destination_room_id and len(room_ids) == 1:
        destination_room_id = room_ids[0]
    
    confidence = 0.0
    if start_room_id and destination_room_id:
        confidence = 1.0
    elif destination_room_id:
        confidence = 0.8
    elif descriptions.get('destination'):
        confidence = 0.6
    
    return {
        'startRoomId': start_room_id,
        'destinationRoomId': destination_room_id,
        'confidence': confidence,
        'raw_room_ids': room_ids,
        'descriptions': descriptions
    }


def validate_room_ids(room_ids: Dict, available_rooms: Dict) -> Tuple[bool, str]:
    """Validate that room IDs exist in available rooms"""
    
    if room_ids.get('startRoomId'):
        if room_ids['startRoomId'] not in available_rooms:
            return False, f"Starting room {room_ids['startRoomId']} not found"
    
    if room_ids.get('destinationRoomId'):
        if room_ids['destinationRoomId'] not in available_rooms:
            return False, f"Destination room {room_ids['destinationRoomId']} not found"
    
    if not room_ids.get('destinationRoomId'):
        return False, "No destination room specified"
    
    return True, ""


def suggest_similar_rooms(room_id: str, available_rooms: Dict, max_suggestions: int = 3) -> List[str]:
    """Suggest similar room IDs for typo correction"""
    from difflib import get_close_matches
    
    suggestions = get_close_matches(
        room_id,
        available_rooms.keys(),
        n=max_suggestions,
        cutoff=0.6
    )
    
    return suggestions


def format_room_info(room_id: str, room_info: Dict) -> str:
    """Format room information for display"""
    room_type = room_info.get('type', 'Room')
    floor = room_info.get('floor', '?')
    building = room_info.get('building', '?')
    
    return f"{room_id} ({room_type.title()} in {building}, Floor {floor})"
```

### Step 3: Integrate with App.jsx

In your `App.jsx`, add the hook and handle navigation responses:

```jsx
import { useChatbotNavigation } from './hooks/useChatbotNavigation';

export default function FanshaweNavigator() {
    const { triggerNavigation, navigationStatus, navigationAvailability } = useChatbotNavigation();
    const [showInteractiveMap, setShowInteractiveMap] = useState(false);
    
    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        const userInput = input;
        setInput('');
        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mensagem: userInput })
            });

            const data = await response.json();

            const botResponse = {
                role: 'assistant',
                content: data.reply || 'Sorry, I couldn\'t process that request.'
            };
            setMessages(prev => [...prev, botResponse]);

            // HANDLE NAVIGATION ACTION
            if (data.navigationAction) {
                console.log('📍 Navigation action received:', data.navigationAction);

                if (!navigationAvailability.interactiveMapLoaded) {
                    console.log('⚠️ Interactive map not loaded, opening now...');
                    setMessages(prev => [...prev, {
                        role: 'system',
                        content: '🗺️ Opening interactive map for navigation...'
                    }]);

                    setShowInteractiveMap(true);

                    // Wait for map to load
                    setTimeout(async () => {
                        await triggerNavigation(data.navigationAction);
                    }, 2000);
                } else {
                    console.log('✅ Interactive map already loaded, triggering navigation...');
                    await triggerNavigation(data.navigationAction);
                }
            }

            // Display navigation status if it exists
            if (navigationStatus?.message) {
                setMessages(prev => [...prev, {
                    role: 'system',
                    content: navigationStatus.message
                }]);
            }

        } catch (error) {
            console.error('Error sending message:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        // ... existing JSX ...
        {navigationStatus && (
            <div className={navigationStatus.success ? 'bg-green-100' : 'bg-red-100'}>
                {navigationStatus.message}
            </div>
        )}
        // ... rest of JSX ...
    );
}
```

### Step 4: Update Backend Chat Handler

In `src/api/app.py`, find the NAVIGATION intent handler and add navigation action extraction:

```python
from src.api.utils.room_id_extraction import parse_navigation_intent, validate_room_ids

# In your /api/chat endpoint, in the NAVIGATION handler:
if intent_type == "NAVIGATION":
    # Extract room IDs from user message
    nav_intent = parse_navigation_intent(user_message, available_rooms)
    
    # Validate room IDs
    is_valid, error = validate_room_ids({
        'startRoomId': nav_intent.get('startRoomId'),
        'destinationRoomId': nav_intent.get('destinationRoomId')
    }, available_rooms)
    
    if not is_valid:
        response_data = {
            'reply': error,
            'navigationAction': None
        }
    else:
        # Build navigation action
        navigation_action = {
            'type': 'objectDeparture' if nav_intent.get('startRoomId') else 'coordDeparture',
            'destinationRoomId': nav_intent['destinationRoomId']
        }
        if nav_intent.get('startRoomId'):
            navigation_action['startRoomId'] = nav_intent['startRoomId']
        
        response_data = {
            'reply': f"Navigating to {nav_intent['destinationRoomId']}...",
            'navigationAction': navigation_action
        }
```

---

## Data Flow Example

### User: "Navigate me from H1015 to H1019"

1. **Backend Processing:**
   - Extract: startRoomId="H1015", destinationRoomId="H1019"
   - Validate: Both rooms exist ✓
   - Response includes `navigationAction` object

2. **Frontend Receives:**
   ```json
   {
     "reply": "Navigating from H1015 to H1019...",
     "navigationAction": {
       "type": "objectDeparture",
       "startRoomId": "H1015",
       "destinationRoomId": "H1019"
     }
   }
   ```

3. **Frontend Processing:**
   - Check if interactive map is loaded
   - If not, open it and wait 2 seconds
   - Call `triggerNavigation()` with navigation data
   - This calls `window.objectDepartureNavigation("H1015", "H1019")`

4. **Result:**
   - Path is drawn on interactive map
   - Navigation status shown to user
   - Turn-by-turn directions available

---

## Navigation Function Interface

Your existing functions in `interactiveMap.html`:

### `objectDepartureNavigation(startRoomId, destinationRoomId)`
- **Use when:** Both start and end rooms are known
- **Returns:** boolean (success)
- **Called by:** Room modal or chatbot-triggered navigation

### `coordDepartureNavigation(destinationRoomId)`
- **Use when:** Only destination is known (user position used)
- **Returns:** boolean (success)
- **Called by:** Chatbot when only destination provided

---

## Testing Checklist

- [ ] Create `navigationService.js` with all functions
- [ ] Create `useChatbotNavigation.js` hook
- [ ] Create `room_id_extraction.py` utility
- [ ] Add hook to `App.jsx`
- [ ] Handle `navigationAction` in chat handler
- [ ] Update backend NAVIGATION handler
- [ ] Test with: "Navigate from H1015 to H1019"
- [ ] Test with: "Take me to the library"
- [ ] Verify map opens automatically
- [ ] Verify path is drawn
- [ ] Verify error handling (invalid rooms)

---

## Key Features

✅ **Room ID Extraction:**
- Regex-based: Finds "H1015", "H1019" in text
- Pattern-based: Parses "from X to Y"
- Natural language: Matches "library" to actual room ID

✅ **Validation:**
- Checks if rooms exist
- Suggests alternatives for typos
- Provides helpful error messages

✅ **Two Navigation Modes:**
- Room-to-room (when start + destination known)
- GPS/Manual-to-room (when only destination known)

✅ **User Feedback:**
- Automatic map opening
- Status messages
- Error handling with suggestions

---

## Error Handling Examples

**Invalid Room:**
```
User: "Navigate to H9999"
Backend: Room not found, suggest similar rooms
Response: "H9999 not found. Did you mean H9015 or H9119?"
```

**Map Not Loaded:**
```
User: Sends navigation request
Map not open yet
System: Opens map automatically, waits for load
Then: Triggers navigation
```

**Missing Destination:**
```
User: "How do I navigate?"
Backend: No destination extracted
Response: "Please specify where you'd like to go"
```

---

## File Structure

```
Frontend_Data/frontend/src/
├── services/
│   └── navigationService.js (NEW)
├── hooks/
│   └── useChatbotNavigation.js (NEW)
├── components/
│   └── App.jsx (MODIFY: Add hook and handle navigationAction)
└── main.jsx

src/api/
├── utils/
│   └── room_id_extraction.py (NEW)
└── app.py (MODIFY: Update NAVIGATION handler)

LeafletJS/
└── interactiveMap.html (NO CHANGES NEEDED - already has functions)
```

---

## For Your Groupmates

**If you're implementing this:**

1. **Frontend person:** Create the two new JS files, add hook to App.jsx
2. **Backend person:** Create Python utility, update chat handler
3. **Testing person:** Test all patterns and error cases
4. **Documentation person:** Document any custom room matching logic

**Key Points:**
- Don't modify existing navigation functions (they're already perfect!)
- The framework is non-invasive - just adds new files
- All three layers must be implemented for it to work
- Start with the simplest test case: "Navigate from H1015 to H1019"

---

## Questions & Troubleshooting

**Q: What if the map doesn't load?**
A: The hook monitors `navigationAvailability.interactiveMapLoaded` every 5 seconds. The chat waits 2 seconds before triggering navigation after opening the map.

**Q: What room IDs should I use?**
A: Use format: Building Letter + 4-digit number (H1015, H1019, M3045, etc.)

**Q: How do I add custom room matching?**
A: Extend the `find_room_id_from_description()` function in `room_id_extraction.py` with more keywords and logic.

**Q: Can I test without full backend?**
A: Yes! Use the example in `ChatbotNavigationExample.jsx` component for reference implementation.

---

## Next Steps

1. Create all three new files
2. Add hook to your existing `App.jsx`
3. Update backend chat handler
4. Test with sample navigation requests
5. Add custom room matching as needed
6. Deploy and iterate

Good luck! 🗺️
