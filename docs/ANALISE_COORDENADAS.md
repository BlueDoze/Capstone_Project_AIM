# 🗺️ ANÁLISE: INCOMPATIBILIDADE DE COORDENADAS SVG vs APLICAÇÃO

## ❓ PROBLEMA RELATADO

Você seleciona coordenadas no `find_room_centers.html` mas elas **NÃO** mantêm a mesma posição quando inseridas no `config/building_m_rooms.json` e visualizadas na aplicação.

---

## 🔍 INVESTIGAÇÃO TÉCNICA - ACHADO IMPORTANTE!

### 1. **Coordenadas no find_room_centers.html**

```javascript
// find_room_centers.html - Linhas 324-333
function handleSvgClick(event) {
    const svg = event.currentTarget;
    const pt = svg.createSVGPoint();
    pt.x = event.clientX;
    pt.y = event.clientY;

    // Transform to SVG coordinate system
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    const x = Math.round(svgP.x * 100) / 100;
    const y = Math.round(svgP.y * 100) / 100;
}
```

**O que faz:** Captura a posição do clique e transforma em **coordenadas SVG puras** (0-1000 range aprox)

---

### 2. **Coordenadas na Aplicação (map-controller.js)**

```javascript
// map-controller.js - Linhas 196-206
const svgPath = '/LeafletJS/Floorplans/Building%20M/M1_official.svg?ts=' + new Date().getTime();

fetch(svgPath)
    .then(r => r.text())
    .then(svgText => {
        const svgDoc = new DOMParser().parseFromString(svgText, 'image/svg+xml');
        currentSvgMap = svgDoc.documentElement;

        // Calculate corners for SVG overlay
        const corners = [
            L.latLng(bounds.getNorth(), bounds.getWest()),   // top-left
            L.latLng(bounds.getNorth(), bounds.getEast()),   // top-right
            L.latLng(bounds.getSouth(), bounds.getEast()),   // bottom-right
            L.latLng(bounds.getSouth(), bounds.getWest())    // bottom-left
        ];

        // 🔴 IMPORTANTE: Aplica rotação de 21.3 graus!
        const mapBearing = 21.3;
        currentCorners = corners.map(corner => rotatePoint(corner, center, mapBearing));
```

---

## 🚨 PROBLEMA RAIZ IDENTIFICADO

### **✅ AMBOS usam M1_official.svg - MAS há TRANSFORMAÇÕES DIFERENTES!**

#### Em `find_room_centers.html`:
- Carrega: `M1_official.svg`
- Captura: **SVG puro SEM transformação**
- Coordenadas: X, Y diretas do SVG

#### Em `map-controller.js`:
- Carrega: **Mesmo M1_official.svg**
- MAS aplica: **Rotação de 21.3 graus** aos corners
- Usa: **Bilinear interpolation** com corners rotacionados
- RESULTADO: Coordenadas diferem porque os corners estão ROTACIONADOS!

---

## 📊 FLUXO DE COORDENADAS - O PROBLEMA

```
┌─────────────────────────────────────────────────────────────┐
│ find_room_centers.html                                      │
│ • Abre: M1_official.svg                                     │
│ • Você clica no ponto do room                               │
│ • Captura: X=250.5, Y=600.3 (SVG puro, SEM rotação)        │
│ • Armazena em building_m_rooms.json                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Você copia as coordenadas
                 │ "Room_1003": { "x": 250.5, "y": 600.3 }
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ map-controller.js (getRoomCenterFromSVG)                    │
│ • Lê: manualRoomCenters[roomId] = {x: 250.5, y: 600.3}     │
│ • Carrega: M1_official.svg (MESMO arquivo)                  │
│ • Obtém: viewBox do SVG                                     │
│ • Normaliza: normX = (250.5 - x) / width                    │
│ • Aplica: Bilinear interpolation com corners ROTACIONADOS   │
│ • 🔴 PROBLEMA: corners estão em 21.3° mas X,Y não!          │
│ • Resultado: LatLng DIFERENTE do esperado ❌                 │
└─────────────────────────────────────────────────────────────┘

Analogia: É como copiar uma nota de um mapa girado 21.3 graus
e tentar usá-la em um mapa não girado. A posição fica errada!
```

---

## ✅ SOLUÇÃO DEFINITIVA

### **O Problema: Rotação de 21.3 graus NÃO é aplicada no find_room_centers.html**

A aplicação **rotaciona os corners em 21.3 graus** para alinhar o mapa com o norte geográfico. Quando você captura coordenadas em `find_room_centers.html` **SEM essa rotação**, elas não correspondem ao sistema de coordenadas rotacionado da aplicação.

### **Opção 1: Corrigir find_room_centers.html para aplicar a rotação** ⭐ RECOMENDADO

Modifique `find_room_centers.html` para aplicar a mesma transformação:

```javascript
// Adicionar esta função (antes de handleSvgClick)
function rotatePoint(x, y, centerX, centerY, angleDeg) {
    const angleRad = (angleDeg * Math.PI) / 180;
    const cos = Math.cos(angleRad);
    const sin = Math.sin(angleRad);

    const dx = x - centerX;
    const dy = y - centerY;

    return {
        x: centerX + (dx * cos - dy * sin),
        y: centerY + (dx * cos + dy * sin)
    };
}

// Modificar handleSvgClick para aplicar rotação
function handleSvgClick(event) {
    if (!selectedRoom) {
        showStatus('⚠️ Please select a room first!', 'error');
        return;
    }

    const svg = event.currentTarget;
    const pt = svg.createSVGPoint();
    pt.x = event.clientX;
    pt.y = event.clientY;

    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    // 🔴 APPLY THE SAME 21.3 DEGREE ROTATION AS THE APPLICATION
    const svgBBox = svg.viewBox.baseVal || {
        x: 0, y: 0,
        width: svg.width.baseVal.value,
        height: svg.height.baseVal.value
    };

    const centerX = svgBBox.x + svgBBox.width / 2;
    const centerY = svgBBox.y + svgBBox.height / 2;

    const rotatedPoint = rotatePoint(svgP.x, svgP.y, centerX, centerY, 21.3);

    const x = Math.round(rotatedPoint.x * 100) / 100;
    const y = Math.round(rotatedPoint.y * 100) / 100;

    // Store coordinates
    allRoomCoordinates[selectedRoom] = { x, y };

    // Display coordinates
    document.getElementById('svgCoords').textContent = `X: ${x}, Y: ${y} (ROTATED 21.3°)`;

    // ... resto do código ...
}
```

### **Opção 2: Usar sem rotação e aplicar manualmente** (Alternativa)

Se preferir usar coordenadas SEM rotação, aplique manualmente no `building_m_rooms.json`:

1. Capture as coordenadas em `find_room_centers.html` (sem rotação)
2. Use uma ferramenta online para rotacionar as coordenadas
3. Ou faça a conta manualmente

**Fórmula de Rotação:**
```
x' = centerX + (x - centerX) * cos(θ) - (y - centerY) * sin(θ)
y' = centerY + (x - centerX) * sin(θ) + (y - centerY) * cos(θ)

Onde:
- θ = 21.3 graus = 0.371 radianos
- (centerX, centerY) = centro do SVG viewBox
```

---

## 🔧 VERIFICAÇÃO PASSO-A-PASSO

### 1. **Identifique qual SVG a aplicação usa:**

```bash
# Abrir a aplicação em http://localhost:8081
# F12 (Developer Tools) → Console
# Procurar por mensagens como "Loading SVG" ou logs relacionados
```

### 2. **Compare viewBox dos arquivos:**

```bash
# Ver viewBox do M1_official.svg
grep "viewBox" LeafletJS/Floorplans/Building\ M/M1_official.svg

# Ver viewBox do M1.svg
grep "viewBox" LeafletJS/Floorplans/Building\ M/M1.svg

# Ver outros possíveis arquivos
ls -la LeafletJS/Floorplans/Building\ M/
```

### 3. **Verificar tamanho/dimensões:**

```bash
# Comparar dimensões dos arquivos
wc -l LeafletJS/Floorplans/Building\ M/M1*.svg
```

---

## 📋 POSSÍVEIS CAUSAS

| Causa | Impacto | Solução |
|-------|--------|--------|
| ViewBox diferente | Normalização errada | Usar mesmo SVG |
| Escala diferente | Coordenadas escaladas | Recalcular proporção |
| Rotação aplicada | Coordenadas rotacionadas | Aplicar transformação |
| Versões diferentes | Elementos em posições distintas | Usar versão única |

---

## 💡 RECOMENDAÇÃO

### **Passo 1: Achar qual SVG a aplicação usa**

Adicionar log em `map-controller.js` para identificar:

```javascript
// Em map-controller.js, função loadBuildingM()
async function loadBuildingM() {
    // ... código existente ...

    try {
        const response = await fetch('/LeafletJS/Floorplans/Building M/M1.svg');
        const svgText = await response.text();
        const svg = new DOMParser().parseFromString(svgText, 'image/svg+xml').querySelector('svg');

        // 🔍 LOG CRÍTICO
        console.log('🔍 SVG LOADED DETAILS:', {
            url: '/LeafletJS/Floorplans/Building M/M1.svg',
            viewBox: svg.getAttribute('viewBox'),
            width: svg.getAttribute('width'),
            height: svg.getAttribute('height')
        });
```

### **Passo 2: Atualizar find_room_centers.html**

Modifique a linha 245 para usar o MESMO arquivo:

```javascript
// Usar o mesmo arquivo que a aplicação
const response = await fetch('../LeafletJS/Floorplans/Building M/M1.svg');
```

### **Passo 3: Testar novamente**

1. Abrir `find_room_centers.html`
2. Selecionar uma sala
3. Clicar no centro
4. Copiar as coordenadas
5. Colar em `config/building_m_rooms.json`
6. Verificar se a posição está correta na aplicação

---

## 🧪 TESTE DIAGNÓSTICO

Para confirmar o problema:

```javascript
// No console do navegador, enquanto em find_room_centers.html
fetch('../LeafletJS/Floorplans/Building M/M1.svg')
    .then(r => r.text())
    .then(svg => {
        const parsed = new DOMParser().parseFromString(svg, 'image/svg+xml');
        const svgEl = parsed.querySelector('svg');
        console.log('ViewBox:', svgEl.getAttribute('viewBox'));
        console.log('Width:', svgEl.getAttribute('width'));
        console.log('Height:', svgEl.getAttribute('height'));
    });
```

Repita isso para os diferentes arquivos SVG para comparar.

---

## 📌 RESUMO

| Aspecto | Status |
|--------|--------|
| Problema | ✅ Identificado: SVG diferente |
| Causa | ❌ find_room_centers.html usa M1_official.svg |
| | ❌ aplicação usa M1.svg (provavelmente) |
| Solução | ✅ Unificar para usar o mesmo arquivo |
| Prioridade | 🔴 ALTA - Coordenadas críticas para navegação |

---

**Próximo passo:** Abra a aplicação, verifique qual SVG está sendo carregado, e nos avise qual é o nome exato. Daí farei a correção permanente no `find_room_centers.html`.

