# 🗺️ Route Visualization Tool

Ferramenta para visualizar rotas do mapa do Building M de forma interativa.

## 📁 Arquivos

- **`visualize_routes.html`** - Visualizador interativo de rotas no mapa
- **`../check_map_routes.py`** - Script Python para análise detalhada de rotas
- **`../list_routes.py`** - Script Python para listagem simples de rotas

## 🚀 Como Usar

### Visualização Interativa (HTML)

1. Abra o arquivo `visualize_routes.html` em um navegador web
2. O mapa será carregado automaticamente com todas as rotas
3. Use os botões para filtrar por tipo de rota:
   - **Todas** - Mostra todas as rotas
   - **Entradas** - Mostra apenas rotas de entrada
   - **Saídas** - Mostra apenas rotas de saída
   - **Normais** - Mostra apenas corredores normais

### Funcionalidades

#### Mapa Interativo
- **Zoom/Pan**: Use mouse/trackpad para navegar
- **Clique nas rotas**: Ver detalhes em popup
- **Marcadores**: Círculos mostram início/fim de cada rota

#### Painel Lateral
- **Estatísticas**: Total de rotas, entradas, saídas e nós
- **Lista de Rotas**: Clique em qualquer rota para destacá-la no mapa
- **Cores**:
  - 🟢 Verde: Entrada principal
  - 🔴 Vermelho: Saída
  - 🔵 Azul: Corredor normal
  - 🟡 Amarelo: Rota destacada

### Scripts Python

#### Análise Detalhada
```bash
python3 check_map_routes.py
```

Mostra:
- Todas as rotas com coordenadas completas
- Nós conectados
- Keywords associadas
- Comparação entre arquivos GeoJSON
- Estatísticas detalhadas

#### Listagem Simples
```bash
python3 list_routes.py
```

Mostra:
- Lista simplificada de rotas
- Nome e conexões
- Marcadores especiais (entrada/saída)

## 📊 Estrutura dos Dados

### Arquivo GeoJSON Principal
`map/corridor_segments_building_m.geojson`

Cada rota contém:
```json
{
  "properties": {
    "name": "M1_1_M1_2",
    "segmentType": "corridor",
    "startNode": "M1_1",
    "endNode": "M1_2",
    "description": "Main entrance corridor from H Building",
    "connectsTo": ["H-Building", "Stairs_1"],
    "isEntrance": true,
    "building": "H",
    "keywords": ["entrance", "h building"],
    "length": 4.17,
    "pointCount": 2
  }
}
```

### Campos Importantes

- **`name`**: Identificador único da rota
- **`startNode`/`endNode`**: Nós de início e fim
- **`description`**: Descrição legível da rota
- **`connectsTo`**: Lista de locais conectados
- **`isEntrance`**: Marca rota como entrada
- **`isExit`**: Marca rota como saída
- **`keywords`**: Palavras-chave para busca
- **`length`**: Comprimento em metros

## 🔧 Adicionar Novas Rotas

1. Edite `map/corridor_segments_building_m.geojson`
2. Adicione um novo feature com as propriedades necessárias
3. Inclua metadados descritivos:
   - `description` - Descrição clara
   - `keywords` - Palavras-chave para busca
   - `connectsTo` - Locais conectados
   - `isEntrance`/`isExit` - Se aplicável

Exemplo:
```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-81.1986, 43.0141],
      [-81.1985, 43.0141]
    ]
  },
  "properties": {
    "name": "M1_X_M1_Y",
    "segmentType": "corridor",
    "startNode": "M1_X",
    "endNode": "M1_Y",
    "description": "Corridor from X to Y",
    "keywords": ["room X", "area Y"],
    "pointCount": 2,
    "length": 5.0
  }
}
```

## 🎯 Para Identificar Entradas

Para que o chatbot encontre entradas corretamente:

1. **Adicione no GeoJSON**:
   ```json
   "isEntrance": true,
   "entranceType": "main",
   "building": "H",
   "keywords": ["entrance", "h building", "main entrance"]
   ```

2. **Adicione aliases no config**:
   Edite `config/building_m_rooms.json`:
   ```json
   "aliases": {
     "entrance": "H-Building",
     "main entrance": "H-Building",
     "h building": "H-Building"
   }
   ```

3. **Adicione coordenadas SVG**:
   ```json
   "roomCentersSVG": {
     "H-Building": {
       "x": 704,
       "y": 850
     }
   }
   ```

## 📝 Notas

- As coordenadas são em formato GeoJSON: `[longitude, latitude]`
- O mapa usa projeção Web Mercator (EPSG:3857)
- Comprimentos são calculados em metros
- Use zoom level 19-21 para melhor visualização do Building M

## 🐛 Troubleshooting

**Mapa não carrega:**
- Verifique se o arquivo GeoJSON está no caminho correto
- Abra o console do navegador (F12) para ver erros

**Rotas não aparecem:**
- Verifique se as coordenadas estão no formato correto
- Confirme que o GeoJSON é válido (use jsonlint.com)

**Entrada não é encontrada pelo chatbot:**
- Verifique se tem alias no `building_m_rooms.json`
- Confirme que o `roomToNode` mapeia corretamente
- Adicione keywords no GeoJSON
