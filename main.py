import os
import google.generativeai as genai
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_url_path='/static', static_folder='static')

# Configure the generative AI model
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise KeyError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except KeyError as e:
    print(e)
    model = None

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

@app.route("/")
def index():
    return send_file('src/index.html')

@app.route("/chat", methods=['POST'])
def chat():
    if model is None:
        return jsonify({"reply": "The AI model is not configured. Please set the GEMINI_API_KEY environment variable."}), 500

    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Please provide a message."}), 400

    # Combine the map info with the user's message
    prompt = f'{map_info}\n\nUser: {user_message}\nAI:'

    try:
        # Generate a response from the AI model
        response = model.generate_content(prompt)
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": f"An error occurred: {e}"}), 500

def main():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    main()
