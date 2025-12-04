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

**Arquivo:** `src/services/d2l_scraper.py` (505 linhas)

**Funcionalidade:** Extração de eventos da plataforma D2L/Brightspace

**Status:** ✅ **Produção**

**Medidas Anti-Detecção:**
- ✅ `playwright-stealth` library
- ✅ User-Agent: `Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0`
- ✅ Extra HTTP headers (Accept, DNT: 1, Sec-Fetch-*, Cache-Control)
- ✅ `--disable-blink-features=AutomationControlled`
- ✅ Bloqueio de recursos desnecessários (imagens, fontes, media)
- ✅ Delays aleatórios (2-4s) entre requisições

**Como Rodar:**

```bash
# Via teste isolado com menu interativo
python tests/test_d2l_scraper.py

# Modo interativo (ver navegador)
# Escolher opção 5 no menu

# Programaticamente
python -c "
import asyncio
from src.services.d2l_scraper import D2LEventScraper

async def main():
    scraper = D2LEventScraper()
    events = await scraper.scrape_events(course_id='2001540')
    print(f'{len(events)} eventos extraídos')

asyncio.run(main())
"
```

**Saída Esperada:**
```json
{
  "metadata": {
    "source": "d2l_scraper",
    "scraped_at": "2025-11-22T14:30:00",
    "total_events": 5
  },
  "events": [
    {
      "name": "Workshop de Python",
      "date": "2025-11-25",
      "time": "14:00 PM",
      "location": "Room SC 2013",
      "description": "Workshop introdutório sobre Python..."
    }
  ]
}
```

**Documentação Completa:** `docs/scraping/D2L_SCRAPER_README.md`

**Integração com Agente:** `docs/scraping/D2L_AGENT_INTEGRATION.md`

---

### 2. Announcements Scraper

**Arquivo:** `src/scrapers/d2l/announcements.py` (545 linhas)

**Funcionalidade:** Extração dos 5 anúncios mais recentes do D2L com único login

**Status:** ✅ **Produção**

**Medidas Anti-Detecção:**
- ✅ `playwright-stealth` library
- ✅ User-Agent: Firefox 121.0
- ✅ Extra HTTP headers
- ✅ Auto-preenchimento 2FA
- ✅ Delays aleatórios entre interações
- ✅ Bloqueio de recursos desnecessários

**Como Rodar:**

```bash
# Coleta bruta dos anúncios
python3 extract_all_announcements.py

# Resultado esperado
# ✅ Extraction completed successfully!
# 📊 Total announcements: 5
# 📁 Saved to: all_announcements.json
```

**Fluxo Completo de Integração:**

```bash
# Etapa 1: Coleta
python3 extract_all_announcements.py

# Etapa 2: Transformação para cache
python3 transform_cache.py
# ✅ Transformed 5 announcements
# 📁 Saved to: data/d2l_announcements.json

# Etapa 3: Via API (se servidor Flask rodando)
curl -X POST http://localhost:8081/api/announcements/refresh
```

**Atualização Recomendada:** Diariamente via cron

```bash
# Adicionar ao crontab (executa todo dia às 8h)
0 8 * * * cd /path/to/Capstone_Project_AIM && source .venv/bin/activate && python3 extract_all_announcements.py && python3 transform_cache.py
```

**Documentação Completa:** `docs/guides/ANNOUNCEMENTS_USAGE_GUIDE.md`

---

### 3. Links Crawler

**Arquivo:** `src/scrapers/d2l/links_crawler.py` (643 linhas)

**Funcionalidade:** Rastreia todos os links das páginas de conteúdo do D2L e extrai conteúdo de cada URL

**Status:** 📋 **Desenvolvimento**

**Medidas Anti-Detecção:**
- ✅ `playwright-stealth` library (importa e aplica)
- ✅ User-Agent: Firefox 121.0
- ✅ Extra HTTP headers
- ✅ Delays aleatórios (2-4s) entre requisições
- ✅ Auto-preenchimento 2FA com múltiplas estratégias
- ✅ Sanitização de nomes de arquivo

**Como Rodar:**

```bash
# Extração para um curso específico
python src/scrapers/d2l/links_crawler.py --course-id 2001540

# Com curso customizado
python src/scrapers/d2l/links_crawler.py --course-id 2001541

# Resultado
# Cria arquivos JSON individuais para cada página descoberta
# Salva em: data/content_links/ ou similar
```

**Saída Esperada:** Múltiplos arquivos JSON com conteúdo de cada link

**Documentação:** Guia integrado no próprio script

---

### 4. Announcement Content

**Arquivo:** `src/scrapers/d2l/announcement_content.py` (237 linhas)

**Funcionalidade:** Extrator focado em conteúdo completo dos 5 anúncios mais recentes

**Status:** 📋 **Desenvolvimento**

**Medidas Anti-Detecção:**
- ✅ `playwright-stealth` library
- ✅ User-Agent: Firefox 121.0
- ✅ Extra HTTP headers (Accept, Accept-Language, DNT: 1, etc)
- ✅ Bloqueio de recursos desnecessários (imagens, fontes, media)
- ✅ Parsing de elementos `d2l-html-block`

**Como Rodar:**

```bash
# Extração de conteúdo completo dos anúncios
python src/scrapers/d2l/announcement_content.py

# Resultado
# Cria arquivo: announcement_contents.json
# Com conteúdo HTML completo de cada anúncio
```

**Saída Esperada:**
```json
{
  "announcements": [
    {
      "title": "Announcement Title",
      "content": "Full HTML content...",
      "extracted_at": "2025-11-22T13:00:00"
    }
  ]
}
```

**Documentação:** Disponível no script

---

### 5. Content Home

**Arquivo:** `src/scrapers/d2l/content_home.py` (636 linhas)

**Funcionalidade:** Extrai conteúdo da página Home do curso D2L (módulos, links, estrutura principal)

**Status:** 📋 **Desenvolvimento**

**Medidas Anti-Detecção:**
- ✅ `playwright-stealth` library
- ✅ User-Agent: Firefox 121.0
- ✅ Extra HTTP headers
- ✅ Auto-preenchimento 2FA
- ✅ Delays aleatórios
- ✅ Parsing de estrutura de módulos D2L

**Como Rodar:**

```bash
# Extração para um curso específico
python src/scrapers/d2l/content_home.py --course-id 2001540

# Com curso customizado
python src/scrapers/d2l/content_home.py --course-id 2001541

# Resultado
# Arquivo: content_home_2001540.json
```

**Saída Esperada:**
```json
{
  "course_id": "2001540",
  "modules": [
    {
      "name": "Module 1",
      "links": ["url1", "url2"]
    }
  ]
}
```

**Documentação:** Integrada no script

---

### 6. Professor Info

**Arquivo:** `src/scrapers/d2l/professor_info.py` (687 linhas)

**Funcionalidade:** Extrai informações do professor (nome, email, escritório, horários)

**Status:** ✅ **Produção**

**Medidas Anti-Detecção:**
- ✅ `playwright-stealth` library
- ✅ User-Agent: Firefox 121.0
- ✅ Extra HTTP headers
- ✅ Auto-preenchimento 2FA
- ✅ Delays aleatórios
- ✅ Múltiplas estratégias de extração (widget, shadow DOM, full page scan)
- ✅ Debug com screenshots

**Como Rodar:**

```bash
# Extração básica
python extract_professor_info.py --course-id 2001540

# Com debug e screenshots
python extract_professor_info.py --course-id 2001540 --debug

# Custom output
python extract_professor_info.py --course-id 2001540 --output custom_path.json
```

**Saída Esperada:**
```json
{
  "course_id": "2001540",
  "extracted_at": "2025-11-22T13:23:19.567674",
  "name": "Mohammad Noorchenarboo",
  "email": "mnoorchenarboo@fanshawec.ca",
  "office": "By appointment only",
  "office_hours": "Please email to arrange a meeting"
}
```

**Integração:** Cache em `data/course_{COURSE_ID}/professor_info.json`

**Documentação Completa:** `docs/guides/PROFESSOR_EXTRACTION_GUIDE.md`

---

### 7. SharePoint Events

**Arquivo:** `src/scrapers/sharepoint/events.py` (709 linhas)

**Funcionalidade:** Extrai eventos do calendário SharePoint da Fanshawe

**Status:** 📋 **Desenvolvimento**

**Medidas Anti-Detecção:**
- ✅ `playwright-stealth` library
- ✅ User-Agent: Firefox 121.0
- ✅ Extra HTTP headers
- ✅ Auto-preenchimento 2FA
- ✅ Delays aleatórios
- ✅ Múltiplas estratégias (event cards, list cells, aria-labels)

**Como Rodar:**

```bash
# Extração básica
python src/scrapers/sharepoint/events.py

# Com ID de lista customizado (opcional)
# Edite SHAREPOINT_EVENTS_LIST_GUID no script

# Resultado
# Arquivo: sharepoint_events.json (até 100 eventos)
```

**Saída Esperada:**
```json
{
  "source": "sharepoint",
  "events": [
    {
      "title": "Event Name",
      "date": "2025-11-25",
      "location": "Campus Location"
    }
  ]
}
```

**SharePoint Events List GUID:** `d1ad5108-61da-44a6-9b0a-d114a09c5e7e`

**Limite:** 100 eventos por extração

**Documentação:** `docs/scraping/sharepoint_scraper.md`

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
   - 📄 Script wrapper: `extract_all_announcements.py`
   - 📄 Transformador: `src/services/announcement_transformer.py`

3. **Professor Info Scraper**
   - 📄 Guia Completo: `docs/guides/PROFESSOR_EXTRACTION_GUIDE.md`
   - 📄 Script wrapper: `extract_professor_info.py`
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
python3 extract_all_announcements.py

# Verifica resultado
cat all_announcements.json | python -m json.tool
```

### Teste Professor Info

```bash
source .venv/bin/activate

# Com debug
python extract_professor_info.py --course-id 2001540 --debug

# Verifica screenshot gerado
ls -la debug_page.png
```

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