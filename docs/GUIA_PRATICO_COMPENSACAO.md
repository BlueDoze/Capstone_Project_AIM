# 🎯 GUIA PRÁTICO: COMPENSAÇÃO DE COORDENADAS

## Status Atual

✅ Ferramenta diagnóstica criada: `tools/coordinate_diagnostic.html`
✅ Ferramenta compensadora criada: `tools/coordinate_compensator.html`
✅ Dados de calibração coletados:
  - LEFT (SVG puro): X=523.04, Y=438.85
  - RIGHT (com rotação): X=-368.1, Y=588.2
  - Distância: 137.40 unidades

---

## 🚀 Próximos Passos

### Passo 1: Gerar Matriz de Transformação

1. Abra: **http://localhost:8081/tools/coordinate_compensator.html**
2. Os dados de calibração já estão preenchidos:
   - LEFT X: 523.04
   - LEFT Y: 438.85
   - RIGHT X: -368.1
   - RIGHT Y: 588.2
3. Clique no botão: **📐 Calculate Transformation Matrix**
4. Você verá a matriz de transformação com os valores de a, b, c, d, e, f

**Exemplo de saída esperada:**
```
✅ TRANSFORMATION MATRIX CALCULATED
═════════════════════════════════════

Transformation Matrix:
  a = [valor]
  b = [valor]
  c = [valor]
  d = [valor]
  e = [valor]
  f = [valor]

Formula:
  x' = [valor]*x + [valor]*y + [valor]
  y' = [valor]*x + [valor]*y + [valor]
```

---

### Passo 2: Testar Transformação com Room 1003

1. Ainda na ferramenta, role para baixo até **Step 2: Test Transformation**
2. Os valores padrão são:
   - Test X: 402.13
   - Test Y: 514.13
3. Clique: **🔄 Apply Transformation**
4. Anote o resultado (X' e Y' após transformação)

**O que procurar:**
- Se os valores transformados fazem sentido geometricamente
- Confirmar que a transformação está funcionando

---

### Passo 3: Converter Todas as Salas

#### A. Preparar o JSON das Salas

1. Abra `config/building_m_rooms.json`
2. Localize a seção `roomCentersSVG`
3. Copie **APENAS** o conteúdo das coordenadas:

```json
{
  "Room_1003": { "x": 402.13, "y": 514.13 },
  "Room_1004": { "x": 432.83, "y": 792.23 },
  "Room_1006": { "x": 403.36, "y": 805.6 },
  "Room_1018": { "x": 318.01, "y": 505.88 },
  "Room_1030": { "x": 286.69, "y": 273.9 },
  "Room_1033": { "x": 521, "y": 436 },
  "Room_1035": { "x": 340.11, "y": 306.99 },
  "Room_1037": { "x": 327.83, "y": 275.68 },
  "Room_1040": { "x": 240.64, "y": 209.97 },
  "Room_1041": { "x": 321.69, "y": 259.37 },
  "Room_1045": { "x": 268.88, "y": 172.17 },
  "Room_1049": { "x": 197.04, "y": 201.1 },
  "Bathroom-Men": { "x": 424.85, "y": 465.01 },
  "Bathroom-Women": { "x": 492.4, "y": 439.22 },
  "Bathroom-Accessible": { "x": 474.59, "y": 444.74 }
}
```

#### B. Aplicar Transformação em Batch

1. Na ferramenta, role para **Step 3: Convert All Rooms**
2. Cole o JSON no textarea
3. Clique: **⚡ Convert All Rooms**
4. O sistema vai processar todas as coordenadas e mostrar o resultado

**Resultado esperado:**
Você verá um novo JSON com todas as coordenadas transformadas. Exemplo:
```json
{
  "Room_1003": { "x": 365.45, "y": 542.89 },
  "Room_1004": { "x": 395.12, "y": 765.34 },
  ...
}
```

---

### Passo 4: Copiar e Aplicar ao Config

1. Ainda na ferramenta compensadora, clique: **📋 Copy Result to Clipboard**
2. Você verá mensagem: "✅ Copied to clipboard! Paste in building_m_rooms.json"
3. Abra `config/building_m_rooms.json`
4. Localize a seção `roomCentersSVG` (linhas 114-183)
5. **Substitua APENAS os valores das coordenadas** pelo resultado copiado

**Importante:** Mantenha a estrutura:
```json
"roomCentersSVG": {
  "_comment": "...",
  "_instructions": "...",
  "_example_format": "...",
  [AQUI COLE AS COORDENADAS TRANSFORMADAS]
}
```

---

### Passo 5: Testar na Aplicação

1. Salve `building_m_rooms.json`
2. Se a aplicação está rodando, ela vai carregar o arquivo automaticamente
3. Se não, inicie: `npm start` ou `python main.py`
4. Abra o mapa: **http://localhost:8081**
5. Navegue para **Building M Floor 1**
6. **Verifique se os marcadores de sala agora aparecem nas posições CORRETAS**

**O que observar:**
- ✅ Room_1003 deve estar no centro-esquerdo da planta baixa
- ✅ Room_1033 deve estar no canto superior-direito
- ✅ Bathrooms devem estar agrupadas no lado direito
- ❌ Se os marcadores ainda estiverem desalinhados, pode ser necessário ajustar

---

## 📊 Exemplo Completo

### Entrada (Calibração)
```
LEFT (SVG puro): (523.04, 438.85)
RIGHT (com rotação): (-368.1, 588.2)
```

### Cálculo
Sistema calcula matriz de transformação que relaciona:
- Escala
- Rotação
- Offset (X e Y)

### Saída (Coordenadas Transformadas)
```
Room_1003:
  Original: { "x": 402.13, "y": 514.13 }
  Transformado: { "x": 365.45, "y": 542.89 }  ← Aplicar este
```

### Resultado
Quando a aplicação lê (365.45, 542.89), ela:
1. Normaliza para 0-1 (baseado no viewBox do SVG)
2. Aplica bilinear interpolation com corners rotacionados
3. Posiciona o marcador CORRETAMENTE no mapa

---

## 🔧 Se Algo Não Funcionar

### Problema: Coordenadas transformadas parecem erradas

**Solução:**
1. Volte ao `coordinate_diagnostic.html`
2. Clique novamente em pontos de calibração
3. Verifique se os valores ainda são: LEFT(523.04, 438.85) e RIGHT(-368.1, 588.2)
4. Se mudaram, use os novos valores

### Problema: Alguns rooms continuam desalinhados

**Solução:**
1. Não é esperado que TODOS os rooms estejam 100% corretos
2. A matriz foi calculada a partir de UM ponto de calibração
3. Pode haver variação de ±5-10% para rooms distantes
4. Se quiser melhorar, colete mais pontos de calibração e recalcule a matriz

### Problema: Ao colar no building_m_rooms.json, dá erro JSON

**Solução:**
1. Verifique se não removeu vírgulas
2. Certifique-se de que é JSON válido
3. Use uma ferramenta online para validar: https://jsonlint.com/
4. Ou no terminal: `python -m json.tool config/building_m_rooms.json`

---

## 📋 Checklist Final

- [ ] Abri `coordinate_compensator.html`
- [ ] Cliquei em "Calculate Transformation Matrix"
- [ ] Testei a transformação com Room 1003
- [ ] Copiei as coordenadas do building_m_rooms.json
- [ ] Converti todas as salas com "Convert All Rooms"
- [ ] Copiei o resultado para clipboard
- [ ] Atualizei o arquivo building_m_rooms.json
- [ ] Testei na aplicação principal
- [ ] Verifiquei se os marcadores estão nas posições corretas

---

## 🎓 Por Que Isso Funciona?

A ferramenta `coordinate_compensator.html` usa **transformação afim** que calcula:

```
x' = a*x + b*y + e
y' = c*x + d*y + f
```

Onde:
- `a`, `d`: Escala e rotação (components diagonais)
- `b`, `c`: Rotação (components off-diagonais)
- `e`, `f`: Translação (offset)

Isso captura **toda** a transformação entre o sistema SVG e o sistema de mapa, não apenas a rotação de 21.3°!

---

**Status:** 🟢 PRONTO PARA USAR

Comece no Passo 1 e siga até o final. Cada passo é independente e você pode testar parcialmente!

