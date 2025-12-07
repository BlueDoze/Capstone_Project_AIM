# Web Scraping Pipelines com Medidas Anti-Detecção

## 📊 Resumo Executivo

Este documento descreve os **6 pipelines de web scraping** desenvolvidos para a aplicação Fanshawe Navigator. Todos implementam medidas robustas anti-detecção usando `playwright-stealth` para evitar bloqueios.

- **Total de pipelines:** 6
- **Plataformas cobertas:** D2L/Brightspace + SharePoint
- **Status geral:** Produção e desenvolvimento
- **Medida anti-detecção comum:** playwright-stealth + user-agent realista + HTTP headers legítimos

---

## 🔧 6 Pipelines Documentados

### 1. D2L Event Scraper (Serviço Principal)

**📁 Arquivos:**
- **Serviço:** `src/services/d2l_scraper.py`
- **Script de execução:** `tests/test_d2l_scraper.py`

**🎯 O que faz:** Extrai eventos do calendário D2L/Brightspace de um curso específico

**📊 Status:** ✅ Produção

**▶️ Como executar:**

```bash
# 1. Ativar ambiente virtual
source .venv/bin/activate

# 2. Executar script de teste interativo com menu
python tests/test_d2l_scraper.py

# O script apresenta um menu com opções:
# [1] Teste básico de scraping
# [2] Teste com screenshot (salva debug_page.png)
# [3] Testar com curso diferente
# [4] Executar todos os testes
# [5] Modo interativo (navegador visível)
# [0] Sair

# 3. OU executar programaticamente
python -c "
import asyncio
import os
from src.services.d2l_scraper import D2LEventScraper

async def main():
    username = os.getenv('D2L_USERNAME')
    password = os.getenv('D2L_PASSWORD')
    scraper = D2LEventScraper(username=username, password=password, headless=True)
    events = await scraper.scrape_events(course_id='2001540')
    print(f'✅ {len(events)} eventos extraídos')

asyncio.run(main())
"
```

**✅ Resultado esperado:**

**Execução do script interativo:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    D2L EVENT SCRAPER - TESTE ISOLADO                         ║
║                        Fanshawe Navigator Project                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

[Menu de Testes]
  [1] Teste básico de scraping (curso 2001540)
  [2] Teste com screenshot (debug visual)
  [3] Testar com curso diferente
  [4] Executar todos os testes
  [5] Modo interativo (ver navegador)
  [0] Sair

Escolha uma opção: 1

================================================================================
  TESTE 1: Scraping Básico de Eventos
================================================================================

✓ Credenciais encontradas
  Username: abc***xy
  Password: **********

[Test] Iniciando scraping...
[Test] Isso pode levar 30-60 segundos...

================================================================================

✓ Scraping concluído!
  Total de eventos encontrados: 3

================================================================================
  EVENTOS EXTRAÍDOS
================================================================================

[Evento #1]
  📌 Título: Workshop de Python
  📅 Data: 2025-12-10
  🕐 Hora: 14:00 PM
  📍 Local: Room SC 2013
  📝 Descrição: Workshop introdutório sobre Python para iniciantes

[Evento #2]
  📌 Título: Prova Final
  📅 Data: 2025-12-15
  🕐 Hora: 10:00 AM
  📍 Local: Room SC 1001
  📝 Descrição: Avaliação final do curso

Salvar eventos em JSON? (s/n): s
✓ Eventos salvos em: test_events_20251206_143025.json
```

**Estrutura JSON retornada:**
```json
{
  "metadata": {
    "source": "d2l_scraper",
    "scraped_at": "2025-12-06T14:30:00",
    "total_events": 3
  },
  "events": [
    {
      "name": "Workshop de Python",
      "date": "2025-12-10",
      "time": "14:00 PM",
      "location": "Room SC 2013",
      "description": "Workshop introdutório sobre Python para iniciantes"
    },
    {
      "name": "Prova Final",
      "date": "2025-12-15",
      "time": "10:00 AM",
      "location": "Room SC 1001",
      "description": "Avaliação final do curso"
    }
  ]
}
```

**🔒 Medidas Anti-Detecção:**
- playwright-stealth library
- User-Agent Firefox 121.0 realista
- HTTP headers legítimos (Accept, DNT, Sec-Fetch-*)
- Bloqueio de recursos desnecessários
- Delays aleatórios (2-4s) entre ações

**📚 Docs:** `docs/scraping/D2L_SCRAPER_README.md` | `docs/scraping/D2L_AGENT_INTEGRATION.md`

---

### 2. Announcements Scraper

**📁 Arquivos:**
- **Serviço:** `src/scrapers/d2l/announcements.py` (executável diretamente)

**🎯 O que faz:** Extrai os 5 anúncios mais recentes do D2L com login único e automação 2FA

**📊 Status:** ✅ Produção

**▶️ Como executar:**

```bash
# 1. Ativar ambiente virtual
source .venv/bin/activate

# 2. Executar coleta de anúncios
python src/scrapers/d2l/announcements.py

# O script salva automaticamente em: all_announcements.json
```

**✅ Resultado esperado:**

A execução gera dois arquivos:

1. **all_announcements.json** (dados brutos):
```json
[
  {
    "title": "Important Course Update",
    "date": "Dec 5, 2025",
    "content": "Please review the updated syllabus...",
    "author": "Prof. John Smith"
  },
  {
    "title": "Assignment 3 Deadline Extended",
    "date": "Dec 4, 2025",
    "content": "The deadline has been moved to Dec 15...",
    "author": "Prof. John Smith"
  }
]
```

2. **data/d2l_announcements.json** (após transformação, formato cache):
- Estrutura otimizada para o agente conversacional
- Inclui metadados de extração
- Formatação limpa para processamento

**Console output:**
```
✅ Extraction completed successfully!
📊 Total announcements: 5
📁 Saved to: all_announcements.json
```

**⏰ Atualização recomendada:** Diariamente via cron
```bash
0 8 * * * cd /path/to/Capstone_Project_AIM && source .venv/bin/activate && python3 extract_all_announcements.py && python3 transform_cache.py
```

**🔒 Medidas Anti-Detecção:**
- playwright-stealth library
- User-Agent Firefox 121.0
- Auto-preenchimento 2FA
- Delays aleatórios entre interações
- Bloqueio de recursos desnecessários

**📚 Docs:** `docs/guides/ANNOUNCEMENTS_USAGE_GUIDE.md`

---

### 3. Links Crawler

**📁 Arquivo:** `src/scrapers/d2l/links_crawler.py`

**🎯 O que faz:** Rastreia todos os links das páginas de conteúdo do D2L e extrai conteúdo HTML de cada URL encontrada

**📊 Status:** 📋 Desenvolvimento

**▶️ Como executar:**

```bash
# 1. Ativar ambiente virtual
source .venv/bin/activate

# 2. Executar para um curso específico
python src/scrapers/d2l/links_crawler.py --course-id 2001540

# 3. OU para outro curso
python src/scrapers/d2l/links_crawler.py --course-id 2001541
```

**✅ Resultado esperado:**

O crawler cria múltiplos arquivos JSON, um para cada link descoberto:

**Estrutura de saída:**
```
data/content_links/
├── module_1_introduction.json
├── module_2_variables.json
├── assignment_1_details.json
└── ...
```

**Formato de cada arquivo:**
```json
{
  "url": "https://fanshawec.desire2learn.com/d2l/le/content/...",
  "title": "Module 1: Introduction to Programming",
  "content": "<html>...</html>",
  "extracted_at": "2025-12-06T15:20:00",
  "links_found": 5
}
```

**Console output:**
```
🔍 Crawling course 2001540...
✅ Found 15 links
📥 Extracting content from link 1/15...
📥 Extracting content from link 2/15...
...
✅ Crawl completed! 15 files saved to data/content_links/
```

**🔒 Medidas Anti-Detecção:**
- playwright-stealth library
- User-Agent Firefox 121.0
- Auto-preenchimento 2FA
- Delays aleatórios (2-4s) entre requisições
- Sanitização de nomes de arquivo

**📚 Docs:** Guia integrado no próprio script

---

### 4. Announcement Content

**📁 Arquivo:** `src/scrapers/d2l/announcement_content.py`

**🎯 O que faz:** Extrai o conteúdo HTML completo dos 5 anúncios mais recentes do D2L, incluindo formatação e elementos `d2l-html-block`

**📊 Status:** 📋 Desenvolvimento

**▶️ Como executar:**

```bash
# 1. Ativar ambiente virtual
source .venv/bin/activate

# 2. Executar extração de conteúdo
python src/scrapers/d2l/announcement_content.py
```

**✅ Resultado esperado:**

O scraper cria o arquivo **announcement_contents.json** com conteúdo HTML completo:

```json
{
  "total": 5,
  "extracted_at": "2025-12-06T13:00:00",
  "announcements": [
    {
      "title": "Important Course Update",
      "date": "Dec 5, 2025",
      "author": "Prof. John Smith",
      "content": "<div class='d2l-html-block'><p>Please review the updated syllabus...</p><ul><li>Topic 1</li><li>Topic 2</li></ul></div>",
      "has_attachments": true,
      "word_count": 245
    },
    {
      "title": "Assignment 3 Deadline Extended",
      "date": "Dec 4, 2025",
      "author": "Prof. John Smith",
      "content": "<div class='d2l-html-block'><p>The deadline has been moved to Dec 15...</p></div>",
      "has_attachments": false,
      "word_count": 87
    }
  ]
}
```

**Console output:**
```
🔍 Extracting announcement content...
✅ Extracted 5 announcements with full HTML
📁 Saved to: announcement_contents.json
📊 Total words extracted: 1,234
```

**🔒 Medidas Anti-Detecção:**
- playwright-stealth library
- User-Agent Firefox 121.0
- HTTP headers legítimos
- Bloqueio de recursos desnecessários
- Parsing especializado de elementos D2L

**📚 Docs:** Disponível no script

---

### 5. Content Home

**📁 Arquivo:** `src/scrapers/d2l/content_home.py`

**🎯 O que faz:** Extrai a estrutura completa da página Content/Home do curso D2L, incluindo módulos, tópicos, links e organização hierárquica

**📊 Status:** 📋 Desenvolvimento

**▶️ Como executar:**

```bash
# 1. Ativar ambiente virtual
source .venv/bin/activate

# 2. Executar para um curso específico
python src/scrapers/d2l/content_home.py --course-id 2001540

# 3. OU para outro curso
python src/scrapers/d2l/content_home.py --course-id 2001541
```

**✅ Resultado esperado:**

O scraper cria o arquivo **content_home_{COURSE_ID}.json** com a estrutura completa:

```json
{
  "course_id": "2001540",
  "course_name": "Introduction to Programming",
  "extracted_at": "2025-12-06T14:00:00",
  "total_modules": 8,
  "total_items": 45,
  "modules": [
    {
      "module_number": 1,
      "name": "Module 1: Introduction to Python",
      "status": "active",
      "items": [
        {
          "type": "topic",
          "title": "What is Python?",
          "url": "https://fanshawec.desire2learn.com/d2l/le/content/..."
        },
        {
          "type": "assignment",
          "title": "Assignment 1: Hello World",
          "url": "https://fanshawec.desire2learn.com/d2l/lms/dropbox/...",
          "due_date": "Dec 15, 2025"
        }
      ]
    },
    {
      "module_number": 2,
      "name": "Module 2: Variables and Data Types",
      "status": "locked",
      "items": []
    }
  ]
}
```

**Console output:**
```
🔍 Extracting content structure for course 2001540...
✅ Found 8 modules
📥 Processing Module 1...
📥 Processing Module 2...
...
✅ Extraction complete!
📁 Saved to: content_home_2001540.json
📊 Total: 8 modules, 45 items
```

**🔒 Medidas Anti-Detecção:**
- playwright-stealth library
- User-Agent Firefox 121.0
- Auto-preenchimento 2FA
- Delays aleatórios
- Parsing especializado de estrutura D2L

**📚 Docs:** Integrada no script

---

### 6. Professor Info

**📁 Arquivo:** `src/scrapers/d2l/professor_info.py`

**🎯 O que faz:** Extrai informações do professor do curso (nome, email, escritório, horários de atendimento) do widget "Professor Information" na página Home do curso

**📊 Status:** ✅ Produção (corrigido para extrair conteúdo interno do widget)

**▶️ Como executar:**

```bash
# 1. Ativar ambiente virtual
source .venv/bin/activate

# 2. Extração básica
python src/scrapers/d2l/professor_info.py --course-id 2001540

# 3. Com modo debug (gera screenshots)
python src/scrapers/d2l/professor_info.py --course-id 2001540 --debug

# 4. Com caminho de saída customizado
python src/scrapers/d2l/professor_info.py --course-id 2001540 --output custom_path.json
```

**✅ Resultado esperado:**

Arquivo salvo em `data/course_{COURSE_ID}/professor_info.json`:
```json
{
  "course_id": "2001540",
  "extracted_at": "2025-12-06T13:23:19.567674",
  "source_url": "https://www.fanshaweonline.ca/d2l/home/2001540",
  "extraction_method": "widget_selector:.d2l-widget",
  "name": "Mohammad Noorchenarboo",
  "email": "mnoorchenarboo@fanshawec.ca",
  "office": "By appointment only",
  "office_hours": "Please email to arrange a meeting"
}
```

**💡 Como funciona:**

O script usa estratégias em cascata:
1. **Busca widget principal** com seletor `.d2l-widget` que contém "Professor Information"
2. **Extrai conteúdo interno** procurando por `d2l-html-block` ou `d2l-widget-content` dentro do widget
3. **Parseia campos específicos** usando regex para extrair:
   - Name: após "Name:" ou padrões de nome completo
   - Email: de links `mailto:` ou padrão de email
   - Office: após "Office:" ou "Office Location:"
   - Office Hours: após "Office Hours:" ou "Hours:"
4. **Fallback para iframes**: Se conteúdo não encontrado no DOM, verifica iframes da página

**Console output:**
```
🔍 Extracting professor info for course 2001540...
✅ Login successful
🔎 Trying widget parser...
✅ Professor info extracted!
📁 Saved to: professor_info_2001540.json
📁 Cache updated: data/course_2001540/professor_info.json

👤 Professor: Mohammad Noorchenarboo
📧 Email: mnoorchenarboo@fanshawec.ca
🏢 Office: By appointment only
```

**Modo Debug:**
Com `--debug`, gera screenshot `debug_page.png` para troubleshooting

**🔒 Medidas Anti-Detecção:**
- playwright-stealth library
- User-Agent Firefox 121.0
- Auto-preenchimento 2FA
- Delays aleatórios
- Múltiplas estratégias (widget, shadow DOM, full page scan)
- Debug com screenshots

**📚 Docs:** `docs/guides/PROFESSOR_EXTRACTION_GUIDE.md`

---

### 7. SharePoint Events

**📁 Arquivo:** `src/scrapers/sharepoint/events.py`

**🎯 O que faz:** Extrai eventos do calendário SharePoint da Fanshawe College, incluindo título, data, horário, local e descrição

**📊 Status:** 📋 Desenvolvimento

**▶️ Como executar:**

```bash
# 1. Ativar ambiente virtual
source .venv/bin/activate

# 2. Executar extração básica
python src/scrapers/sharepoint/events.py

# 3. (Opcional) Editar SHAREPOINT_EVENTS_LIST_GUID no script para lista customizada
```

**✅ Resultado esperado:**

O scraper cria o arquivo **sharepoint_events.json** com até 100 eventos:

```json
{
  "source": "sharepoint",
  "list_guid": "d1ad5108-61da-44a6-9b0a-d114a09c5e7e",
  "extracted_at": "2025-12-06T16:00:00",
  "total_events": 47,
  "events": [
    {
      "title": "Career Fair - Winter 2025",
      "date": "2025-12-15",
      "time": "10:00 AM - 3:00 PM",
      "location": "Student Centre - Main Hall",
      "description": "Annual career fair with 50+ employers from various industries.",
      "category": "Career Services",
      "registration_required": true
    },
    {
      "title": "International Student Orientation",
      "date": "2026-01-05",
      "time": "9:00 AM - 12:00 PM",
      "location": "F Building - Room 2010",
      "description": "Welcome session for new international students.",
      "category": "Student Services",
      "registration_required": false
    }
  ]
}
```

**Console output:**
```
🔍 Connecting to SharePoint...
✅ Login successful
📅 Extracting events from list: d1ad5108-61da-44a6-9b0a-d114a09c5e7e
✅ Found 47 events
📁 Saved to: sharepoint_events.json
⚠️  Limit: 100 events per execution
```

**Configuração:**
- **List GUID padrão:** `d1ad5108-61da-44a6-9b0a-d114a09c5e7e`
- **Limite:** 100 eventos por extração
- Para alterar o GUID, edite a constante `SHAREPOINT_EVENTS_LIST_GUID` no script

**🔒 Medidas Anti-Detecção:**
- playwright-stealth library
- User-Agent Firefox 121.0
- Auto-preenchimento 2FA
- Delays aleatórios
- Múltiplas estratégias de parsing (event cards, list cells, aria-labels)

**📚 Docs:** `docs/scraping/sharepoint_scraper.md`

---

## 🔧 Configuração Comum

### Arquivo .env

Criar arquivo `.env` na raiz do projeto com as credenciais:

```env
D2L_USERNAME=seu_username_fanshawe
D2L_PASSWORD=sua_senha_fanshawe
GEMINI_API_KEY=sua_chave_gemini
```

⚠️ **IMPORTANTE:** Nunca fazer commit do arquivo `.env` com credenciais reais!

### Instalação de Dependências

```bash
# Instalar packages Python
pip install -r requirements.txt

# Instalar navegador Playwright (Firefox)
playwright install firefox

# OU se preferir Chrome/Chromium
playwright install chromium
```

### Ativar Ambiente Virtual

```bash
# Ativar .venv
source .venv/bin/activate

# Desativar
deactivate
```

---

## 🛡️ Medidas Anti-Detecção em Detalhe

### 1. Biblioteca Stealth

```python
from playwright_stealth import Stealth

stealth = Stealth()
await stealth.apply_stealth_async(page)
```

Simula comportamento de navegador legítimo, ocultando indicadores de automação.

### 2. User-Agent Realista

```python
user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
```

Simula um Firefox real em ambiente Linux.

### 3. HTTP Headers Legítimos

```python
extra_http_headers={
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',  # Do Not Track
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}
```

Headers que um navegador legítimo enviaria.

### 4. Bloqueio de Recursos Desnecessários

```python
await context.route("**/*", lambda route:
    route.abort() if route.request.resource_type in ["image", "font", "media"]
    else route.continue_()
)
```

Acelera carregamento e reduz assinatura digital.

### 5. Delays Aleatórios

```python
import random
await asyncio.sleep(random.uniform(2.0, 4.0))  # 2-4 segundos
```

Simula comportamento humano entre ações.

### 6. Auto-preenchimento 2FA

Os scripts detectam e preenchem automaticamente códigos 2FA da Microsoft:

```python
verification_code = await page.evaluate("""
    () => {
        const codeSelectors = [
            '#idRichContext_DisplaySign',
            '[data-value]',
            '.text-title'
        ];
        // ... lógica para extrair código
    }
""")
```

---

## 📊 Matriz Comparativa de Pipelines

| Recurso | d2l_scraper.py | announcements.py | links_crawler.py | announcement_content.py | content_home.py | professor_info.py | events.py |
|---------|---|---|---|---|---|---|---|
| **Produção** | ✅ | ✅ | 📋 | 📋 | 📋 | ✅ | 📋 |
| **Documentação Completa** | ✅ | ✅ | 📄 | 📄 | 📄 | ✅ | 📄 |
| **playwright-stealth** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **User-Agent Firefox** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Extra Headers** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **2FA Automation** | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Delays Aleatórios** | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Teste Isolado** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Integração Sistema** | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |

**Legenda:**
- ✅ Totalmente implementado
- 📋 Em desenvolvimento
- 📄 Documentação básica integrada
- ❌ Não implementado

---

## 📚 Referências de Documentação

### Pipelines em Produção (Documentação Completa)

1. **D2L Event Scraper**
   - 📄 Guia Principal: `docs/scraping/D2L_SCRAPER_README.md`
   - 📄 Integração com Agente: `docs/scraping/D2L_AGENT_INTEGRATION.md`
   - 📄 Teste: `tests/test_d2l_scraper.py`

2. **Announcements Scraper**
   - 📄 Guia de Uso: `docs/guides/ANNOUNCEMENTS_USAGE_GUIDE.md`
   - 📄 Script: `src/scrapers/d2l/announcements.py`
   - 📄 Saída: `data/announcements/all_announcements.json`

3. **Professor Info Scraper**
   - 📄 Guia Completo: `docs/guides/PROFESSOR_EXTRACTION_GUIDE.md`
   - 📄 Script: `src/scrapers/d2l/professor_info.py`
   - 📄 Integração: Cache em `data/course_{ID}/professor_info.json`

### Pipelines em Desenvolvimento

4. **Links Crawler** - Documentação integrada no script
5. **Announcement Content** - Documentação integrada no script
6. **Content Home** - Documentação integrada no script
7. **My Courses Scraper** - Documentação integrada no script
8. **SharePoint Events** - `docs/scraping/sharepoint_scraper.md`

---

## 🧪 Testando os Pipelines

### Teste Rápido D2L Scraper

```bash
# Ativa ambiente virtual
source .venv/bin/activate

# Executa teste isolado com menu
python tests/test_d2l_scraper.py

# Escolha opção 1 para teste básico
# Escolha opção 5 para modo interativo (ver navegador)
```

### Teste Announcements

```bash
source .venv/bin/activate

# Coleta
python src/scrapers/d2l/announcements.py

# Verifica resultado
cat data/announcements/all_announcements.json | python -m json.tool
```

### Teste Professor Info

```bash
source .venv/bin/activate

# Extração básica
python src/scrapers/d2l/professor_info.py --course-id 2001540

# Com debug (gera screenshots para investigação)
python src/scrapers/d2l/professor_info.py --course-id 2001540 --debug

# Verifica resultado e screenshot gerado
cat data/course_2001540/professor_info.json | python -m json.tool
ls -la debug_professor_2001540.png
```

---

## 🐛 Troubleshooting

### Professor Info retorna campos null

**Problema:** Alguns campos retornam `null` mesmo com widget presente

**Diagnóstico:**
```bash
# Execute com debug
python src/scrapers/d2l/professor_info.py --course-id 2001540 --debug

# Verifique o JSON gerado
cat data/course_2001540/professor_info.json | python -m json.tool

# Abra o screenshot para ver visualmente
xdg-open debug_professor_2001540.png  # Linux
open debug_professor_2001540.png      # macOS
```

**Soluções possíveis:**
1. **Widget não configurado**: Verifique manualmente no D2L se o curso tem informações do professor
2. **Formato diferente**: Alguns cursos podem usar formato diferente (ex: "Instructor:" ao invés de "Name:")
3. **Testar outro curso**: `python src/scrapers/d2l/professor_info.py --course-id OUTRO_ID --debug`
4. **Conteúdo parcial**: O script extrai o que estiver disponível - campos faltantes retornam `null`

### 2FA timeout

**Problema:** Script aguarda 5 minutos por aprovação do 2FA

**Solução:**
- Mantenha o celular com Microsoft Authenticator próximo
- Aprove imediatamente quando a notificação aparecer
- Se timeout, execute o script novamente (login pode persistir)

### Announcements não salva no diretório correto

**Problema:** Arquivo salvo no diretório raiz ao invés de `data/announcements/`

**Diagnóstico:**
```bash
# Verificar se diretório foi criado
ls -la data/announcements/

# Verificar se arquivo foi salvo corretamente
cat data/announcements/all_announcements.json
```

**Solução:** Código já foi corrigido para salvar em `data/announcements/all_announcements.json` automaticamente

---

## ⚖️ Considerações Legais

⚠️ **IMPORTANTE:**

- Este sistema de scraping é para uso **educacional** apenas
- Obtenha **autorização** do departamento de TI da Fanshawe
- Respeite os **Termos de Serviço** do D2L e SharePoint
- Não use para scraping em massa ou comercial
- Implemente **rate limiting** adequado
- Não compartilhe dados pessoais de outros usuários
- Mantenha logs de actividade de scraping

---

## 📝 Histórico de Documentação

**Documento Criado:** Novembro 2025

**Versão:** 1.0

**Objetivo:** Documentar todos os 7 pipelines de web scraping com medidas anti-detecção

**Pipelines Documentados:**
1. ✅ D2L Event Scraper (Produção)
2. ✅ Announcements Scraper (Produção)
3. ✅ Professor Info Scraper (Produção)
4. 📋 Links Crawler (Desenvolvimento)
5. 📋 Announcement Content (Desenvolvimento)
6. 📋 Content Home (Desenvolvimento)
7. 📋 SharePoint Events (Desenvolvimento)

**Pipelines Removidos:**
- ❌ My Courses Scraper (Removido em Dezembro 2025 - Shadow DOM com carregamento assíncrono impedia extração confiável)

---

**Documento centralizado para manutenção e referência de todos os pipelines com medidas anti-detecção.**

*Mantido por: Fanshawe Navigator Project Team*
~~