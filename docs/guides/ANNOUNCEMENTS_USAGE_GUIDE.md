# Guia de Uso: D2L Announcements no Chatbot

## 📋 Visão Geral

O chatbot agora pode responder perguntas sobre announcements do D2L. O sistema funciona em **2 etapas simples**:

1. **Você executa o scraper manualmente** (periodicamente)
2. **O chatbot lê os resultados** e responde automaticamente

---

## 🚀 Como Usar

### Etapa 1: Coletar Announcements do D2L

Execute o scraper **quando quiser atualizar** os announcements (diariamente, semanalmente, etc.):

```bash
# Ative o ambiente virtual
source .venv/bin/activate

# Execute o scraper D2L
python3 extract_all_announcements.py
```

**O que acontece:**
- Abre navegador (headless)
- Faz login no D2L (com 2FA)
- Extrai os 5 announcements mais recentes
- Salva em `all_announcements.json`

**Saída esperada:**
```
✅ Extraction completed successfully!
📊 Total announcements: 5
✅ Successful: 5
❌ Failed: 0
📁 Saved to: all_announcements.json
```

---

### Etapa 2A: Transformar para Cache (Via Script)

```bash
# Transforma all_announcements.json → data/d2l_announcements.json
python3 transform_cache.py
```

**Saída esperada:**
```
✅ Transformed 5 announcements
📁 Saved to: data/d2l_announcements.json
📅 Last updated: 2025-11-19T22:51:39.284016
```

---

### Etapa 2B: Transformar para Cache (Via API)

Se o servidor Flask estiver rodando:

```bash
curl -X POST http://localhost:8081/api/announcements/refresh
```

**Resposta esperada:**
```json
{
  "status": "success",
  "message": "Transformed 5 announcements",
  "last_updated": "2025-11-19T22:51:39.284016",
  "total_announcements": 5
}
```

---

### Etapa 3: Consultar via Chatbot

Agora os usuários podem fazer perguntas naturalmente:

**Exemplos de Queries:**
- "What are the latest announcements?"
- "Show me recent D2L news"
- "Any important class updates?"
- "What announcements do I have?"
- "D2L messages from instructor"
- "Quais são os anúncios recentes?"

**Resposta do Chatbot:**

O chatbot vai:
1. Detectar a intenção `ANNOUNCEMENTS`
2. Carregar `data/d2l_announcements.json`
3. Gerar resposta contextualizada com Gemini AI
4. Retornar HTML formatado com:
   - Títulos dos announcements
   - Datas de postagem
   - Conteúdo resumido
   - Prioridades (high/medium/low)
   - Ações requeridas
   - Links para D2L

---

## 📁 Estrutura de Arquivos

```
/Capstone_Project_AIM/
├── extract_all_announcements.py      # Scraper D2L (você executa)
├── all_announcements.json            # Saída bruta do scraper
├── transform_cache.py                # Script de transformação
├── data/
│   └── d2l_announcements.json       # Cache formatado (chatbot lê)
└── src/services/
    └── announcement_transformer.py   # Lógica de transformação
```

---

## ⏱️ Fluxo de Atualização Recomendado

### Opção 1: Manual (Quando Necessário)
Execute o scraper apenas quando souber que há novos announcements.

### Opção 2: Cron Job Diário
```bash
# Edite crontab
crontab -e

# Adicione (executa todo dia às 8h da manhã)
0 8 * * * cd /home/luizeng/Documents/fanshawe_repo/Capstone_Project_AIM && source .venv/bin/activate && python3 extract_all_announcements.py && python3 transform_cache.py
```

### Opção 3: Script Semanal
Execute antes da aula toda segunda-feira:

```bash
# Cria script update_announcements.sh
#!/bin/bash
cd /home/luizeng/Documents/fanshawe_repo/Capstone_Project_AIM
source .venv/bin/activate
python3 extract_all_announcements.py
python3 transform_cache.py
echo "✅ Announcements updated on $(date)"
```

---

## 🔍 Verificar Status

### Via API
```bash
curl http://localhost:8081/api/announcements/status
```

**Resposta:**
```json
{
  "status": "cached",
  "cache_exists": true,
  "total_announcements": 5,
  "last_updated": "2025-11-19T22:51:39.284016",
  "cache_age": "2.3 hours ago",
  "course": "INFO-6156-(01)-25F"
}
```

### Via Arquivo
```bash
ls -lh data/d2l_announcements.json
cat data/d2l_announcements.json | python3 -m json.tool
```

---

## 🎯 Vantagens desta Abordagem

### ✅ Controle Total
- **Você decide quando atualizar** (não executa automaticamente)
- **Evita execuções desnecessárias** (economiza recursos)
- **Não interfere com o servidor Flask** (roda separadamente)

### ✅ Segurança
- **2FA você controla** (não precisa automatizar autenticação)
- **Credenciais seguras** (apenas no .env)

### ✅ Confiabilidade
- **Cache persistente** (não perde dados se servidor reiniciar)
- **Respostas instantâneas** (chatbot lê arquivo, não executa scraper)

### ✅ Flexibilidade
- **Fácil debug** (pode inspecionar all_announcements.json)
- **Fácil teste** (pode editar manualmente o cache)

---

## ⚠️ Troubleshooting

### Problema: "Announcement information is currently unavailable"
**Solução:** Execute o scraper e transforme o cache:
```bash
python3 extract_all_announcements.py
python3 transform_cache.py
```

### Problema: "all_announcements.json not found"
**Solução:** Execute o scraper primeiro:
```bash
python3 extract_all_announcements.py
```

### Problema: Cache antigo (> 7 dias)
**Solução:** Execute atualização:
```bash
python3 extract_all_announcements.py && python3 transform_cache.py
```

### Problema: 2FA não funciona
**Solução:** Verifique:
- Terminal exibe código de verificação?
- Credenciais corretas no `.env`?
- Navegador headless funcionando?

---

## 📊 Exemplo Completo de Uso

```bash
# 1. Coletar announcements do D2L
$ python3 extract_all_announcements.py
🔐 Logging in...
📧 Email: your-email@fanshaweonline.ca
🔑 Password: ********
🔄 Navigating to D2L...
✅ Extraction completed!
📊 Total: 5 announcements

# 2. Transformar para cache
$ python3 transform_cache.py
✅ Transformed 5 announcements
📁 Saved to: data/d2l_announcements.json

# 3. Verificar status
$ curl http://localhost:8081/api/announcements/status
{
  "status": "cached",
  "total_announcements": 5,
  "cache_age": "0.1 hours ago"
}

# 4. Consultar via chatbot (no navegador)
User: "What are the latest announcements?"
Bot: "Here are your recent D2L announcements:

**Reminder: Capstone Class & Agentic AI Workshop**
- Posted: November 18, 2025
- Content: Dear all, Please note that we will be meeting...
- ⚠️ Action Required
- Priority: high
- Link: https://www.fanshaweonline.ca/d2l/le/news/..."
```

---

## 🎓 Resumo do Workflow

```
┌─────────────────────────────────────────────────────────┐
│                    WORKFLOW COMPLETO                    │
└─────────────────────────────────────────────────────────┘

VOCÊ (Manual):
1. python3 extract_all_announcements.py
   → Gera: all_announcements.json

2. python3 transform_cache.py
   → Gera: data/d2l_announcements.json

USUÁRIOS (Automático):
3. Perguntam no chat: "Show me announcements"
   → Chatbot lê: data/d2l_announcements.json
   → Responde com Gemini AI
```

---

## 📝 Notas Importantes

1. **O scraper NÃO roda automaticamente** - você executa quando quiser
2. **O chatbot APENAS LÊ o cache** - não executa o scraper
3. **Cache persiste entre reinicializações** - dados não se perdem
4. **2FA é sempre manual** - mais seguro e controlado
5. **Você controla a frequência** - diária, semanal, ou sob demanda

---

**Data:** 19 de Novembro de 2025
**Status:** ✅ Sistema Simplificado e Pronto para Uso
