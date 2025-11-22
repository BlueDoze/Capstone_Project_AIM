# D2L Event Scraper - Guia de Uso

## 📋 Visão Geral

O D2L Event Scraper é um módulo automatizado que extrai eventos da plataforma Fanshawe Online (D2L/Brightspace). Ele usa Playwright para navegação autenticada e pode ser testado isoladamente antes de integrar com o sistema principal.

## 🎯 Funcionalidades

- ✅ Login automático no D2L com credenciais seguras
- ✅ Navegação em páginas de cursos específicos
- ✅ Extração de eventos com múltiplas estratégias de parsing
- ✅ Suporte a diferentes formatos de data/hora
- ✅ Captura de screenshots para debug
- ✅ Modo interativo (visualizar navegador)
- ✅ Exportação para JSON compatível com `campus_events.json`
- ✅ Logging detalhado para troubleshooting

## 📁 Arquivos Criados

```
Capstone_Project_AIM/
├── src/services/
│   └── d2l_scraper.py          # Módulo principal do scraper
├── tests/
│   └── test_d2l_scraper.py     # Script de teste isolado
├── .env.example                 # Template de configuração
├── requirements.txt             # Dependências (atualizado)
└── D2L_SCRAPER_README.md       # Este arquivo
```

## 🚀 Instalação

### 1. Instalar Dependências

```bash
# Instalar pacotes Python
pip install -r requirements.txt

# Instalar navegador Chromium para Playwright
playwright install chromium
```

### 2. Configurar Credenciais

```bash
# Copiar template de configuração
cp .env.example .env

# Editar .env e adicionar suas credenciais
nano .env  # ou use seu editor preferido
```

**Arquivo .env:**
```env
D2L_USERNAME=seu_username_fanshawe
D2L_PASSWORD=sua_senha_fanshawe
GEMINI_API_KEY=sua_chave_gemini
```

⚠️ **IMPORTANTE**: Nunca faça commit do arquivo `.env` com credenciais reais!

## 🧪 Teste Isolado

O scraper pode ser testado **completamente isolado** do sistema principal:

```bash
python tests/test_d2l_scraper.py
```

### Menu de Testes Disponíveis

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    D2L EVENT SCRAPER - TESTE ISOLADO                         ║
║                        Fanshawe Navigator Project                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Opções disponíveis:
  1. Teste básico de scraping
  2. Scraping com screenshot (para debug)
  3. Teste com ID de curso customizado
  4. Executar todos os testes
  5. Modo interativo (visualizar navegador)
  0. Sair
```

### Descrição dos Testes

#### 1️⃣ Teste Básico
- Executa login e scraping padrão
- Extrai eventos do curso ID 2001540
- Exibe eventos no terminal
- Opção de salvar em JSON

#### 2️⃣ Scraping com Screenshot
- Igual ao teste básico
- **+ Captura screenshot** da página para debug
- Salva em `data/d2l_screenshot.png`
- Útil para identificar estrutura HTML

#### 3️⃣ Curso Customizado
- Permite testar com qualquer ID de curso D2L
- Você fornece o course_id via input
- Exemplo: `2001541`, `2002340`, etc.

#### 4️⃣ Todos os Testes
- Executa testes 1 e 2 sequencialmente
- Compila todos os eventos
- Salva resultado consolidado

#### 5️⃣ Modo Interativo
- **Abre navegador visível** (não-headless)
- Você pode VER o processo acontecendo
- Útil para debugging visual
- Ver onde o scraper clica e navega

## 💻 Uso Programático

### Exemplo Básico

```python
import asyncio
from src.services.d2l_scraper import D2LEventScraper

async def main():
    # Criar scraper (credenciais do .env)
    scraper = D2LEventScraper()

    # Executar scraping
    events = await scraper.scrape_events(course_id="2001540")

    # Processar eventos
    for event in events:
        print(f"Evento: {event['name']}")
        print(f"Data: {event['date']}")
        print(f"Local: {event['location']}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### Exemplo com Screenshot

```python
import asyncio
from src.services.d2l_scraper import D2LEventScraper

async def main():
    scraper = D2LEventScraper()

    # Scraping + screenshot para debug
    events, screenshot_path = await scraper.scrape_with_screenshot(
        course_id="2001540",
        screenshot_path="debug_page.png"
    )

    print(f"Screenshot salvo em: {screenshot_path}")
    print(f"Total de eventos: {len(events)}")

asyncio.run(main())
```

### Exemplo com Credenciais Customizadas

```python
import asyncio
from src.services.d2l_scraper import D2LEventScraper

async def main():
    # Passar credenciais diretamente (sem .env)
    scraper = D2LEventScraper(
        username="meu_user",
        password="minha_senha",
        headless=False  # Mostrar navegador
    )

    events = await scraper.scrape_events()
    return events

asyncio.run(main())
```

## 🔧 Troubleshooting

### Erro: "Credenciais não fornecidas"

**Solução:**
```bash
# Verificar se .env existe
ls -la .env

# Se não existir, criar a partir do template
cp .env.example .env

# Editar e adicionar credenciais
nano .env
```

### Erro: "Campo de username não encontrado"

**Problema:** Seletores HTML mudaram ou página não carregou

**Solução:**
```bash
# Executar em modo interativo para ver a página
python tests/test_d2l_scraper.py
# Escolher opção 5 (Modo Interativo)
```

**Ou capturar screenshot:**
```bash
# Opção 2 do menu
# Analise o screenshot em data/d2l_screenshot.png
```

### Erro: "Login falhou - ainda na página de login"

**Possíveis causas:**
- Credenciais incorretas
- D2L mudou fluxo de login (SSO, captcha, etc.)
- Sessão expirada

**Solução:**
```bash
# 1. Verificar credenciais manualmente
# Login manual em: https://www.fanshaweonline.ca/d2l/login

# 2. Executar em modo NÃO-headless para ver o que acontece
# Edite d2l_scraper.py temporariamente:
# headless=False

# 3. Verificar se D2L adicionou autenticação de dois fatores
```

### Nenhum Evento Encontrado

**Possíveis razões:**
1. A página realmente não tem eventos no momento
2. Eventos estão em outra seção/aba
3. Seletores HTML precisam ajuste

**Solução:**
```python
# Capturar screenshot para análise
scraper = D2LEventScraper()
events, screenshot = await scraper.scrape_with_screenshot()

# Analise o screenshot e ajuste seletores em:
# src/services/d2l_scraper.py -> método _extract_events()
```

### Erro: "playwright não instalado"

```bash
pip install playwright
playwright install chromium
```

## 🔐 Segurança

### Boas Práticas

✅ **FAÇA:**
- Use variáveis de ambiente (`.env`)
- Adicione `.env` ao `.gitignore`
- Armazene credenciais de forma segura
- Use HTTPS para comunicação
- Implemente rate limiting
- Adicione timeouts adequados

❌ **NÃO FAÇA:**
- Commit de credenciais no código
- Hardcode de senhas
- Compartilhar arquivo `.env`
- Fazer scraping agressivo (risco de ban)

### Rate Limiting

O scraper já implementa delays automáticos:
- Aguarda `networkidle` antes de extrair
- Delay de 2 segundos após carregar conteúdo
- Timeouts de 30 segundos por operação

## 📊 Formato de Saída

### Estrutura JSON

```json
{
  "metadata": {
    "source": "d2l_scraper",
    "scraped_at": "2025-11-18T14:30:00",
    "total_events": 5,
    "scraper_version": "1.0.0"
  },
  "events": [
    {
      "name": "Workshop de Python",
      "date": "2025-11-25",
      "time": "14:00 PM",
      "location": "Room SC 2013",
      "description": "Workshop introdutório sobre Python para iniciantes...",
      "category": "academic",
      "source": "d2l_scraper",
      "scraped_at": "2025-11-18T14:30:00"
    }
  ]
}
```

### Campos Extraídos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome do evento |
| `date` | string | Data (múltiplos formatos suportados) |
| `time` | string | Horário ou "All Day" |
| `location` | string | Localização física ou "Online" |
| `description` | string | Descrição completa (até 200 chars) |
| `category` | string | Categoria (padrão: "academic") |
| `source` | string | Sempre "d2l_scraper" |
| `scraped_at` | string | Timestamp ISO 8601 |

## 🔄 Integração com Sistema Principal

### Opção 1: Endpoint Flask (Recomendado)

Adicione ao `main.py`:

```python
from src.services.d2l_scraper import D2LEventScraper
import asyncio

@app.route("/api/events/refresh-d2l", methods=['POST'])
def refresh_d2l_events():
    """Atualiza eventos do D2L"""
    try:
        scraper = D2LEventScraper()
        events = asyncio.run(scraper.scrape_events())

        # Merge com eventos existentes
        with open('data/campus_events.json', 'r') as f:
            existing_data = json.load(f)

        existing_data['events'].extend(events)

        with open('data/campus_events.json', 'w') as f:
            json.dump(existing_data, f, indent=2)

        return jsonify({
            "status": "success",
            "message": f"{len(events)} eventos adicionados",
            "count": len(events)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
```

### Opção 2: Scheduled Job (Celery/APScheduler)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from src.services.d2l_scraper import D2LEventScraper
import asyncio

def scheduled_scrape():
    """Executa scraping agendado"""
    scraper = D2LEventScraper()
    events = asyncio.run(scraper.scrape_events())
    # Salvar em banco/arquivo

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_scrape, 'interval', hours=6)
scheduler.start()
```

### Opção 3: Ferramenta do Agente Gemini

Adicione como ferramenta disponível para o chatbot:

```python
def get_latest_d2l_events():
    """Função chamável pelo agente Gemini"""
    scraper = D2LEventScraper()
    events = asyncio.run(scraper.scrape_events())
    return events

# Registrar como ferramenta no Gemini function calling
```

## 📝 Customização

### Ajustar Seletores HTML

Se a estrutura da página D2L mudar, edite os seletores em:

**[src/services/d2l_scraper.py:169-180](src/services/d2l_scraper.py#L169-L180)**

```python
calendar_selectors = [
    ".d2l-calendar-event",
    "[class*='calendar'][class*='event']",
    "[class*='upcoming-event']",
    # Adicione novos seletores aqui
]
```

### Adicionar Novos Campos

Edite o método `_parse_event_element()`:

**[src/services/d2l_scraper.py:253-291](src/services/d2l_scraper.py#L253-L291)**

```python
event = {
    "name": title,
    "date": extracted_date,
    # Adicione novos campos aqui
    "organizer": extracted_organizer,
    "cost": extracted_cost,
}
```

## 🐛 Debug Avançado

### Logs Detalhados

O scraper já inclui logging extensivo:

```
[D2L Scraper] Iniciando scraping para curso 2001540...
[D2L Scraper] Fazendo login...
[D2L Scraper] Campo username encontrado: input[name='userName']
[D2L Scraper] Campo password encontrado: input[name='password']
[D2L Scraper] Login completado. URL atual: https://...
[D2L Scraper] Navegando para curso 2001540...
[D2L Scraper] Página do curso carregada!
[D2L Scraper] Extraindo eventos da página...
[D2L Scraper] Encontrados 3 elementos com seletor: .d2l-calendar-event
[D2L Scraper] Evento 1 extraído: Workshop de Python...
[D2L Scraper] 3 eventos extraídos com sucesso!
```

### Capturar HTML da Página

```python
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    # ... login e navegação ...

    # Salvar HTML completo
    html = await page.content()
    with open("page_source.html", "w") as f:
        f.write(html)
```

## 📚 Referências

- [Playwright Python Docs](https://playwright.dev/python/)
- [D2L Brightspace](https://www.d2l.com/)
- [Fanshawe Online](https://www.fanshaweonline.ca/)

## 🤝 Contribuindo

Para melhorar o scraper:

1. Teste com diferentes cursos
2. Identifique novos padrões HTML
3. Adicione seletores robustos
4. Melhore tratamento de erros

## ⚖️ Considerações Legais

⚠️ **IMPORTANTE:**

- Este scraper é para uso **educacional** apenas
- Obtenha **autorização** do departamento de TI da Fanshawe
- Respeite os **Termos de Serviço** do D2L
- Não use para scraping em massa ou comercial
- Implemente **rate limiting** adequado
- Não compartilhe dados pessoais de outros usuários

## 📞 Suporte

Se encontrar problemas:

1. Verifique logs detalhados
2. Capture screenshot da página
3. Execute em modo interativo (opção 5)
4. Verifique se credenciais estão corretas
5. Teste login manual primeiro

---

**Desenvolvido para o Fanshawe Navigator Project**
*Versão 1.0.0 - Novembro 2025*
