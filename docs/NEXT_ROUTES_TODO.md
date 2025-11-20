# 📋 Lista de Próximas Rotas a Adicionar - Building M

**Data:** 17 de Novembro, 2025  
**Cobertura Atual:** 38.1% (8 de 21 nós conectados)  
**Rotas Existentes:** 7  
**Rotas Faltando:** ~27-30 rotas

---

## 📊 Status Atual

### ✅ Rotas Já Criadas (7)
1. ✅ **M1_1_M1_2** - Entrada principal do H Building (ENTRADA)
2. ✅ **M1_2_M1_3** - Corredor das escadas para Room 1006
3. ✅ **M1_3_M1_Int_1** - Room 1006 para intersecção principal
4. ✅ **M1_Int_1_M1_4** - Intersecção para Room 1004
5. ✅ **M1_4_M1_5** - Room 1004 para Elevador
6. ✅ **M1_5_M1_6** - Elevador para Room 1003
7. ✅ **M1_6_M1_7** - Room 1003 para Exit 1 (SAÍDA)

---

## 🎯 PRÓXIMAS 5 ROTAS (Prioridade ALTA)

### PATH 2: Área de Banheiros

#### 1. **M1_Int_1_M1_Turn_1** 🔴 URGENTE
- **Início:** M1_Int_1 (já existe)
- **Fim:** M1_Turn_1 (novo nó)
- **Descrição:** Intersecção T no corredor principal
- **Importância:** Conecta à área de banheiros e Room 1018
- **Metadados sugeridos:**
  ```json
  {
    "description": "Main corridor T-intersection to bathroom area",
    "connectsTo": ["M1_Int_1", "M1_Turn_1"],
    "keywords": ["intersection", "bathrooms", "study room"]
  }
  ```

#### 2. **M1_Turn_1_M1_8** 🔴 URGENTE
- **Início:** M1_Turn_1 (criado na rota #1)
- **Fim:** M1_8 (Room 1018)
- **Descrição:** Corredor para Room 1018 - Study Room
- **Importância:** Sala de estudo com tráfego alto
- **Metadados sugeridos:**
  ```json
  {
    "description": "Corridor to Room 1018 (Study Room)",
    "connectsTo": ["Room_1018", "M1_Turn_1"],
    "keywords": ["room 1018", "study room", "estudos"]
  }
  ```

#### 3. **M1_8_M1_9** 🔴 URGENTE
- **Início:** M1_8 (Room 1018)
- **Fim:** M1_9 (Banheiro Masculino)
- **Descrição:** Corredor para o banheiro masculino
- **Importância:** Instalação essencial
- **Metadados sugeridos:**
  ```json
  {
    "description": "Corridor to Men's Restroom",
    "connectsTo": ["Room_1018", "Bathroom-Men"],
    "keywords": ["bathroom", "men", "restroom", "banheiro masculino"]
  }
  ```

#### 4. **M1_9_M1_10** 🔴 URGENTE
- **Início:** M1_9 (Banheiro Masculino)
- **Fim:** M1_10 (Banheiro Acessível)
- **Descrição:** Entre banheiros
- **Importância:** Conecta banheiros acessíveis
- **Metadados sugeridos:**
  ```json
  {
    "description": "Corridor between bathrooms",
    "connectsTo": ["Bathroom-Men", "Bathroom-Accessible"],
    "keywords": ["bathroom", "accessible", "acessível"],
    "accessibility": "wheelchair"
  }
  ```

#### 5. **M1_10_M1_11** 🔴 URGENTE
- **Início:** M1_10 (Banheiro Acessível)
- **Fim:** M1_11 (Banheiro Feminino)
- **Descrição:** Para o banheiro feminino
- **Importância:** Completa a área de banheiros
- **Metadados sugeridos:**
  ```json
  {
    "description": "Corridor to Women's Restroom",
    "connectsTo": ["Bathroom-Accessible", "Bathroom-Women"],
    "keywords": ["bathroom", "women", "restroom", "banheiro feminino"]
  }
  ```

---

## 🗺️ PRÓXIMAS 10 ROTAS (Prioridade MÉDIA-ALTA)

### PATH 3: Ala Norte (Classrooms)

#### 6. **M1_Int_1_M1_Int_2** 🟡
- **Início:** M1_Int_1
- **Fim:** M1_Int_2 (nova intersecção)
- **Descrição:** Segunda intersecção principal
- **Conecta:** Ala norte com salas de aula

#### 7. **M1_Int_2_M1_12** 🟡
- **Fim:** M1_12 (Room 1033 - Classroom)
- **Importância:** Sala de aula com alto tráfego

#### 8. **M1_12_M1_Turn_2** 🟡
- **Fim:** M1_Turn_2 (curva + Room 1045)
- **Descrição:** Curva no corredor

#### 9. **M1_Turn_2_M1_13** 🟡
- **Fim:** M1_13 (Stairs_2 + Exit_3)
- **Importância:** Escadas e saída norte

### PATH 4: Ala Oeste (Labs & Offices)

#### 10. **M1_Int_2_M1_14** 🟢
- **Fim:** M1_14 (Room 1035 - Office)

#### 11. **M1_14_M1_15** 🟢
- **Fim:** M1_15 (Room 1037 - Meeting Room)

#### 12. **M1_15_M1_16** 🟢
- **Fim:** M1_16 (Room 1030 + Room 1041 - Labs)
- **Nota:** Nó compartilhado por 2 salas

#### 13. **M1_16_M1_Turn_3** 🟢
- **Fim:** M1_Turn_3 (curva)

#### 14. **M1_Turn_3_M1_17** 🟢
- **Fim:** M1_17 (Room 1040 - Workshop)

#### 15. **M1_17_M1_18** 🟢
- **Fim:** M1_18 (Room 1049 - Resource Center)

---

## 📍 Salas Sem Rotas (Total: 17)

### 🔴 Alta Prioridade
- Room_1018 (M1_8) - Study Room
- Room_1033 (M1_12) - Classroom
- Room_1049 (M1_18) - Resource Center
- Bathroom-Men (M1_9)
- Bathroom-Women (M1_11)
- Bathroom-Accessible (M1_10)

### 🟡 Média Prioridade
- Room_1030 (M1_16) - Lab
- Room_1035 (M1_14) - Office
- Room_1037 (M1_15) - Meeting Room
- Room_1040 (M1_17) - Workshop
- Room_1041 (M1_16) - Lab
- Room_1045 (M1_Turn_2) - Studio

### 🟢 Baixa Prioridade
- H-Building (H_entry) - Já tem entrada via M1_1
- Outside-Exit_3 (M1_13) - North Exit
- Outside-Exit_4 (M1_19) - West Exit
- Stairs_2 (M1_13)
- Stairs_3 (M1_19)

---

## 🛠️ Como Adicionar Novas Rotas

### 1. Obter Coordenadas
```bash
# Abra a ferramenta de coordenadas
open tools/find_room_centers_no_rotation.html
```
- Clique no mapa para traçar a rota
- Copie as coordenadas geradas

### 2. Template de Rota
```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-81.1986xxxx, 43.0141xxxx],
      [-81.1985xxxx, 43.0141xxxx]
    ]
  },
  "properties": {
    "name": "M1_X_M1_Y",
    "segmentType": "corridor",
    "startNode": "M1_X",
    "endNode": "M1_Y",
    "description": "DESCRIPTION",
    "connectsTo": ["Room_XXXX", "Location"],
    "keywords": ["keyword1", "keyword2"],
    "pointCount": 2,
    "length": 0.0,
    "timestamp": "2025-11-17T..."
  }
}
```

### 3. Adicionar ao GeoJSON
Edite: `map/corridor_segments_building_m.geojson`

### 4. Validar
```bash
python3 diagnose_routes.py
python3 check_map_routes.py
```

### 5. Visualizar
```bash
python3 generate_route_viewer.py
./open_route_viewer.sh
```

---

## 📈 Meta de Cobertura

### Cobertura Atual: 38.1% (8/21 nós)

**Após próximas 5 rotas:** ~62% (13/21 nós)  
**Após próximas 10 rotas:** ~86% (18/21 nós)  
**Para 100%:** Adicionar ~25-30 rotas totais

---

## 💡 Dicas

1. **Priorize áreas de alto tráfego**: Banheiros, salas de estudo, classrooms
2. **Siga a sequência lógica**: Complete um PATH antes de começar outro
3. **Adicione metadados ricos**: Description, keywords, connectsTo
4. **Marque entradas/saídas**: Use `isEntrance: true` ou `isExit: true`
5. **Teste sempre**: Use o visualizador para verificar as rotas

---

## 📞 Comandos Úteis

```bash
# Ver lista de rotas
python3 list_routes.py

# Análise detalhada
python3 check_map_routes.py

# Sugerir próximas rotas
python3 suggest_next_routes.py

# Visualizar no mapa
python3 generate_route_viewer.py && ./open_route_viewer.sh

# Diagnosticar problemas
python3 diagnose_routes.py

# Testar busca de entrada
python3 test_entrance_search.py
```

---

**Atualizado:** 17 Nov 2025  
**Próxima Revisão:** Após adicionar as 5 primeiras rotas
