# Quick Start: D2L Announcements

## 🚀 Uso Rápido

### 1. Coletar Announcements (Você executa periodicamente)

```bash
source .venv/bin/activate
python3 extract_all_announcements.py
```

### 2. Atualizar Cache do Chatbot

```bash
python3 transform_cache.py
```

**OU** (se servidor estiver rodando):

```bash
curl -X POST http://localhost:8081/api/announcements/refresh
```

### 3. Pronto! 🎉

Agora o chatbot responde automaticamente:
- "What are the latest announcements?"
- "Show me D2L news"
- "Any class updates?"

---

## 📁 Arquivos Importantes

| Arquivo | Descrição |
|---------|-----------|
| `all_announcements.json` | Saída bruta do scraper |
| `data/d2l_announcements.json` | Cache formatado (chatbot lê) |
| `extract_all_announcements.py` | Scraper D2L (você executa) |
| `transform_cache.py` | Converte formato |

---

## ⚙️ Como Funciona

```
┌─────────────────────────────────────────────┐
│ 1. VOCÊ EXECUTA (Manual/Periódico)         │
│    python3 extract_all_announcements.py    │
│         ↓                                   │
│    all_announcements.json                  │
│         ↓                                   │
│    python3 transform_cache.py              │
│         ↓                                   │
│    data/d2l_announcements.json             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 2. CHATBOT RESPONDE (Automático)           │
│    User: "Show me announcements"           │
│         ↓                                   │
│    Lê: data/d2l_announcements.json         │
│         ↓                                   │
│    Gera resposta com Gemini AI             │
└─────────────────────────────────────────────┘
```

---

## ✅ Vantagens

- **Você controla quando atualizar** (não automático)
- **2FA manual** (mais seguro)
- **Respostas instantâneas** (chatbot lê cache)
- **Sem interferência** (scraper separado do servidor)

---

## 📖 Documentação Completa

Veja: [ANNOUNCEMENTS_USAGE_GUIDE.md](ANNOUNCEMENTS_USAGE_GUIDE.md)
