# Integração D2L Announcements - Chatbot

## Resumo da Implementação

Este documento descreve a integração completa do scraper D2L de announcements como uma ferramenta do chatbot Fanshawe Navigator.

## Arquitetura

### Componentes Implementados

1. **Classificação de Intenção** (`main.py`)
   - Nova intenção `ANNOUNCEMENTS` adicionada ao sistema de classificação
   - Keywords: announcement, d2l, news, notice, update, brightspace, instructor, etc.
   - Classificação híbrida: keyword matching + Gemini AI

2. **Handler de Announcements** (`main.py:795-849`)
   - Função `handle_announcement_query()`
   - Carrega cache de announcements do arquivo `data/d2l_announcements.json`
   - Formata contexto com informações relevantes (priority, action_required, deadline)
   - Gera respostas usando Gemini AI

3. **Transformer Service** (`src/services/announcement_transformer.py`)
   - Transforma saída do scraper para formato padronizado
   - Adiciona metadados: priority, action_required, deadline
   - Parse de datas e detecção de ações requeridas

4. **API Endpoints** (`main.py:1180-1268`)
   - `POST /api/announcements/refresh` - Atualiza cache executando scraper
   - `GET /api/announcements/status` - Retorna status do cache

## Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO COMPLETO                           │
└─────────────────────────────────────────────────────────────┘

1. COLETA DE DADOS (Manual/Agendada)
   ┌──────────────────────────────┐
   │ extract_all_announcements.py │
   │  - Login D2L (2FA)           │
   │  - Scraping de announcements │
   │  - Saída: all_announcements.json │
   └──────────────────────────────┘
                  ↓
   ┌──────────────────────────────┐
   │ announcement_transformer.py  │
   │  - Parse de datas            │
   │  - Detecção de prioridade    │
   │  - Identificação de ações    │
   └──────────────────────────────┘
                  ↓
   ┌──────────────────────────────┐
   │ data/d2l_announcements.json  │
   │  (Cache padronizado)         │
   └──────────────────────────────┘

2. CONSULTA VIA CHATBOT
   ┌──────────────────────────────┐
   │ Usuário: "Show me recent     │
   │ D2L announcements"           │
   └──────────────────────────────┘
                  ↓
   ┌──────────────────────────────┐
   │ classify_user_intent()       │
   │  → Intent: ANNOUNCEMENTS     │
   └──────────────────────────────┘
                  ↓
   ┌──────────────────────────────┐
   │ handle_announcement_query()  │
   │  - Carrega cache             │
   │  - Formata contexto          │
   │  - Gera resposta com Gemini  │
   └──────────────────────────────┘
                  ↓
   ┌──────────────────────────────┐
   │ Resposta HTML para usuário   │
   └──────────────────────────────┘
```

## Formato de Dados

### Entrada (Scraper Output)
```json
{
  "total_announcements": 5,
  "course": "INFO-6156-(01)-25F",
  "announcements": [
    {
      "index": 1,
      "title": "Reminder: Capstone Class",
      "date": "Nov 18, 2025 10:15 AM",
      "url": "https://...",
      "content": "Dear all,..."
    }
  ]
}
```

### Saída (Cache Transformado)
```json
{
  "announcements": [
    {
      "id": "ann001",
      "title": "Reminder: Capstone Class",
      "date": "2025-11-18",
      "time": "10:15 AM",
      "posted_by": "Instructor",
      "course": "INFO-6156-(01)-25F",
      "content": "Dear all,...",
      "url": "https://...",
      "priority": "high",
      "action_required": true,
      "deadline": ""
    }
  ],
  "last_updated": "2025-11-19T22:51:39.284016",
  "total": 5
}
```

## Uso

### 1. Coletar Announcements do D2L (Manual)

**IMPORTANTE:** O scraper **NÃO executa automaticamente**. Você deve executá-lo manualmente quando quiser atualizar os announcements.

```bash
source .venv/bin/activate
python3 extract_all_announcements.py
```

Isso gera: `all_announcements.json`

### 2. Atualizar Cache do Chatbot

#### Opção A: Via Script (Recomendado)
```bash
python3 transform_cache.py
```

#### Opção B: Via API (se servidor estiver rodando)
```bash
curl -X POST http://localhost:8081/api/announcements/refresh
```

**Nota:** O endpoint API apenas transforma o arquivo `all_announcements.json` existente. Ele **NÃO executa o scraper**.

### 2. Consultar Status do Cache
```bash
curl http://localhost:8081/api/announcements/status
```

### 3. Consultas via Chat

Exemplos de queries que ativam a intenção ANNOUNCEMENTS:

- "What are the latest announcements?"
- "Show me recent D2L news"
- "Any important class updates?"
- "What announcements do I have?"
- "D2L messages from instructor"
- "Recent course news"

## Testes Realizados

### Status do Cache
```bash
$ curl http://localhost:5000/api/announcements/status
{
    "cache_age": "0.1 hours ago",
    "cache_exists": true,
    "course": "INFO-6156-(01)-25F",
    "last_updated": "2025-11-19T22:51:39.284016",
    "status": "cached",
    "total_announcements": 5
}
```

### Consultas de Chat
Todas as 4 queries de teste retornaram respostas corretas:
- ✅ "What are the latest announcements?"
- ✅ "Show me recent D2L news"
- ✅ "Any important class updates?"
- ✅ "What announcements do I have for my course?"

## Arquivos Criados/Modificados

### Arquivos Criados
- `src/services/announcement_transformer.py` - Serviço de transformação
- `data/d2l_announcements.json` - Cache de announcements
- `transform_cache.py` - Script de transformação
- `test_announcements_chat.py` - Script de testes
- `ANNOUNCEMENTS_INTEGRATION.md` - Esta documentação

### Arquivos Modificados
- `main.py`
  - Adicionado prompt `announcements_prompt` (linhas 191-211)
  - Adicionados keywords de announcements em `classify_user_intent()` (linhas 640-643)
  - Atualizado score de classificação (linha 652)
  - Atualizado prompt de classificação Gemini (linhas 664-674)
  - Criada função `handle_announcement_query()` (linhas 795-849)
  - Atualizada mensagem de fallback (linha 860)
  - Adicionado roteamento ANNOUNCEMENTS (linhas 972-975)
  - Criados endpoints API (linhas 1182-1268)

## Detecção Automática de Metadados

### Prioridade (priority)
- **High**: urgent, important, deadline, exam, test, mandatory, required
- **Medium**: update, change, announcement, notice, workshop
- **Low**: demais casos

### Ação Requerida (action_required)
Detecta keywords: submit, complete, attend, register, respond, confirm, required, must, deadline

### Deadline
Extrai datas do conteúdo usando regex patterns

## Próximos Passos (Opcional)

### 1. Refresh Automático Agendado
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    refresh_announcements_background,
    'interval',
    hours=6,
    id='announcement_refresh'
)
scheduler.start()
```

### 2. Notificações de Novos Announcements
- Detectar novos announcements após refresh
- Enviar notificação ao usuário

### 3. Filtros Avançados
- Filtrar por prioridade
- Filtrar por ação requerida
- Filtrar por data

## Limitações Conhecidas

1. **2FA Manual**: O scraper requer autenticação 2FA interativa
2. **Cache pode ficar desatualizado**: Máximo de 6 horas com refresh agendado
3. **Curso específico**: Atualmente configurado para INFO-6156-(01)-25F

## Conclusão

A integração foi implementada com sucesso seguindo o padrão arquitetural existente do sistema (EVENTS e RESTAURANTS). O chatbot agora reconhece consultas sobre announcements e fornece respostas contextualizadas e formatadas com base nos dados extraídos do D2L.

---

**Data**: 19 de Novembro de 2025
**Status**: ✅ Implementação Completa e Testada
