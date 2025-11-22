#!/usr/bin/env python3
"""
Template Generator for New Routes with Full Metadata
Generates ready-to-use GeoJSON route templates
"""

def generate_route_templates():
    """Generate templates for the next 5 priority routes"""
    
    templates = [
        {
            "name": "M1_Int_1_M1_Turn_1",
            "startNode": "M1_Int_1",
            "endNode": "M1_Turn_1",
            "description": "Main corridor T-intersection to bathroom area",
            "connectsTo": ["M1_Int_1", "M1_Turn_1"],
            "keywords": ["intersection", "t-junction", "bathrooms", "study room"],
            "note": "This intersection splits the main corridor to the bathroom area"
        },
        {
            "name": "M1_Turn_1_M1_8",
            "startNode": "M1_Turn_1",
            "endNode": "M1_8",
            "description": "Corridor to Room 1018 (Study Room)",
            "connectsTo": ["M1_Turn_1", "Room_1018"],
            "keywords": ["room 1018", "study room", "sala de estudos", "1018"],
            "note": "Connects to the study room - high traffic area"
        },
        {
            "name": "M1_8_M1_9",
            "startNode": "M1_8",
            "endNode": "M1_9",
            "description": "Corridor from Room 1018 to Men's Restroom",
            "connectsTo": ["Room_1018", "Bathroom-Men"],
            "keywords": ["bathroom", "men", "restroom", "banheiro masculino", "wc"],
            "accessibility": "wheelchair",
            "note": "Essential facility - men's bathroom"
        },
        {
            "name": "M1_9_M1_10",
            "startNode": "M1_9",
            "endNode": "M1_10",
            "description": "Corridor between Men's and Accessible Restrooms",
            "connectsTo": ["Bathroom-Men", "Bathroom-Accessible"],
            "keywords": ["bathroom", "accessible", "acessível", "wheelchair", "cadeira de rodas"],
            "accessibility": "wheelchair",
            "note": "Connects accessible bathroom facilities"
        },
        {
            "name": "M1_10_M1_11",
            "startNode": "M1_10",
            "endNode": "M1_11",
            "description": "Corridor from Accessible to Women's Restroom",
            "connectsTo": ["Bathroom-Accessible", "Bathroom-Women"],
            "keywords": ["bathroom", "women", "restroom", "banheiro feminino", "wc"],
            "accessibility": "wheelchair",
            "note": "Completes bathroom area connections"
        }
    ]
    
    print("=" * 80)
    print("📋 ROUTE TEMPLATES WITH FULL METADATA - NEXT 5 ROUTES")
    print("=" * 80)
    
    for i, template in enumerate(templates, 1):
        print(f"\n{'=' * 80}")
        print(f"ROUTE {i}: {template['name']}")
        print(f"{'=' * 80}")
        
        # Generate full GeoJSON template
        geojson_template = f'''{{
  "type": "Feature",
  "geometry": {{
    "type": "LineString",
    "coordinates": [
      [
        -81.198XXXXX,
        43.0141XXXX
      ],
      [
        -81.198XXXXX,
        43.0141XXXX
      ]
    ]
  }},
  "properties": {{
    "name": "{template['name']}",
    "segmentType": "corridor",
    "startNode": "{template['startNode']}",
    "endNode": "{template['endNode']}",
    "description": "{template['description']}",
    "connectsTo": {template['connectsTo']},
    "keywords": {template['keywords']},'''
        
        # Add accessibility if present
        if 'accessibility' in template:
            geojson_template += f'''
    "accessibility": "{template['accessibility']}",'''
        
        # Add remaining fields
        geojson_template += '''
    "pointCount": 2,
    "length": 0.0,
    "timestamp": "2025-11-17T20:00:00.000Z"
  }
}'''
        
        print("\n📝 COPY THIS TO corridor_segments_building_m.geojson:")
        print("\n```json")
        print(geojson_template)
        print("```")
        
        print(f"\n💡 NOTE: {template['note']}")
        print(f"\n⚠️  TODO:")
        print(f"   1. Use find_room_centers_no_rotation.html to get coordinates")
        print(f"   2. Replace -81.198XXXXX and 43.0141XXXX with real coordinates")
        print(f"   3. Calculate actual length if possible")
        print(f"   4. Update timestamp to current time")

def print_metadata_checklist():
    """Print a checklist of metadata to include"""
    
    print("\n" + "=" * 80)
    print("✅ METADATA CHECKLIST - What to Include in Each Route")
    print("=" * 80)
    
    checklist = {
        "🔴 OBRIGATÓRIO (Required)": [
            ("name", "Nome único da rota (ex: M1_8_M1_9)"),
            ("segmentType", "Sempre 'corridor' para corredores"),
            ("startNode", "Nó de início (ex: M1_8)"),
            ("endNode", "Nó de fim (ex: M1_9)"),
            ("pointCount", "Número de pontos de coordenadas"),
            ("coordinates", "Array de coordenadas [longitude, latitude]"),
        ],
        "🟡 RECOMENDADO (Recommended)": [
            ("description", "Descrição clara em português/inglês"),
            ("connectsTo", "Array de locais conectados"),
            ("keywords", "Array de palavras-chave para busca"),
            ("length", "Comprimento em metros (pode ser 0.0 inicial)"),
            ("timestamp", "Data/hora de criação"),
        ],
        "🟢 OPCIONAL (Optional)": [
            ("isEntrance", "true se for entrada principal"),
            ("isExit", "true se for saída"),
            ("entranceType", "'main', 'secondary', etc"),
            ("exitNumber", "Número da saída (1, 2, 3...)"),
            ("building", "Prédio conectado (ex: 'H')"),
            ("accessibility", "'wheelchair' se acessível"),
            ("floor", "Andar (ex: 1, 2, 3)"),
            ("note", "Notas adicionais"),
        ]
    }
    
    for category, items in checklist.items():
        print(f"\n{category}")
        for field, description in items:
            print(f"   • {field:20s} → {description}")

def print_keyword_suggestions():
    """Print suggestions for keywords by room type"""
    
    print("\n" + "=" * 80)
    print("🏷️  KEYWORD SUGGESTIONS BY ROOM TYPE")
    print("=" * 80)
    
    suggestions = {
        "Bathrooms/Banheiros": [
            "bathroom", "restroom", "wc", "toilet",
            "banheiro", "lavabo", "sanitário",
            "men", "women", "accessible",
            "masculino", "feminino", "acessível"
        ],
        "Study Areas": [
            "study", "library", "quiet", "reading",
            "estudos", "biblioteca", "silêncio", "leitura"
        ],
        "Classrooms": [
            "classroom", "lecture", "teaching", "class",
            "sala de aula", "aula", "ensino"
        ],
        "Labs": [
            "lab", "laboratory", "experiment", "research",
            "laboratório", "experimento", "pesquisa"
        ],
        "Offices": [
            "office", "staff", "administration", "desk",
            "escritório", "administração", "mesa"
        ],
        "Entrances/Exits": [
            "entrance", "exit", "door", "access",
            "entrada", "saída", "porta", "acesso",
            "main", "principal", "secondary", "secundária"
        ],
        "Stairs/Elevators": [
            "stairs", "elevator", "lift", "escalator",
            "escada", "elevador", "subir", "descer"
        ]
    }
    
    for category, keywords in suggestions.items():
        print(f"\n{category}:")
        print(f"   {', '.join(keywords)}")

def main():
    print("=" * 80)
    print("🎯 ROUTE METADATA TEMPLATE GENERATOR")
    print("=" * 80)
    
    generate_route_templates()
    print_metadata_checklist()
    print_keyword_suggestions()
    
    print("\n" + "=" * 80)
    print("💡 DICAS IMPORTANTES")
    print("=" * 80)
    print("""
1. ✅ SEMPRE inclua description, connectsTo e keywords
   → Facilita busca pelo chatbot
   → Melhora navegação

2. 🎯 Keywords em PORTUGUÊS e INGLÊS
   → Usuários podem buscar em qualquer idioma
   → Ex: ["bathroom", "banheiro", "wc"]

3. ♿ Marque acessibilidade quando aplicável
   → "accessibility": "wheelchair"
   → Importante para usuários com necessidades especiais

4. 🏷️  Use nomes descritivos
   → "Corridor to Room 1018 (Study Room)" 
   → Não: "Corridor"

5. 🔗 connectsTo deve ter AMBOS os lados
   → ["Room_1018", "Bathroom-Men"]
   → Facilita navegação bidirecional

6. 📍 Priorize rotas de alto tráfego
   → Banheiros, entradas, salas de estudo
   → Adicione mais keywords nessas rotas
""")
    
    print("\n" + "=" * 80)
    print("📂 ARQUIVOS PARA EDITAR")
    print("=" * 80)
    print("""
1. Adicionar rotas:
   → map/corridor_segments_building_m.geojson
   
2. Testar/validar:
   → python3 diagnose_routes.py
   → python3 check_map_routes.py
   
3. Visualizar:
   → python3 generate_route_viewer.py
   → ./open_route_viewer.sh
""")

if __name__ == "__main__":
    main()
