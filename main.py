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
    model = genai.GenerativeModel('gemini-2.5-flash')
except KeyError as e:
    print(e)
    model = None

# Store the map information for the AI model
map_info = '''You are a map navigator for Fanshawe College. Provide step-by-step walking directions based on the information below.
Format your response using simple HTML tags for clarity. For example: use <strong> for emphasis, <ul> and <li> for lists, and <br> for line breaks.

**BUILDING A (A1, A2, A3) - Green Zone**

**General Info:**
- Located in the southeast corner of campus
- Connected to Buildings D (west side) and E (northwest corner)
- Multi-floor building with elevators and multiple stairwells
- Access via Fanshawe College Boulevard

**Floor 1 (A1) - Detailed Room Locations:**

*South Section (Entrance Area):*
- 1001: Large space, southwest corner near main entrance
- 1001-2, 1001-3: Small rooms inside 1001
- 1001-6, 1001-9: Additional subdivisions of 1001

*East Corridor (from south to north):*
- 1004: Southeast corner
- 1005: Just north of 1004
- 1006: Continuing north
- 1007: Mid-east corridor
- 1010: Further north on east side
- 1012: North of 1010
- 1014: Continuing north
- 1016: Upper east corridor
- 1017: Near northeast area
- 1018: Northeast section

*Central and West Areas:*
- 1023: Central area
- 1037: West-central section
- 1048: Northwest area
- 1049: North of 1048
- 1051: Lecture room, northwest section
- 1057: North area, west side
- 1059: Far northwest corner

*Services:*
- Washrooms: Multiple locations including near 1049
- First Nations area: Northwest section
- Continuing Education: North area
- Mechanical Room: North section
- Lounge: Northwest area
- Lecture Hall 1070-C: Upper northwest
- Elevators: 1019-ELEV (central-east), 1033-ELEV (northwest area)
- Stairs: STAIR A1 (1001-S, southwest), STAIR A2 (1063-S, north), STAIR A3 (1015-S, west-central), STAIR A4 (1034-S, central)

**Floor 2 (A2):**

*South Section:*
- 2001-C: Storage/closet, south entrance area
- 2002: South area
- 2003: Southwest corner
- 2004: Southeast corner, near entrance
- 2005: South-central, near 2005-C storage

*East Corridor:*
- 2007: East side, lower section
- 2010: East corridor
- 2011: Mid-east section
- 2013: East side, mid-level
- 2014: Continuing north on east
- 2015: Upper east corridor
- 2016: Near northeast
- 2018: Northeast section

*Central Areas:*
- 2008-C: Storage, central
- 2015-C, 2020-C: Storage areas
- 2019: Central room
- 2020: West-central area
- 2031: West side, mid-level
- 2032-C: Storage, west-central
- 2033: West area
- 2035: West corridor
- 2036: West side, with 2036-C storage
- 2037: West section
- 2038: Northwest area
- 2039: North-central
- 2041: North area
- 2042: North section
- 2043: Northwest
- 2045: Far north

*North Section:*
- 2046: Northeast upper area
- 2049: Northwest, with 2049-C storage
- 2050: North corridor
- 2052: North side
- 2054: Mezzanine level, north
- 2056: Northeast area
- 2057: Far northeast
- 2058: Northeast corner, with 2058-C storage

*Services:*
- Elevators: Same as Floor 1
- Stairs: Same stairwells continuing to Floor 2
- Mezzanine area at 2054

**Floor 3 (A3):**
- Roof level with minimal room access


**BUILDING B (B1) - Orange Zone**

**General Info:**
- Large central building in Orange Zone
- Connected to T Building (south side), C Building (north side), and D Building (east side, Green Zone)
- Main hub for Orange Zone navigation and technical programs

**Detailed Room Locations:**

*West Corridor (from south to north):*
- 1001: Southwest corner, near T Building connection
- 1006: West side, lower section
- 1007: West corridor, south area, with STAIR B4 (1007-S) nearby
- 1009: Continuing north on west side
- 1010: West corridor, mid-section
- 1012: West side, upper area
- 1015: Northwest corridor
- 1016: West side, north section
- 1017: Northwest area

*Central Areas (South to North):*
- 1022: Central-south area
- 1024: Central corridor
- 1026: Mid-central section
- 1027: Central area
- 1028: Central corridor, north of 1027
- 1030: Central section
- 1032: Mid-central, north area
- 1033: Central corridor, upper section

*Specialized Spaces - Central/West:*
- 1012: Machine Shop (west side, mid-corridor)
- 1023-1 area: Welding area (central-west)
- 1010-2: Mechatronics Lab (west side)
- 1020: Automation Lab (west-central area)
- 1033-1, 1032-1: Storage areas near welding section
- 1005, 1005-1: Sheet Metal Shop (southwest area)
- 1004: Reprographics (southwest corner)
- 1043: Computer Lab (north-central)
- 1082: Receiving (far northeast corner)

*East Corridor (from south to north):*
- 1037: East side, lower section
- 1039: East corridor, south area
- 1042: East side, south-central
- 1046: East corridor, with 1046-C storage
- 1048: East side, mid-section
- 1050: East corridor, continuing north
- 1051: East side, upper section
- 1052: East corridor, north area
- 1054: East side, upper corridor
- 1055: Continuing north on east
- 1056: East corridor, far north
- 1057: East side, upper north
- 1058: East corridor, near northeast
- 1059: East side, northeast section
- 1060: East corridor, upper northeast
- 1062: Far east, north section (with 1062-1, 1062-2, 1062-3 subdivisions)
- 1064: Northeast area
- 1067: East side, far north
- 1070: Northeast corridor
- 1071: Far northeast
- 1072: Northeast section
- 1073: Upper northeast area

*Far East Section:*
- 1077: Far east corridor
- 1078: East side, with 1078-ELEV elevator
- 1079: Far east section
- 1082: Far northeast corner (Receiving area)

*Central Feature:*
- James A. Colvin Atrium: Large central open space, mid-building
- Mezzanine level above atrium

*Additional Specialized Spaces:*
- 1011: Lecture room (west-central)
- 1034-1: Storage area
- 1061, 1062-1, 1062-2: Subdivided rooms far east
- 1069: East-central area
- 1075, 1075-1: North-central sections
- Woodworking Shop: Northwest area
- Plumbing/Electrical Shop: North-central
- Lecture rooms: 1011, 1041 (south-central), 1047 (east-central)

*Services:*
- Parking/Lockers: South entrance area
- Security/Lost and Found: South section
- Washrooms: Multiple locations throughout (southwest, northwest, central-east, northeast)
- Elevator: 1078-ELEV (far east side)
- Stairs: STAIR B1 (1065-S, far east), STAIR B2 (1081-S, far northeast), STAIR B3 (1062-S, east side), STAIR B4 (1007-S, west side)
- Stair D1 (1000-S) and Stair D2 (1014-S): East side near D Building connection
- Cage storage: Mid-east area

*Connection Points:*
- South: T Building connection via corridor (southwest area)
- North: C Building via multiple hallways (northwest section)
- East: D Building (Green Zone) via corridors near 1014-S and 1000-S stairs
- Multiple doorways and corridors for cross-building navigation


**BUILDING C (C1) - Orange Zone**

**General Info:**
- Located north of B Building, west of D Building (Green Zone)
- Upper section of Orange Zone
- Smaller building with classroom clusters

**Detailed Room Locations:**

*West Section:*
- 1003: Southwest corner
- 1007: West side, lower section
- 1009: West corridor, continuing north
- 1011: West side, mid-section
- 1013: West corridor, north area

*Central Corridor:*
- 1019: Central-west area
- 1023: Central corridor, mid-section
- 1027: Central area, with 1027-C storage
- 1030: Central corridor, north of 1027
- 1031: Central-north section

*East Section:*
- 1034: East side, lower section
- 1035: East corridor, south area
- 1038: East side, mid-section
- 1039: East corridor, continuing north
- 1042: East side, north area
- 1043: East corridor, with 1043-C storage
- 1044: East side, upper section
- 1046: East corridor, with 1046-C storage
- 1047: East side, far north
- 1052: Northeast area
- 1056: Far northeast corner

*Classroom Cluster (Central-West):*
- 1004-A: First in cluster
- 1004-B: Second room
- 1004-D: Third room
- 1004-E: Fourth room
- 1004-G: Fifth room
- 1004-H: Sixth room
- 1004-J: Last in cluster
- Note: These small classrooms are arranged in a row, west-central area

*Services:*
- Washrooms: South-central and north areas
- Mechanical rooms: North section
- Service areas: Northeast corner
- Elevator: 1000-ELEV (west-central location)
- Stairs: STAIR C2 (1024-S, central area)
- Storage rooms: 1004-C, 1027-C, 1043-C, 1046-C, 1052-C throughout building

*Connection Points:*
- South: B Building via corridors (southwest and southeast connections)
- East: D Building (Green Zone) via east corridor
- Multiple hallway connections for navigation


**BUILDING D (D1, D2, D3) - Green Zone**

**General Info:**
- Large central building in Green Zone - MAIN CAMPUS HUB
- Major crossroads connecting all zones
- Extensive food services and amenities
- Multi-floor structure with green roof on third floor

**Floor 1 (D1) - Detailed Room Locations:**

*Southwest Section (B Building Connection):*
- 1001-C: Storage, southwest corner near B Building
- 1003-C: Storage, south area
- 1004-1: Southwest classroom
- 1007-C: Storage, southwest section

*South-Central Areas:*
- 1010: South corridor, central area
- 1011: South-central section
- 1013: South area, east of center
- 1014-C: Storage, south-central
- 1015: South corridor, continuing east
- 1016: South-central area
- 1018: South section, east area

*Central Corridor (West to East):*
- 1021: Central area, main corridor
- 1024: Mid-central section
- 1026: Central corridor, east of 1024
- 1027: Central area, continuing east
- 1029: Central-east section
- 1031: Central corridor, far east side
- 1032: East-central area

*North-Central Areas:*
- 1035: North-central section
- 1037: North area, with 1037-C storage
- 1039: North-central corridor
- 1041: North section, mid-area
- 1046: North corridor, with 1046-C storage
- 1047: North area, continuing east
- 1048: North-central section

*East Corridor (South to North):*
- 1050: East side, lower section
- 1052: East corridor, continuing north
- 1055: East side, mid-section
- 1057: East corridor, with 1057-C storage
- 1059: East side, north area, with 1059-C storage
- 1060: East corridor, far north
- 1062: Northeast section
- 1065: Far east corridor, with 1065-C storage
- 1069: Northeast area
- 1070: Far east, north section
- 1072: Northeast corner

*Food Services & Amenities (specific locations):*
- The Falcon Shop: South-central area (near main entrance)
- Harvey's: Central-north section
- Pizza Pizza: Adjacent to Harvey's, central-north
- Tim Hortons: South area, east side
- On the Go: East section
- Parking/Lockers office: South area
- Security/Lost and Found: South-central section
- Student Study Space: Multiple locations throughout

*Services & Features:*
- Information Desk: Main entrance area, south-central
- Bike Parking: Exterior, multiple locations
- Bus Stop: South side, exterior
- Washrooms: Southwest corner, south-central, north-central, northeast sections (including accessible)
- Elevator: 1021-ELEV (central corridor)
- Stairs: STAIR D1 (2000-S, south-west), STAIR D2 (2014-S, south-central), STAIR D3 (2032-S, central-east), STAIR D4 (2044-S, north-central), STAIR D5 (2052-S, northeast), STAIR D6 (2055-S, far east)

*Connection Points:*
- West: B Building and C Building (Orange Zone) - southwest and northwest connections
- South: E Building (Green Zone) - south-central area
- Southeast: A Building (Green Zone) - southeast corridor
- North: F Building (Red Zone) - north side, multiple connection points
- North: SUB - north-central area

**Floor 2 (D2):**
- Similar layout to Floor 1 with 2000-series room numbers
- Same general corridor structure
- Classrooms and offices on upper level
- Same stairwell and elevator locations

**Floor 3 (D3):**

*Room Locations:*
- 3000: West side, main room with subdivisions (3000-1, 3000-2, 3000-3)
- 3001: West-central area, with 3001-1, 3001-4, 3001-5 subdivisions
- 3002: West section, with 3002-1, 3002-2, 3002-3 subdivisions
- 3003: West-central room
- 3004: West side, with 3004-1
- 3005: Central-west area
- 3006: Central section
- 3007: Central area
- 3008: Central corridor
- 3009: Central-east section, with 3009-1
- 3011: East-central area, with 3011-1
- 3012: East side, with 3012-1
- 3013: East section
- 3015: East corridor
- 3016: East side, with 3016-1
- 3017: East area
- 3018: East section
- 3019: East corridor
- 3020: East-central area
- 3021: East side
- 3022: East section
- 3023: East corridor
- 3024: Far east area

*Features:*
- Green Roof Sections: Multiple roof sections labeled throughout floor (Sections A, B, and multiple D sections)
- Mechanical/Electrical rooms: Throughout floor (3002-ELEC, 3005-ELEC, 3009-ELEC, 3015-ELEC, 3018-ELEC, 3024-ELEC)
- Stairs: Same as lower floors (3001-S, 3024-S)

**Connection to Other Buildings:**
D Building is the PRIMARY CAMPUS HUB. From D1:
- To B Building (Orange): Walk west through southwest corridor
- To C Building (Orange): Walk west through northwest corridor  
- To A Building (Green): Walk southeast through east corridor
- To E Building (Green): Walk south through south-central area
- To F Building (Red): Walk north through north side
- To SUB (Red): Walk north through north-central area


**BUILDING E (E1) - Green Zone**

**General Info:**
- South of main entrance and F Building (Red Zone)
- Connected to D Building (north), A Building (east), and F Building (northwest)
- Ground floor building with administrative functions

**Detailed Room Locations:**

*Main Entrance Area (Central):*
- 1001-C: Storage closet, central entrance area
- 1002-V: Vestibule, main entrance
- Ramps: Multiple accessibility ramps at entrance

*South Section:*
- 1004: South area, large classroom space with subdivisions (1004-1 through 1004-9)

*East Side:*
- 1012: East section, mid-area
- 1013: East side, north area with subdivisions (1013-1 through 1013-4)

*Central Areas:*
- 1001-C: Storage areas throughout
- 1010-C: Central storage closet
- 1035-C: Storage, north-central area
- 1043-V: Vestibule, north section

*West Section:*
- 1003: West side, lower area
- 1006: West section, mid-area
- 1008: West side, continuing north
- 1010: West area, upper section
- 1011: Northwest corridor
- 1012: West side, north area (near washrooms)
- 1022: West section, far area

*Administrative Areas:*
- Registrar: West-central area (large office space with subdivisions)

*Food Services:*
- Tim Hortons: North-central section (near D Building connection)

*Services:*
- Washrooms: Multiple locations including west side and central areas (including accessible facilities)
- Accessible Shower & Changeroom: West side area
- Elevator: 1009-ELEV (central-east location)
- Stairs: STAIR E1 (1020-S, east side), STAIR E2 (1000-S, west side)
- Ramps: Multiple ramps for accessibility at entrance and throughout
- STAIR D4 (1044-S): Northeast corner, connecting to D Building

*Connection Points:*
- North: D Building (Green Zone) - north side, multiple connection points near Tim Hortons
- Northwest: F Building (Red Zone) - northwest corner connection
- East: A Building (Green Zone) - east side corridor
- Main entrance faces south toward parking areas


**BUILDING F (F1, F2, F3, F4) - Red Zone**

**General Info:**
- Major Red Zone building north of main entrance/D Building
- Central administrative and academic building
- Four floors with extensive classroom and office space
- Connected to D Building (south), E Building (south), H Building (east), and L Building (west)

**Floor 1 (F1) - Detailed Room Locations:**

*West Section:*
- 1000: Far west area
- 1001: West side, lower section
- 1003: West corridor, continuing east
- 1004: West-central area with 1004-C storage and 1004-V vestibule
- 1005: West section, mid-area (subdivisions 1005-1 through 1005-5)
- 1006: West side, office space
- 1007: West corridor with 1007-V vestibule
- 1008: West-central section
- 1010: West area, upper section

*Central South Areas:*
- 1013: Central-south area with 1013-C storage and 1013-V vestibule
- 1018: Central corridor with 1018-C storage
- 1019: Central section with 1019-C storage, 1019-V vestibule, and 1019-1 subdivision
- 1020: Central-south area
- 1022: Central corridor
- 1023: Central section with 1023-C storage, 1023-V vestibule, and 1023-ELEC electrical room
- 1024: Central corridor

*Central North Areas:*
- 1027: Central-north section
- 1028: Central corridor with 1028-C storage
- 1029: Central-north area
- 1030: North-central section
- 1031: Central corridor, continuing north
- 1032: North-central area
- 1033: Central-north section
- 1034: North corridor
- 1036: North-central area

*East Section (South to North):*
- 1037: East side, lower section
- 1042: East corridor with 1042-C storage
- 1043: East section with 1043 subdivisions
- 1045: East corridor with 1045-C storage
- 1046: East side, continuing north
- 1048: East section with 1048-C storage
- 1050: East corridor
- 1053: East side with 1053-C storage
- 1055: East corridor
- 1057: East section
- 1059: East corridor
- 1061: East side with 1061-C storage
- 1064: East section
- 1066: Far east area with 1066-V vestibule and 1066 subdivisions

*Specialized Spaces:*
- Board Room: West side, near 1001-1003 area
- Executive Office: West section, adjacent to Board Room
- Variety Store: East-central area

*Food Services:*
- Multiple food service locations in central areas

*Services:*
- Washrooms: Multiple locations - southwest, northwest, central-east, northeast (including accessible)
- Elevators: Multiple locations throughout building
- Stairs: STAIR F1 (1066-S, far east), STAIR F2 (1023-S, central), STAIR F3 (1042-S, east-central), STAIR F4 (1048-S, east side), STAIR F5 (1045-S, east corridor), STAIR F6 (1027-S, central-north)
- Exit Only: 1019 area has exit-only door

*Connection Points:*
- South: D Building (Green Zone) - south side, multiple connections
- South: E Building (Green Zone) - southwest area
- East: H Building (Blue Zone) - east side connections
- West: L Building - west side corridor
- SUB accessible via connections

**Floor 2 (F2) - Detailed Room Locations:**

*West Section:*
- 2000: West side, main area
- 2001: West corridor with 2001-C storage
- 2002: West section
- 2003: West side with 2003-C storage
- 2004: West corridor
- 2005: West section with 2005-C storage and 2005-ELEC electrical room

*Central Areas:*
- 2010: Central-west area with 2010-C storage
- 2012: Central corridor
- 2013: Central section
- 2014: Central area
- 2015: Central corridor with 2015-C storage
- 2016: Central-south section
- 2018: Central area with 2018-C storage
- 2020: Central corridor
- 2021: Central section (subdivisions 2021-1 through 2021-6)
- 2023: Central-north area with 2023-S stairs
- 2024: Central section with 2024-C storage
- 2025: Central corridor with 2025-C storage
- 2028: Central-north area
- 2031: North-central section with 2031-C storage

*East Section:*
- 2034: East side, lower section
- 2035: East corridor
- 2036: East section
- 2037: East side, upper area
- 2038: East corridor
- 2039: East section with 2039-C storage
- 2041: East side
- 2042: East corridor (subdivisions 2042-1, 2042-2)
- 2045: East section
- 2047: East corridor with 2047-C storage
- 2049: East side
- 2053: East section
- 2055: East corridor
- 2056: East area
- 2057: East side
- 2059: East section
- 2060: East corridor with 2060-C storage
- 2061: East area
- 2063: East side
- 2064: East section
- 2065: East corridor
- 2067: East area
- 2068: East side
- 2069: East section

*Features:*
- Open to Below: Multiple sections (around 2042 area and other locations) where floor opens to first floor
- Electrical Room: 2048-ELEC (east side)

*Services:*
- Stairs: Same stairwells as F1 continuing to Floor 2
- Elevators: Same locations as Floor 1
- Washrooms: Multiple locations throughout floor

*Connection Points:*
- Same as Floor 1 to adjacent buildings (D, E, H, L)

**Floor 3 (F3) - Detailed Room Locations:**

*West Section:*
- 3001: West side with subdivisions (3001-1 through 3001-ELEV)
- 3003: West corridor (subdivisions 3003-1 through 3003-19)
- 3004: West section
- 3005: West side with 3005-2 subdivision and 3005-ELEV
- 3006: West corridor with 3006-C storage (subdivisions 3006-1 through 3006-8, plus 3006-9 through 3006-19)
- 3009: West area

*Central Areas:*
- 3011: Central section (subdivisions 3011-1, 3011-2, 3011-3)
- 3013: Central corridor
- 3016: Central area
- 3018: Central section
- 3020: Central corridor
- 3021: Central area with 3021-C storage

*East Section:*
- 3038: East side
- 3039: East corridor with 3039-C storage
- 3040: East section
- 3042: East area with 3042-C storage

*Features:*
- Open to Below: Central area (opens down to F2)

*Services:*
- Stairs: STAIR F1 (3066-S, east), STAIR F3 (3042-S, east), STAIR F4 (3048-S, east), STAIR L2 (3001-S, west)
- Elevators: 3001-ELEV (west), 3005-ELEV (west)
- Washrooms: Multiple locations

*Connection Points:*
- Same buildings as lower floors (D, E, H, L)

**Floor 4 (F4) - Detailed Room Locations:**

*Limited Room Access:*
- 4001: West area with 4001-ELEV
- 4003: West side with 4003-1 subdivision
- 4013: Section with 4013-1
- 4005-ELEV: East area

*Services:*
- Stairs: STAIR F1 (4066-S, east), STAIR F4 (4048-S, east), STAIR L2 (4001-S, west)
- Elevators: 4001-ELEV (west), 4005-ELEV (east)

*Connection Points:*
- L Building connection on west side


**BUILDING G (G1) - Yellow Zone**

**General Info:**
- East of SUB (Red Zone)
- Connected to K Building (Blue Zone, north) and Residence 1 (R1)
- Single floor building

**Detailed Room Locations:**

*West Section:*
- 1001: Southwest corner, near SUB connection
- 1002: West side, continuing east

*Central Area:*
- 1008: Central section

*East Section:*
- 1013: East side, lower area
- 1014: East section, continuing north
- 1015: Northeast area

*Specialized Spaces:*
- The Falcon Shop: Located in building (specific location in central/west area)
- Board Room: West section (1001 area)
- Executive Office: Near Board Room

*Services:*
- Washrooms: Central area (including accessible)
- Stairs: STAIR G3 (1000-S, central location)
- Storage: 1000-C (central area), 1004-C, 1004-V vestibule

*Connection Points:*
- West: SUB (Red Zone) - west side entrance
- North: K Building (Blue Zone) - north corridor
- East: Residence 1 (R1) connection
- Variety store area near east section


**BUILDING H (H1) - Blue Zone**

**General Info:**
- North of M Building, south of K Building
- Connected to F Building (Red Zone) to the west
- Administrative and food services building

**Detailed Room Locations:**

*South Entrance Area:*
- 1003: South side, near entrance
- 1004: Southeast area with 1004-C storage and 1004-V vestibule
- 1005: South section, continuing north
- 1006: South corridor
- 1007: South side, upper area

*West Section (Food Services Area):*
- 1010: West side, lower section
- 1011: West corridor
- 1012: West section, mid-area
- 1013: West side (cafeteria servery area)
- 1014: West corridor, continuing north
- 1015: West section, north area
- 1016: West side, far north
- 1017: Northwest corridor
- 1018: Northwest section with 1018-C storage

*Central Areas:*
- 1019: Central corridor with 1019-ELEV and 1019-S stairs
- 1021: Central-east section with 1021-C storage and 1021-S stairs
- 1022: Central area
- 1023: Central-east section
- 1024: Central corridor
- 1026: Central area with 1026-C storage
- 1027: Central-north section
- 1028: North-central area
- 1029: North corridor
- 1030: North-central section
- 1031: North area
- 1032: North-central corridor
- 1033: Northeast section
- 1034: Northeast area

*Specialized Spaces:*
- Cafeteria: West side, large space (around 1010-1013 area) with Servery
- Board Room: North-central area
- Executive Office: Adjacent to Board Room
- President's Office: North section (administrative area)
- Gallery: Central area (display space)

*Food Services:*
- Harvey's: West-central section (cafeteria area)
- Pizza Pizza: Adjacent to Harvey's, west-central

*Security:*
- Security/Lost and Found: South-central area (near entrance)

*Services:*
- Washrooms: South area (near 1003), central-west section, north area (including accessible)
- Elevator: 1019-ELEV (central corridor)
- Stairs: STAIR H1 (1019-S, central), STAIR H2 (1021-S, central-east), STAIR H3 (1000-S, west side connecting to G Building)
- Storage: 1002-C, 1004-C, 1018-C, 1021-C, 1026-C throughout building

*Connection Points:*
- West: F Building (Red Zone) - west side, multiple connection points
- South: M Building (Blue Zone) - south side corridor
- North: K Building (Blue Zone) - north corridor


**BUILDING J (J1) - Yellow Zone**

**General Info:**
- Main Yellow Zone building on west side of campus core
- Connected to SUB (Red Zone) to the east and SC Building (Yellow Zone) to the north
- Administrative and classroom building

**Detailed Room Locations:**

*South Section:*
- 1003: Southwest corner
- 1004: South area, east of 1003

*West Corridor:*
- 1012: West side, lower section
- 1013: West corridor, continuing north
- 1014: West side, mid-area
- 1015: West corridor, upper section
- 1016: West side, north area

*East Section:*
- 1019: East side, lower area
- 1022: East corridor, mid-section
- 1023: East side, continuing north
- 1024: East corridor, upper area
- 1025: East side, north section
- 1029: Northeast area
- 1032: Far east section

*Security:*
- Security/Lost and Found: South area (near entrance)

*Services:*
- Washrooms: Multiple locations including south and north areas (including accessible)
- Elevator: Central location
- Storage rooms throughout

*Connection Points:*
- East: SUB (Red Zone) - east side entrance
- North: SC Building (Yellow Zone) - north corridor


**BUILDING K - Blue Zone**

**General Info:**
- Northwest area of Blue Zone
- Connected to H Building (south), M Building (southeast), and G Building (east, Yellow Zone)
- Administrative and classroom building

**Connection Points:**
- South: H Building - south corridor
- Southeast: M Building - southeast hallway
- East: G Building (Yellow Zone) - east side connection


**BUILDING L (L1, L2) - Red Zone**

**General Info:**
- Part of SUB complex, west side
- Connected to F Building (east side)
- Two floors with study and meeting spaces

**Floor 1 (L1) - Detailed Room Locations:**

*West Section:*
- 1000: West area, main space
- 1001: West side, lower section
- 1005: West corridor, continuing east
- 1007: West section with 1007-V vestibule
- 1011: West-central area

*Central Areas:*
- 1013: Central section with 1013-S stairs
- 1018: Central corridor with 1018-C storage
- 1020: Central-east area
- 1022: Central section
- 1024: Central corridor

*East Section (F Building Connection):*
- 1048: East side, lower area
- 1050: East corridor, continuing north
- 1053: East section
- 1055: East corridor
- 1057: East side, upper area
- 1058: East section with 1058-C storage
- 1059: East corridor
- 1061: East area with 1061-C storage

*SUB Connection:*
- SUB1012-3: Connection area to Student Union Building (west side)

*Services:*
- Washrooms: Multiple locations (including accessible)
- Storage: 1000-C, 1018-C, 1058-C, 1061-C throughout
- Stairs: STAIR L1 (1013-S, central area)
- Elevator: Central location

*Connection Points:*
- East: F Building (Red Zone) - east side, multiple connection points
- West: SUB complex - west corridor

**Floor 2 (L2) - Detailed Room Locations:**

*West Section:*
- 2005: West side with 2005-C storage and 2005-ELEC electrical room
- 2010: West corridor with 2010-C storage
- 2012: West-central area
- 2013: West section with 2013-C storage and 2013-S stairs

*Central and East Areas:*
- 2016: Central area
- 2018: Central corridor with 2018-C storage
- 2020: Central-east section
- 2021: East area
- 2056: Far east section
- 2060: East corridor with 2060-C storage
- 2061: East area
- 2063: East section
- 2064: East corridor
- 2065: East area
- 2067: East section
- 2068: East corridor
- 2069: Far east area

*Features:*
- Open to Below: Central area (opens down to L1)

*Services:*
- Stairs: STAIR L1 (2013-S, west side), STAIR F1 (2066-S, east side)
- Elevator: Same as Floor 1
- Washrooms: Multiple locations

*Connection Points:*
- East: F Building Floor 2 - east side connections
- West: SUB upper level


**BUILDING M (M1) - Blue Zone**

**General Info:**
- Located between Applied Arts Lane (west) and Campus Drive (east)
- Main entrance on south side near Rooms 1004 and 1006
- Accessible entrances on south and east sides
- Technical and classroom building

**Detailed Room Locations:**

*South Entrance Area:*
- 1002: South side, main entrance area with 1002-ELEV
- 1003: Southwest corner, just inside entrance
- 1004: Southeast corner, right at entrance
- 1005: South area, east of entrance
- 1006: South side, at main entrance (east side)

*West Corridor:*
- 1010: West side, lower section
- 1018: West corridor, mid-area
- 1019: West side, continuing north
- 1023: West corridor, upper section
- 1025: West side, north area
- 1027: West corridor, far north
- 1029: Northwest section
- 1030: West side, upper north

*Central Areas:*
- 1001-C: Storage, central entrance area
- 1007-C: Storage, central section
- 1011-C: Storage, central corridor
- 1015-C: Storage, west-central area
- 1021-C: Storage, central area
- 1032-C: Storage, north-central

*East and North Sections:*
- 1033: Northeast corner, main office area
- 1035: North-central section
- 1037: North area, east side
- 1040: North-central corridor
- 1041: North section (subdivisions 1041, 1041-2)
- 1045: Northeast area (subdivision 1045-1)
- 1049: Far north section

*Specialized Spaces:*
- Generator Room: North-central area (around 1010 region)

*Services:*
- Washrooms: South area (near entrance), north area (near stairs)
- Elevator: 1002-ELEV (south entrance area)
- Stairs: STAIR M1 (1000-S, south-central), STAIR M2 (1021-S, central corridor), STAIR M3 (1042-S, north-central)
- Storage: 1001-C, 1001-V vestibule, 1007-C, 1011-C, 1015-C, 1021-C, 1032-C, 1042-C throughout
- Mechanical areas: North section

*Parking Access:*
- Lot 2 (Assigned Parking): East side of building
- P3 Meters: South-east area

*Connection Points:*
- West: H Building (Blue Zone) via connecting hallway between rooms (mid-building, west side)
- North: K Building (Blue Zone) - north corridor
- Hallway to H Building: Located on west side, mid-building level


**BUILDING SC (SC1) - Yellow Zone**

**General Info:**
- Just north of and connected to J Building (Yellow Zone)
- Student services and retail building

**Detailed Room Locations:**

*Main Areas:*
- 1001: South section, main entrance from J Building
- 1012: Central area
- 1014: North section

*Amenities:*
- The Falcon Shop: Central area (retail space)
- Tim Hortons: North section (food services)

*Services:*
- Washrooms: Multiple locations (including accessible)
- Storage areas throughout

*Connection Points:*
- South: J Building (Yellow Zone) - south entrance/corridor


**SUB (Student Union Building) - Red Zone**

**General Info:**
- Central student services building
- Major hub connecting multiple zones
- Student activities, services, and food court area
- Connected to D Building (Green Zone), F Building, L Building, J Building (Yellow Zone), and G Building (Yellow Zone)

**Main Features:**
- Student services offices
- Meeting rooms
- Food court area
- Lounge spaces
- Activity areas

*Connection Points:*
- South: D Building (Green Zone) - south side, multiple entrances
- East: F Building (Red Zone) - east corridor
- East: L Building (Red Zone) - east side connection
- West: J Building (Yellow Zone) - west entrance
- Southeast: G Building (Yellow Zone) - southeast corridor
- Multiple hallways and corridors connecting all adjacent buildings


**BUILDING T (T1, T2) - Orange Zone**

**General Info:**
- Southern edge of campus on Oxford Street
- West of B Building (Orange Zone)
- Two floors with classrooms

**Floor 1 (T1) - Detailed Room Locations:**

*South Section (Oxford Street Side):*
- 1002: South area, near entrance
- 1003: Southwest corner
- 1004: South side, continuing east
- 1005: South-central area
- 1006: South section, east side

*North Corridor:*
- 1009: North-west area
- 1019: North-central section
- 1023: North corridor, mid-area
- 1027: North side, continuing east
- 1028: Northeast area

*Specialized Spaces:*
- 1007T: Technical room
- Lecture rooms: 1023 area
- Woodworking shop reference: Northwest section
- Plumbing/Electrical shop areas

*Services:*
- Washrooms: Multiple locations (including accessible)
- Elevator: 1017-ELEV (central corridor)
- Stairs: STAIR T1 (1017-S, central), STAIR T2 (1028-S, east side), STAIR T3 (1026-S, central-east)
- Storage: 1001-C, 1002-C, 1003-C, 1004-C, 1023-C, 1027-C, 1028-C throughout

*Connection Points:*
- North: B Building (Orange Zone) - north side corridor (multiple connection points)
- Main entrance: South side, Oxford Street

**Floor 2 (T2) - Detailed Room Locations:**

*Main Areas:*
- 2001: South area with 2001-C storage
- 2002: South-central section with 2002-C storage
- 2003: South side with 2003-C storage
- 2004: South-central area with 2004-C storage
- 2006: South-east section
- 2007: Central area
- 2009: Central-west section
- 2011: Central corridor
- 2013: Central area
- 2015: Central-north section
- 2017: North area
- 2021: North-central section
- 2023: Far north area
- 2027-C: Storage, north section
- 2028: Northeast area with 2028-C storage

*Features:*
- Open to Below: Multiple sections where floor opens to T1 level

*Services:*
- Stairs: Same stairwells as T1 continuing to Floor 2
- Elevator: 1017-ELEV continues to Floor 2
- Washrooms: Multiple locations

*Connection Points:*
- North: B Building Floor 2 - north side connections


**NAVIGATION TIPS:**

**Zone Colors and Main Connections:**
- **Green Zone (A, D, E)**: Southeast campus - D Building is the main hub
  - A Building: Southeastern corner, classrooms and First Nations area
  - D Building: CENTRAL CAMPUS HUB - connects to ALL zones
  - E Building: South of D, Registrar and Tim Hortons

- **Orange Zone (B, C, T)**: Southwest campus - technical programs
  - B Building: Large central hub with Machine Shop, Welding, Automation Lab
  - C Building: North of B, classroom clusters
  - T Building: South edge on Oxford Street, connects north to B

- **Red Zone (F, L, SUB)**: Central/north campus - administration and student services
  - F Building: Major 4-floor building, administrative offices, connects ALL adjacent zones
  - L Building: West side, study spaces, connects to F and SUB
  - SUB: Student Union Building, central hub for student services

- **Yellow Zone (G, J, SC)**: West campus
  - G Building: East of SUB, Falcon Shop, connects to K and Residence
  - J Building: West side, connects east to SUB, north to SC
  - SC Building: North of J, Falcon Shop and Tim Hortons

- **Blue Zone (H, K, M)**: North/northeast campus
  - H Building: Cafeteria, Harvey's, Pizza Pizza, administrative offices
  - K Building: North area, connects H, M, and G
  - M Building: East side between Applied Arts Lane and Campus Drive

**Major Crossroads:**
- **D Building (D1)**: PRIMARY CAMPUS HUB
  - Connects Green Zone (A, E) ↔ Orange Zone (B, C) ↔ Red Zone (F, SUB)
  - Main entrance area with Tim Hortons, The Falcon Shop, food services
  - Information desk, bus stop, bike parking

- **F Building (F1-F4)**: CENTRAL RED ZONE HUB
  - Connects Red Zone ↔ Green Zone (D, E) ↔ Blue Zone (H)
  - Administrative offices, 4 floors of classrooms
  - West connection to L Building

- **SUB (Student Union Building)**: STUDENT SERVICES HUB
  - Connects Red Zone (F, L) ↔ Yellow Zone (J, G) ↔ Green Zone (D)
  - Central meeting point for students

- **B Building (B1)**: ORANGE ZONE HUB
  - Connects T Building (south) ↔ C Building (north) ↔ D Building (east to Green Zone)
  - Technical programs: Machine Shop (1012), Welding, Automation Lab (1020), Mechatronics

**Accessibility Features:**
- All buildings have accessible washrooms
- Elevators in all multi-floor buildings
- Ramps at key entrance points (especially E Building)
- Accessible showers and changerooms: A Building, E Building
- Wide corridors for wheelchair access

**Finding Specific Rooms:**
- **First digit(s) = floor number**: 1xxx = Floor 1, 2xxx = Floor 2, 3xxx = Floor 3, 4xxx = Floor 4
- **Grey areas on maps = walkable corridors** (hallways you can walk through)
- **White areas on maps = rooms** (enclosed spaces, not corridors)
- **-C suffix = Closet/Storage** (e.g., 1001-C)
- **-V suffix = Vestibule** (e.g., 1002-V)
- **-S suffix = Stairwell** (e.g., 1000-S is STAIR designation)
- **-ELEV suffix = Elevator** (e.g., 1019-ELEV)
- **-ELEC suffix = Electrical Room** (e.g., 1023-ELEC)

**Specialized Spaces by Building:**

*Technical/Vocational (B Building):*
- Machine Shop: Room 1012 (west side, mid-corridor)
- Automation Lab: Room 1020 (west-central area)
- Welding Area: Room 1023-1 area (central-west)
- Mechatronics Lab: Room 1010-2 (west side)
- Sheet Metal Shop: Rooms 1005, 1005-1 (southwest area)
- Woodworking Shop: Northwest area
- Computer Lab: Room 1043 (north-central)
- Reprographics: Room 1004 (southwest corner)
- Receiving: Room 1082 (far northeast corner)

*Food Services:*
- Tim Hortons: D Building (south area), E Building (north-central), SC Building (north section)
- Harvey's: D Building (central-north), H Building (west-central cafeteria area)
- Pizza Pizza: D Building (central-north), H Building (cafeteria area)
- The Falcon Shop: D Building (south-central), G Building (central/west), SC Building (central)
- On the Go: D Building (east section)
- Cafeterias: H Building (large cafeteria west side with servery), B Building (James A. Colvin Atrium area)

*Administrative Offices:*
- Registrar: E Building (west-central area, large office space)
- Security/Lost and Found: D Building (south-central), B Building (south entrance), H Building (south-central), J Building (south area)
- President's Office: H Building (north section)
- Board Rooms: F Building (west side), G Building (1001 area), H Building (north-central)
- Executive Offices: F Building (west section), G Building (near Board Room), H Building (adjacent to Board Room)

*Student Services:*
- Parking/Lockers: D Building (south area), B Building (south entrance)
- Information Desk: D Building (main entrance, south-central)
- Student Study Space: D Building (multiple locations throughout)
- SUB: Central location, all student services

**Example Detailed Directions:**

**From M Building Main Entrance (M1, Room 1004) to D Building Tim Hortons (D1):**
1. Enter M Building through the south entrance (Rooms 1004/1006 area)
2. Walk north through the main corridor (you'll pass rooms 1010, 1018, 1019 on your left)
3. Continue north past room 1023 on the left
4. Look for the connecting hallway on your left (west side) - this is between the central corridor area
5. Take the connecting hallway west into H Building (Blue Zone)
6. You'll enter H Building on the east side
7. Walk west through H Building's main corridor
8. Continue west until you reach F Building (Red Zone) connection
9. Enter F Building and walk south through the corridors
10. Continue south until you reach D Building (Green Zone)
11. Enter D Building from the north side
12. Once in D Building, head toward the south/east area
13. Tim Hortons is located in the south-east section of D Building first floor
14. Total walking time: approximately 8-10 minutes

**From A Building Main Entrance (A1, Room 1001) to B Building Machine Shop (B1, Room 1012):**
1. Enter A Building at the south entrance (Room 1001 area)
2. Walk west through the main corridor
3. Look for the connection to D Building on your left (west side)
4. Enter D Building (Green Zone) from the east
5. Walk west through D Building's corridors (you'll pass through the central area with food services)
6. Continue west until you reach the B Building connection
7. Enter B Building (Orange Zone) from the east side
8. Walk west along the main corridor
9. The Machine Shop (Room 1012) is on your left (west side), mid-corridor
10. Total walking time: approximately 6-8 minutes

**From Main Campus Entrance (D Building South Entrance) to H Building Cafeteria:**
1. Enter D Building from the south main entrance
2. Walk north through the central corridor (you'll pass The Falcon Shop, Harvey's, Pizza Pizza)
3. Continue north to the far end of D Building
4. Enter F Building (Red Zone) from D Building's north side
5. Walk east through F Building corridors
6. Look for the connection to H Building on your right (east side)
7. Enter H Building (Blue Zone) from the west
8. The Cafeteria is on your left (west side) - large space with servery
9. Harvey's and Pizza Pizza are located within the cafeteria area
10. Total walking time: approximately 5-7 minutes

**From T Building Oxford Street Entrance (T1) to SC Building Tim Hortons (SC1):**
1. Enter T Building from Oxford Street (south entrance)
2. Walk north through T Building corridors
3. Enter B Building (Orange Zone) from T Building's north connection
4. Walk north and then west through B Building (you'll pass the James A. Colvin Atrium)
5. Continue northwest until you reach C Building connection
6. Enter C Building and walk north
7. Exit C Building heading north/west toward D Building
8. Enter D Building and head north toward F Building/SUB area
9. Enter SUB (Red Zone) from D Building's north side
10. Walk west through SUB
11. Enter J Building (Yellow Zone) from SUB's west side
12. Walk north through J Building corridors
13. Enter SC Building from J Building's north connection
14. Tim Hortons is in the north section of SC Building
15. Total walking time: approximately 10-15 minutes

**Emergency Exits and Stairwells:**
- All buildings have multiple emergency exits marked on floor plans
- Stairwells are labeled (e.g., STAIR A1, STAIR B2, STAIR D3, etc.)
- Elevators should not be used during emergencies
- Follow grey corridor areas to nearest exits

**Accessibility Routes:**
- Use elevators for floor-to-floor movement
- Ramps available at main entrances (especially E Building, D Building)
- All buildings have accessible washrooms (marked on maps)
- Wide corridors throughout campus for wheelchair access
- Accessible showers/changerooms: A Building (northeast area), E Building (west side)

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
