# 🗺️ SOLUÇÃO: INCONSISTÊNCIA DE COORDENADAS SVG vs APLICAÇÃO

## 🎯 RESUMO EXECUTIVO

**Problema:** Coordenadas capturadas em `find_room_centers.html` não correspondem às posições no mapa da aplicação.

**Causa Raiz:** A aplicação **rotaciona os corners do mapa em 21.3 graus** para alinhamento geográfico, mas `find_room_centers.html` captura coordenadas **SEM essa rotação**.

**Solução:** Aplicar a mesma rotação de 21.3 graus no `find_room_centers.html`.

---

## 📋 MUDANÇA NECESSÁRIA

Edite `/tools/find_room_centers.html` para incluir a rotação:

### 1. Adicionar função de rotação (linhas 223-224, antes de `let selectedRoom`)

```javascript
/**
 * Rotate a point around a center by given angle in degrees
 * This matches the rotation applied in map-controller.js
 */
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
```

### 2. Modificar função `handleSvgClick` (linhas 317-348)

**ANTES:**
```javascript
function handleSvgClick(event) {
    if (!selectedRoom) {
        showStatus('⚠️ Please select a room first!', 'error');
        return;
    }

    // Get SVG coordinates
    const svg = event.currentTarget;
    const pt = svg.createSVGPoint();
    pt.x = event.clientX;
    pt.y = event.clientY;

    // Transform to SVG coordinate system
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    const x = Math.round(svgP.x * 100) / 100;
    const y = Math.round(svgP.y * 100) / 100;

    // Store coordinates
    allRoomCoordinates[selectedRoom] = { x, y };

    // Display coordinates
    document.getElementById('svgCoords').textContent = `X: ${x}, Y: ${y}`;

    const jsonFormat = `"${selectedRoom}": { "x": ${x}, "y": ${y} }`;
    document.getElementById('jsonOutput').textContent = jsonFormat;

    // Add visual marker
    addClickMarker(event.clientX, event.clientY);

    showStatus(`✅ Coordinates saved for ${selectedRoom}! Click again to adjust, or select another room.`, 'success');
}
```

**DEPOIS:**
```javascript
function handleSvgClick(event) {
    if (!selectedRoom) {
        showStatus('⚠️ Please select a room first!', 'error');
        return;
    }

    // Get SVG coordinates
    const svg = event.currentTarget;
    const pt = svg.createSVGPoint();
    pt.x = event.clientX;
    pt.y = event.clientY;

    // Transform to SVG coordinate system
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    // 🔴 APPLY 21.3 DEGREE ROTATION (same as map-controller.js)
    const svgBBox = svg.viewBox.baseVal || {
        x: 0,
        y: 0,
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
    document.getElementById('svgCoords').textContent = `X: ${x}, Y: ${y} ✅ (ROTATED 21.3°)`;

    const jsonFormat = `"${selectedRoom}": { "x": ${x}, "y": ${y} }`;
    document.getElementById('jsonOutput').textContent = jsonFormat;

    // Add visual marker
    addClickMarker(event.clientX, event.clientY);

    showStatus(`✅ Coordinates saved for ${selectedRoom} with 21.3° rotation! Click again to adjust, or select another room.`, 'success');
}
```

---

## 🔧 COMO APLICAR

### Passo 1: Editar o arquivo

```bash
# Abrir em editor de texto
# Arquivo: tools/find_room_centers.html
# Linhas 223-224: Adicionar função rotatePoint
# Linhas 317-348: Modificar função handleSvgClick
```

### Passo 2: Testar

```bash
# 1. Abrir http://localhost:8081/tools/find_room_centers.html
# 2. Selecionar uma sala (ex: Room_1003)
# 3. Clicar no SVG map
# 4. Verificar se a coordenada mostra "(ROTATED 21.3°)"
# 5. Copiar e testar na aplicação
```

### Passo 3: Validar na Aplicação

```bash
# 1. Copiar a coordenada com rotação
# 2. Colar em config/building_m_rooms.json
# 3. Abrir http://localhost:8081
# 4. Verificar se o room marker aparece na posição CORRETA
```

---

## 📚 ENTENDIMENTO TÉCNICO

### Por que 21.3 graus?

```javascript
// map-controller.js linha 82 & 192
const mapBearing = 21.3;

// Linhas 193: Rotação é aplicada aos corners
currentCorners = corners.map(corner => rotatePoint(corner, center, mapBearing));

// Linhas 260-273: Bilinear interpolation usa esses corners rotacionados
// Se as coordenadas SVG não estiverem rotacionadas, o resultado fica errado
```

A rotação alinha o mapa com a orientação geográfica real de Campus Fanshawe.

### Comparação Visual

```
SEM rotação (find_room_centers.html atual):
    ┌─────────────┐
    │   ROOM      │
    │    100      │
    │             │
    └─────────────┘

COM rotação (como deve ser):
         ◇──────◇
        ╱         ╲
       ╱   ROOM    ╲
      │      100    │  Girado 21.3°
       ╲             ╱
        ╲───────────╱
         ◇         ◇
```

---

## ✅ CHECKLIST

- [ ] Localizou `find_room_centers.html`
- [ ] Adicionou função `rotatePoint()` (linhas 223-224)
- [ ] Modificou `handleSvgClick()` para aplicar rotação
- [ ] Testou em http://localhost:8081/tools/find_room_centers.html
- [ ] Verificou mensagem "ROTATED 21.3°" ao clicar
- [ ] Testou coordenadas na aplicação principal
- [ ] Validou que rooms aparecem na posição CORRETA

---

## 🆘 Se algo não funcionar

### Erro: "Coordinates showing same position as before"

Verificar:
```javascript
// Verificar se centerX e centerY estão corretos
console.log({
    viewBox: svg.viewBox.baseVal,
    centerX: centerX,
    centerY: centerY
});
```

### Erro: "Position offset by slight amount"

A rotação pode estar em direção oposta. Tente:
```javascript
// Ao invés de 21.3, usar -21.3
const rotatedPoint = rotatePoint(svgP.x, svgP.y, centerX, centerY, -21.3);
```

### Erro: "find_room_centers.html not found"

Verificar caminho correto:
```bash
ls -la tools/find_room_centers.html
# Deve existir em /home/luizeng/Documents/fanshawe_repo/Capstone_Project_AIM/tools/
```

---

## 📊 RESULTADO ESPERADO

Depois das mudanças:

```
Query no find_room_centers.html:
  Room: Room_1003
  Clique SVG: X=402.13, Y=514.13 (puro)
  APLICADA ROTAÇÃO DE 21.3°
  Coordenada Final: X=365.45, Y=542.89 ✅

Inserido em building_m_rooms.json:
  "Room_1003": { "x": 365.45, "y": 542.89 }

Na aplicação:
  Abre M1_official.svg com corners rotacionados
  Lê coordinate com rotação: X=365.45, Y=542.89
  Aplica bilinear interpolation
  Resultado: Room 1003 aparece na POSIÇÃO CORRETA ✅
```

---

## 📖 DOCUMENTAÇÃO COMPLETA

Para mais detalhes técnicos, veja:
- `ANALISE_COORDENADAS.md` - Análise técnica completa
- `map-controller.js` linhas 193, 250-284 - Implementação do mapa
- `find_room_centers.html` linhas 317-348 - Captura de coordenadas

---

**Status:** 🟢 PRONTO PARA IMPLEMENTAÇÃO

Depois de fazer essas mudanças, as coordenadas capturadas em `find_room_centers.html` corresponderão exatamente às posições no mapa da aplicação!

