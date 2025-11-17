# 🔍 Corridor Segment Validator - Guia de Uso

## O que é?

Uma ferramenta visual para **validar e diagnosticar** os segmentos de corredor que você tracejou. Ela verifica:

- ✅ Se todas as propriedades obrigatórias existem (`startNode`, `endNode`)
- ✅ Se os nós existem no grafo de navegação
- ✅ Se as coordenadas estão próximas dos nós esperados
- ✅ Quantos segmentos você já tracejou (cobertura)
- ✅ Quais segmentos estão válidos e quais têm problemas

## Como Usar

### 1. Abrir a Ferramenta

```bash
# No diretório do projeto
cd tools
open corridor_segment_validator.html
# ou simplesmente clique duas vezes no arquivo
```

### 2. Carregar Arquivo

Você tem duas opções:

**Opção A: Botão "Carregar corridor_segments_building_m.geojson"**
- Clique no botão roxo
- Carrega automaticamente do servidor (precisa estar rodando)

**Opção B: Upload Manual**
- Clique em "Escolher arquivo"
- Selecione `map/corridor_segments_building_m.geojson`

### 3. Interpretar os Resultados

#### 📊 Estatísticas (canto superior esquerdo)

```
┌──────────────┬──────────────┐
│ Segmentos: 7 │ Válidos: 7   │
├──────────────┼──────────────┤
│ Inválidos: 0 │ Cobertura: 29%│
└──────────────┴──────────────┘
```

- **Segmentos**: Total tracejado
- **Válidos**: Segmentos com todas as propriedades corretas
- **Inválidos**: Segmentos com problemas
- **Cobertura**: Porcentagem de 24 segmentos necessários

#### ⚠️ Problemas Encontrados

Se houver erros, aparecerá uma seção vermelha listando:

```
❌ M1_2_M1_3: Falta propriedade "startNode"
❌ M1_5_M1_6: endNode "M1_X" não existe no grafo
❌ corridor_M1_1_M1_2: Início está longe do startNode (8.5m)
```

#### 📍 Lista de Segmentos

Cada segmento mostra:

```
M1_2_M1_3
📍 M1_2 → M1_3
📏 2 pontos | 1.7m
✓ Válido
```

**Códigos de Cor:**
- 🟢 **Verde**: Segmento válido, pronto para usar
- 🔴 **Vermelho**: Segmento inválido, precisa correção

#### 🗺️ Visualização no Mapa

- **Pontos azuis**: Todos os nós do grafo de navegação
- **Linhas verdes**: Segmentos válidos
- **Linhas vermelhas**: Segmentos inválidos
- Clique em um segmento na lista para focar no mapa
- Clique em um ponto azul para ver o nome do nó

## Problemas Comuns e Soluções

### ❌ Problema: "Falta propriedade startNode/endNode"

**Causa**: O arquivo GeoJSON exportado não tem essas propriedades.

**Solução**: Adicione manualmente no arquivo:

```json
{
  "properties": {
    "name": "M1_2_M1_3",
    "segmentType": "corridor",
    "startNode": "M1_2",    ← ADICIONAR
    "endNode": "M1_3",      ← ADICIONAR
    "pointCount": 2,
    "length": 1.69
  }
}
```

### ❌ Problema: "startNode 'M1_X' não existe no grafo"

**Causa**: Nome do nó está errado.

**Solução**: Verifique a lista de nós válidos:

**Nós Principais (PATH 1):**
- `H_entry`, `M1_1`, `M1_2`, `M1_3`, `M1_Int_1`, `M1_4`, `M1_5`, `M1_6`, `M1_7`

**Nós Conector (PATH 2):**
- `M1_Turn_1`, `M1_8`

**Nós Banheiros (PATH 3):**
- `M1_Int_2`, `M1_9`, `M1_10`, `M1_11`, `M1_12`, `M1_13`

**Nós Ramificação (PATH 4):**
- `M1_14`, `M1_15`, `M1_16`, `M1_17`, `M1_18`, `M1_19`

### ❌ Problema: "Início está longe do startNode (8.5m)"

**Causa**: Você começou a traçar longe do ponto do nó.

**Solução**: 
1. No Route Builder, comece o traço **exatamente** no ponto azul do nó
2. Termine o traço **exatamente** no ponto azul do nó destino
3. Trace novamente com mais precisão

### ❌ Problema: "Nome não está na lista esperada"

**Causa**: Nome do segmento não segue a convenção.

**Solução**: Use o formato: `corridor_[startNode]_[endNode]`

Exemplos corretos:
- ✅ `corridor_M1_2_M1_3`
- ✅ `corridor_M1_Int_1_M1_4`
- ✅ `corridor_M1_Turn_1_M1_8`

Exemplos incorretos:
- ❌ `M1_2_M1_3` (falta "corridor_")
- ❌ `corridor_M1_2_to_M1_3` (usa "to" em vez de "_")
- ❌ `path_1006_1004` (é um segmento room-to-room, não corridor)

## Workflow Recomendado

### Passo 1: Traceje um Grupo de Segmentos

Use o Route Builder para tracear 3-5 segmentos de uma vez (ex: PATH 1 completo).

### Passo 2: Exporte o GeoJSON

Clique "📦 Export GeoJSON" no Route Builder.

### Passo 3: Adicione startNode/endNode

Edite o arquivo baixado:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "properties": {
        "name": "M1_2_M1_3",
        "startNode": "M1_2",    ← ADICIONAR
        "endNode": "M1_3"       ← ADICIONAR
      }
    }
  ]
}
```

### Passo 4: Valide com esta Ferramenta

1. Abra `corridor_segment_validator.html`
2. Carregue o arquivo
3. Verifique se todos estão **verdes** (válidos)
4. Corrija qualquer erro encontrado

### Passo 5: Substitua o Arquivo Original

```bash
cp ~/Downloads/route_segments_*.geojson \
   map/corridor_segments_building_m.geojson
```

### Passo 6: Teste na Aplicação

```bash
# Reinicie o servidor
python main.py

# Refresh no browser (Ctrl+F5)
# Teste navegação entre salas
```

## Checklist de Validação

Use este checklist antes de considerar um segmento "pronto":

- [ ] Nome segue formato `corridor_[start]_[end]`
- [ ] Tem propriedade `startNode` válida
- [ ] Tem propriedade `endNode` válida
- [ ] `startNode` existe no grafo
- [ ] `endNode` existe no grafo
- [ ] Coordenadas começam próximo ao nó inicial
- [ ] Coordenadas terminam próximo ao nó final
- [ ] Segmento está **verde** na ferramenta de validação
- [ ] Segmento está na lista esperada (CORRIDOR_SEGMENTS_TO_TRACE.md)

## Interpretação de Cobertura

| Cobertura | Segmentos | Status |
|-----------|-----------|--------|
| 0-33% | 0-8 | 🔴 Início - Sistema ainda não funciona bem |
| 34-49% | 9-11 | 🟡 Progresso - Próximo do threshold |
| **50-70%** | **12-17** | 🟢 **Funcional** - Threshold atingido |
| 71-95% | 18-23 | 🟢 Bom - Maioria das rotas funcionam |
| 96-100% | 24/24 | 🟢 Completo - 100% cobertura |

**Threshold Mínimo**: 50% (12 segmentos)
- Abaixo de 50%: Sistema usa Dijkstra (linhas retas)
- Acima de 50%: Sistema usa corridor assembly (suas linhas traçadas)

## Progresso Atual

Baseado no arquivo que você mostrou:

```
✅ Completados: 7/24 segmentos (29%)
📍 PATH 1: 7/8 segmentos
   ✅ corridor_M1_1_M1_2
   ✅ corridor_M1_2_M1_3
   ✅ corridor_M1_3_M1_Int_1
   ✅ corridor_M1_Int_1_M1_4
   ✅ corridor_M1_4_M1_5
   ✅ corridor_M1_5_M1_6
   ✅ corridor_M1_6_M1_7
   ⬜ corridor_H_entry_M1_1  ← FALTA

📍 PATH 2: 0/2 segmentos
📍 PATH 3: 0/7 segmentos
📍 PATH 4: 0/7 segmentos
```

## Próximos Passos

1. **Complete PATH 1**: Trace `corridor_H_entry_M1_1`
2. **Valide os 8 segmentos** com esta ferramenta
3. **Teste na aplicação**: "navigate from room 1003 to 1049"
4. **Continue PATH 2**: 2 segmentos (connector)
5. **Continue PATH 3**: 7 segmentos (bathrooms)
6. **Continue PATH 4**: 7 segmentos (side branch)

## Solução de Problemas Técnicos

### Ferramenta não carrega o arquivo automaticamente

**Causa**: Servidor não está rodando ou arquivo não existe.

**Solução**: 
```bash
# Verifique se o servidor está rodando
curl http://127.0.0.1:8081/map/corridor_segments_building_m.geojson

# Se não funcionar, use upload manual
```

### Mapa não aparece

**Causa**: Problema com Leaflet.js ou internet.

**Solução**: Verifique conexão de internet (usa OpenStreetMap tiles).

### Nós não aparecem no mapa

**Causa**: JavaScript não carregou ou erro no console.

**Solução**: 
1. Abra Console do Browser (F12)
2. Procure por erros em vermelho
3. Recarregue a página (Ctrl+F5)

## Referências

- **CORRIDOR_SEGMENTS_TO_TRACE.md**: Lista completa dos 24 segmentos
- **CORRIDOR_SYSTEM_GUIDE.md**: Guia do sistema de corridor assembly
- **map-controller.js**: Código do sistema de montagem de rotas

## Dicas Pro

1. **Trace em lotes**: Faça PATH completo de uma vez (8 segmentos)
2. **Valide frequentemente**: Use esta ferramenta após cada lote
3. **Teste incrementalmente**: Teste na aplicação após cada PATH
4. **Comece pelos nós**: Sempre inicie e termine traços nos pontos azuis
5. **Use zoom máximo**: Facilita precisão no Route Builder
6. **Salve backups**: Mantenha cópias do GeoJSON durante edição

---

**Dúvidas?** Consulte o console do browser (F12) para logs detalhados!
