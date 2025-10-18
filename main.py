import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

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

# Store the map information for the AI model
map_info = '''You are a map navigator for Fanshawe College. Provide step-by-step walking directions based on the information below.
Format your response using simple HTML tags for clarity. For example: use <strong> for emphasis, <ul> and <li> for lists, and <br> for line breaks.

**M1 Blue Building**

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

**D1 Green Building**

*   **General Info:** Located at the corner of Technology Drive and Colborne Court. Main entrance is on Colborne Court. Accessible entrances on the north and west sides. Adjacent to buildings B and F.
*   **Key Rooms:** 1004-1, 1010, 1011, 1013, 1015, 1016, 1018, 1021, 1024, 1026, 1027, 1029, 1031, 1032, 1035, 1037, 1039, 1041, 1046, 1047, 1048, 1050, 1052, 1055, 1057, 1059, 1060, 1062, 1065, 1069, 1070, 1072.
*   **Amenities:** The Falcon Shop, Parking/Lockers, Security/Lost and Found, Harvey's, Pizza Pizza, Student Study Space, Tim Hortons, On the Go.
*   **Services:** Washrooms (including accessible), Elevator, Information, Bike Parking, Bus Stop.

**E1 Green Building**

*   **General Info:** Adjacent to buildings D, F, and A.
*   **Key Rooms:** 1004, 1012, 1013.
*   **Amenities:** Tim Hortons.
*   **Services:** Washrooms (including accessible), Elevator, Accessible Shower & Changeroom.

**A1 Green Building**

*   **General Info:** Located on London Lane. Adjacent to building D. Near Lot B (Assigned Parking).
*   **Key Rooms:** 1001, 1001-2, 1001-3, 1001-6, 1001-9, 1004, 1005, 1006, 1007, 1010, 1012, 1014, 1016, 1017, 1018, 1023, 1037, 1048, 1049, 1051, 1057, 1059.
*   **Services:** Washrooms (including accessible), Elevator, Accessible Shower & Changeroom.

**J1 Yellow Building**

*   **General Info:** Located on Student Road and Residence Circle. Adjacent to buildings R2, R1, G, and SUB (L is under construction). Near Lot 14 (Assigned Parking).
*   **Key Rooms:** 1003, 1004, 1012, 1013, 1014, 1015, 1016, 1019, 1022, 1023, 1024, 1025, 1029, 1032.
*   **Amenities:** Security/Lost and Found.
*   **Services:** Washrooms (including accessible), Elevator.

**SC1 Yellow Building**

*   **General Info:** Located on Student Road and Residence Circle. Adjacent to building J.
*   **Key Rooms:** 1001, 1012, 1014.
*   **Amenities:** The Falcon Shop, Tim Hortons.
*   **Services:** Washrooms (including accessible).

**C1 Orange Building**

*   **General Info:** Located on Alumni Road and Technology Drive. Adjacent to buildings J, D, and B. Near Lot 1, Lot 2, Lot 3, and Lot 4 (Assigned Parking).
*   **Key Rooms:** 1003, 1004-A, 1004-D, 1004-E, 1004-F, 1004-G, 1004-H, 1004-J, 1007, 1009, 1011, 1013, 1019, 1023, 1027, 1030, 1031, 1034, 1035, 1038, 1039, 1042, 1043, 1044, 1046, 1047, 1052, 1056.
*   **Services:** Washrooms (including accessible), Elevator.

**T1 Orange Building**

*   **General Info:** Located on London Lane and Apprentice Drive. Adjacent to building B. Near Oxford Street.
*   **Key Rooms:** 1002, 1003, 1004, 1005, 1006, 1009, 1019, 1023, 1027, 1028.
*   **Services:** Washrooms (including accessible).

**B1 Orange Building**

*   **General Info:** Located on Technology Drive, Apprentice Drive, London Lane, and Oxford Street. Adjacent to buildings C and D. Near Colborne Court.
*   **Key Rooms:** 1001, 1006, 1007, 1009, 1010, 1012, 1015, 1016, 1017, 1022, 1024, 1026, 1027, 1028, 1030, 1032, 1033, 1037, 1039, 1042, 1046, 1048, 1050, 1051, 1052, 1054, 1055, 1056, 1057, 1058, 1059, 1060, 1062, 1064, 1067, 1070, 1071, 1072, 1073, 1077, 1078, 1079, 1082.
*   **Amenities:** Parking/Lockers, Security/Lost and Found.
*   **Services:** Washrooms (including accessible), Elevator.

**G1 Yellow Building**

*   **General Info:** Located on Residence Circle. Adjacent to building R1.
*   **Key Rooms:** 1001, 1002, 1008, 1013, 1014, 1015.
*   **Amenities:** The Falcon Shop.
*   **Services:** Washrooms (including accessible).

**H1 Blue Building**

*   **General Info:** Located on Applied Arts Lane. Building F is under construction to the west.
*   **Key Rooms:** 1004, 1005, 1006, 1007, 1014, 1016, 1022, 1032, 1033, 1034.
*   **Amenities:** Security/Lost and Found, Harvey's, Pizza Pizza.
*   **Services:** Washrooms (including accessible), Elevator.
'''

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

    # Combine the map info with the user's message
    prompt = f'{map_info}\n\nUser: {user_message}\nAI:'

    try:
        # Generate a response from the AI model
        response = model.generate_content(prompt)
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Error generating content: {e}") # Added for debugging
        return jsonify({"reply": f"An error occurred: {e}"}), 500

def main():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081)))


if __name__ == "__main__":
    main()
