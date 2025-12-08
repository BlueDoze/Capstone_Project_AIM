import json

with open('data/map_data/predios_info_english.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

buildings = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'SC', 'SUB', 'T', 'Y', 'Z']

print("=" * 80)
print("BUILDING FACILITIES SUMMARY")
print("=" * 80)

for b in buildings:
    if b in data and 'facilities' in data[b]:
        facilities = data[b].get('facilities', [])
        name = data[b].get('name', 'Unknown')
        print(f"\n{b}: {name}")
        print(f"   Facilities Count: {len(facilities)}")
        print(f"   Facilities: {', '.join(facilities[:5])}")
        if len(facilities) > 5:
            print(f"              {', '.join(facilities[5:])}")
    else:
        print(f"\n{b}: NO FACILITIES FOUND")

print("\n" + "=" * 80)
print(f"TOTAL: {sum(1 for b in buildings if b in data and 'facilities' in data[b])} buildings have facilities")
print("=" * 80)
