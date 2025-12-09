#!/usr/bin/env python3
"""Fix the updateUserLocation function to use floor selector value"""

file_path = r"c:\Users\Lukeg\Desktop\Capstone Virtual Environment\Capstone_Project_AIM\LeafletJS\interactiveMapUpdate.html"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the malformed replacement
old_text = """                    // Use the current floor from the floor selector`r`n                    const floorSelector = document.getElementById('floor-selector');`r`n                    userFloor = floorSelector ? floorSelector.value : "1";"""

new_text = """                    // Use the current floor from the floor selector
                    const floorSelector = document.getElementById('floor-selector');
                    userFloor = floorSelector ? floorSelector.value : "1";"""

content = content.replace(old_text, new_text)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed floor detection in updateUserLocation()")
