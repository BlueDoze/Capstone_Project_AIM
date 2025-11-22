# Integração do D2L Scraper como Ferramenta do Agente

## 🎯 Objetivo

Transformar o D2L Scraper em uma ferramenta que o agente Gemini pode chamar automaticamente quando usuários perguntarem sobre eventos do campus.

## 🔧 Implementação

### Passo 1: Criar Wrapper de Ferramenta

Crie o arquivo: `src/tools/d2l_events_tool.py`

```python
"""
Ferramenta para o agente Gemini obter eventos do D2L
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from src.services.d2l_scraper import D2LEventScraper


class D2LEventsTool:
    """
    Ferramenta que permite ao agente Gemini acessar eventos do D2L.
    """

    def __init__(self):
        self.scraper = None
        self.cache = {
            "events": [],
            "last_updated": None,
            "cache_duration_minutes": 60  # Cache de 1 hora
        }

    def _is_cache_valid(self) -> bool:
        """Verifica se cache ainda é válido"""
        if not self.cache["last_updated"]:
            return False

        last_update = datetime.fromisoformat(self.cache["last_updated"])
        now = datetime.now()
        diff_minutes = (now - last_update).total_seconds() / 60

        return diff_minutes < self.cache["cache_duration_minutes"]

    async def get_events(
        self,
        course_id: str = "2001540",
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Obtém eventos do D2L.

        Args:
            course_id: ID do curso D2L
            force_refresh: Forçar atualização mesmo com cache válido

        Returns:
            Lista de eventos
        """
        # Verificar cache
        if not force_refresh and self._is_cache_valid():
            print(f"[D2L Tool] Usando cache ({len(self.cache['events'])} eventos)")
            return self.cache["events"]

        # Scraping
        try:
            print(f"[D2L Tool] Buscando eventos do D2L (curso {course_id})...")

            if not self.scraper:
                self.scraper = D2LEventScraper()

            events = await self.scraper.scrape_events(course_id=course_id)

            # Atualizar cache
            self.cache["events"] = events
            self.cache["last_updated"] = datetime.now().isoformat()

            print(f"[D2L Tool] {len(events)} eventos obtidos e em cache")
            return events

        except Exception as e:
            print(f"[D2L Tool] Erro ao buscar eventos: {str(e)}")
            # Retornar cache antigo se disponível
            if self.cache["events"]:
                print(f"[D2L Tool] Retornando cache antigo devido a erro")
                return self.cache["events"]
            return []

    def get_events_sync(
        self,
        course_id: str = "2001540",
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Versão síncrona de get_events para facilitar integração.

        Args:
            course_id: ID do curso D2L
            force_refresh: Forçar atualização

        Returns:
            Lista de eventos
        """
        return asyncio.run(self.get_events(course_id, force_refresh))

    def format_events_for_agent(
        self,
        events: List[Dict[str, Any]],
        limit: int = 10
    ) -> str:
        """
        Formata eventos para o agente Gemini processar.

        Args:
            events: Lista de eventos
            limit: Máximo de eventos a retornar

        Returns:
            String formatada com eventos
        """
        if not events:
            return "Nenhum evento encontrado no D2L no momento."

        # Limitar quantidade
        events_to_show = events[:limit]

        formatted = f"📅 Eventos do Fanshawe D2L ({len(events_to_show)} eventos):\n\n"

        for idx, event in enumerate(events_to_show, 1):
            formatted += f"{idx}. {event.get('name', 'Sem título')}\n"
            formatted += f"   📆 Data: {event.get('date', 'TBD')}\n"
            formatted += f"   🕐 Hora: {event.get('time', 'TBD')}\n"
            formatted += f"   📍 Local: {event.get('location', 'TBD')}\n"

            description = event.get('description', '')
            if description:
                desc_preview = description[:80] + "..." if len(description) > 80 else description
                formatted += f"   📝 {desc_preview}\n"

            formatted += "\n"

        if len(events) > limit:
            formatted += f"\n... e mais {len(events) - limit} eventos.\n"

        return formatted

    def search_events(
        self,
        query: str,
        course_id: str = "2001540"
    ) -> List[Dict[str, Any]]:
        """
        Busca eventos que correspondem a uma query.

        Args:
            query: Termo de busca
            course_id: ID do curso

        Returns:
            Eventos filtrados
        """
        all_events = self.get_events_sync(course_id=course_id)

        query_lower = query.lower()

        filtered = [
            event for event in all_events
            if (
                query_lower in event.get('name', '').lower() or
                query_lower in event.get('description', '').lower() or
                query_lower in event.get('location', '').lower()
            )
        ]

        return filtered


# Instância global (singleton)
d2l_tool = D2LEventsTool()


# Função para uso pelo agente Gemini
def get_d2l_events(
    search_query: str = None,
    course_id: str = "2001540",
    limit: int = 10
) -> str:
    """
    Obtém eventos do D2L Fanshawe.

    Esta função pode ser chamada pelo agente Gemini para responder perguntas
    sobre eventos do campus vindos do sistema D2L.

    Args:
        search_query: Termo de busca opcional para filtrar eventos
        course_id: ID do curso D2L (padrão: 2001540)
        limit: Máximo de eventos a retornar (padrão: 10)

    Returns:
        String formatada com eventos para o agente processar
    """
    try:
        if search_query:
            events = d2l_tool.search_events(search_query, course_id)
            if events:
                result = f"Eventos encontrados para '{search_query}':\n\n"
                result += d2l_tool.format_events_for_agent(events, limit)
                return result
            else:
                return f"Nenhum evento encontrado para '{search_query}'."
        else:
            events = d2l_tool.get_events_sync(course_id)
            return d2l_tool.format_events_for_agent(events, limit)

    except Exception as e:
        return f"Erro ao buscar eventos do D2L: {str(e)}"
```

### Passo 2: Registrar Ferramenta no Gemini

Modifique `main.py` para incluir a ferramenta:

```python
import google.generativeai as genai
from src.tools.d2l_events_tool import get_d2l_events

# Configurar Gemini com ferramentas
tools = [
    {
        "name": "get_d2l_events",
        "description": (
            "Obtém eventos do Fanshawe D2L (sistema de gerenciamento de aprendizado). "
            "Use esta ferramenta quando o usuário perguntar sobre eventos do campus, "
            "calendário acadêmico, prazos de curso, ou atividades escolares. "
            "Você pode buscar eventos específicos usando search_query."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "Termo de busca opcional para filtrar eventos (ex: 'workshop', 'python', 'networking')"
                },
                "course_id": {
                    "type": "string",
                    "description": "ID do curso D2L (padrão: 2001540)",
                    "default": "2001540"
                },
                "limit": {
                    "type": "integer",
                    "description": "Máximo de eventos a retornar (padrão: 10)",
                    "default": 10
                }
            },
            "required": []
        }
    }
]

# Criar modelo com ferramentas
model = genai.GenerativeModel(
    model_name='gemini-1.5-pro',
    tools=[get_d2l_events]  # Registrar função Python diretamente
)
```

### Passo 3: Processar Chamadas de Ferramenta

```python
@app.route("/api/chat", methods=['POST'])
def chat():
    """Endpoint do chatbot com suporte a ferramentas"""
    user_message = request.json.get('message')

    # Criar chat
    chat = model.start_chat(enable_automatic_function_calling=True)

    # Enviar mensagem
    response = chat.send_message(user_message)

    # Gemini automaticamente chamará get_d2l_events se necessário
    return jsonify({
        "response": response.text
    })
```

## 📝 Exemplos de Uso

### Conversa 1: Listar Eventos

**Usuário:**
> Quais eventos estão acontecendo no campus esta semana?

**Agente (internamente):**
- Detecta que precisa de eventos
- Chama `get_d2l_events()`
- Recebe lista de eventos formatada

**Resposta:**
> Aqui estão os eventos desta semana no Fanshawe:
>
> 1. **Workshop de Python**
>    - 📆 25 de Novembro, 2025
>    - 🕐 14:00 PM
>    - 📍 Room SC 2013
>    - Aprenda fundamentos de Python!
>
> 2. **Networking Night**
>    - 📆 27 de Novembro, 2025
>    - 🕐 18:00 PM
>    - 📍 Student Centre
>    - Conecte-se com profissionais da área
>
> ...

### Conversa 2: Busca Específica

**Usuário:**
> Tem algum evento sobre inteligência artificial?

**Agente (internamente):**
- Chama `get_d2l_events(search_query="inteligência artificial")`
- Filtra eventos relevantes

**Resposta:**
> Sim! Encontrei 2 eventos sobre inteligência artificial:
>
> 1. **AI Workshop - Introdução ao Machine Learning**
>    - 📆 30 de Novembro, 2025
>    - 🕐 15:00 PM
>    - 📍 Room F 3020
>
> 2. **Palestra: Ética em IA**
>    - 📆 2 de Dezembro, 2025
>    - 🕐 10:00 AM
>    - 📍 Online (Zoom)

### Conversa 3: Integração com Navegação

**Usuário:**
> Como chego no evento de Python?

**Agente (internamente):**
1. Chama `get_d2l_events(search_query="python")`
2. Identifica local: "Room SC 2013"
3. Usa sistema de navegação existente

**Resposta:**
> O Workshop de Python será na sala SC 2013!
>
> 📍 Para chegar lá:
> 1. Entre pela entrada principal do Student Centre
> 2. Suba para o segundo andar
> 3. Vire à direita no corredor principal
> 4. A sala 2013 estará à sua esquerda
>
> [Visualizar mapa 3D]

## 🔄 Implementação com Cache Inteligente

### Estratégia de Cache em Camadas

```python
class SmartD2LCache:
    """Cache inteligente multi-camadas para eventos D2L"""

    def __init__(self):
        # Camada 1: Cache em memória (rápido, volátil)
        self.memory_cache = {}

        # Camada 2: Cache em arquivo (persistente)
        self.file_cache_path = "data/d2l_events_cache.json"

        # Camada 3: Fallback para eventos estáticos
        self.fallback_path = "data/campus_events.json"

    def get_events(self, force_refresh=False):
        """
        Estratégia multi-camada:
        1. Tenta cache em memória
        2. Tenta cache em arquivo
        3. Faz scraping novo
        4. Fallback para eventos estáticos
        """
        # Camada 1: Memória
        if not force_refresh and self._is_memory_cache_valid():
            return self.memory_cache["events"]

        # Camada 2: Arquivo
        if not force_refresh and self._is_file_cache_valid():
            return self._load_file_cache()

        # Camada 3: Scraping novo
        try:
            events = self._scrape_fresh()
            self._update_caches(events)
            return events
        except Exception as e:
            print(f"Scraping falhou: {e}")

        # Camada 4: Fallback
        return self._load_fallback()
```

## 🎨 Interface Admin para Gerenciar Scraping

### Endpoint de Admin

```python
@app.route("/admin/d2l-scraper", methods=['GET'])
@require_auth  # Adicione autenticação
def d2l_scraper_admin():
    """Painel de controle do D2L Scraper"""
    return render_template("admin/d2l_scraper.html")


@app.route("/admin/api/d2l/refresh", methods=['POST'])
@require_auth
def admin_refresh_d2l():
    """Força refresh de eventos D2L"""
    try:
        events = d2l_tool.get_events_sync(force_refresh=True)
        return jsonify({
            "status": "success",
            "message": f"{len(events)} eventos atualizados",
            "events": events
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/admin/api/d2l/cache-status", methods=['GET'])
@require_auth
def admin_cache_status():
    """Status do cache de eventos"""
    return jsonify({
        "cache_size": len(d2l_tool.cache["events"]),
        "last_updated": d2l_tool.cache["last_updated"],
        "is_valid": d2l_tool._is_cache_valid()
    })
```

### Template HTML Simples

```html
<!-- templates/admin/d2l_scraper.html -->
<!DOCTYPE html>
<html>
<head>
    <title>D2L Scraper Admin</title>
</head>
<body>
    <h1>D2L Event Scraper - Admin Panel</h1>

    <div id="cache-status">
        <h2>Status do Cache</h2>
        <p>Última atualização: <span id="last-update">Carregando...</span></p>
        <p>Eventos em cache: <span id="cache-size">Carregando...</span></p>
    </div>

    <button onclick="refreshEvents()">🔄 Atualizar Eventos Agora</button>

    <div id="events-list"></div>

    <script>
        async function refreshEvents() {
            const response = await fetch('/admin/api/d2l/refresh', {
                method: 'POST'
            });
            const data = await response.json();
            alert(data.message);
            loadCacheStatus();
        }

        async function loadCacheStatus() {
            const response = await fetch('/admin/api/d2l/cache-status');
            const data = await response.json();
            document.getElementById('last-update').textContent = data.last_updated;
            document.getElementById('cache-size').textContent = data.cache_size;
        }

        loadCacheStatus();
    </script>
</body>
</html>
```

## 📊 Monitoramento e Logs

### Sistema de Logging

```python
import logging
from datetime import datetime

# Configurar logger específico para D2L
d2l_logger = logging.getLogger('d2l_scraper')
d2l_logger.setLevel(logging.INFO)

# Handler para arquivo
file_handler = logging.FileHandler('logs/d2l_scraper.log')
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
d2l_logger.addHandler(file_handler)


class MonitoredD2LTool(D2LEventsTool):
    """Versão com monitoramento"""

    def get_events_sync(self, course_id="2001540", force_refresh=False):
        start_time = datetime.now()

        try:
            d2l_logger.info(f"Iniciando scraping - Curso: {course_id}, Force: {force_refresh}")
            events = super().get_events_sync(course_id, force_refresh)

            duration = (datetime.now() - start_time).total_seconds()
            d2l_logger.info(
                f"Scraping concluído - {len(events)} eventos, {duration:.2f}s"
            )

            return events

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            d2l_logger.error(
                f"Scraping falhou após {duration:.2f}s - Erro: {str(e)}"
            )
            raise
```

## 🚀 Deploy em Produção

### Variáveis de Ambiente (Production)

```bash
# .env.production
D2L_USERNAME=service_account_username
D2L_PASSWORD=secure_password_here
D2L_CACHE_DURATION_MINUTES=120
D2L_SCRAPING_ENABLED=true
D2L_HEADLESS=true
```

### Scheduled Jobs (Celery)

```python
from celery import Celery
from celery.schedules import crontab

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def scheduled_d2l_scrape():
    """Tarefa agendada de scraping"""
    from src.tools.d2l_events_tool import d2l_tool

    try:
        events = d2l_tool.get_events_sync(force_refresh=True)
        print(f"[Scheduled] {len(events)} eventos atualizados")
        return len(events)
    except Exception as e:
        print(f"[Scheduled] Erro: {e}")
        return 0


# Agendar para rodar a cada 6 horas
celery.conf.beat_schedule = {
    'scrape-d2l-events': {
        'task': 'tasks.scheduled_d2l_scrape',
        'schedule': crontab(hour='*/6'),  # A cada 6 horas
    },
}
```

## 🧪 Testes Unitários

```python
# tests/test_d2l_tool.py
import unittest
from src.tools.d2l_events_tool import D2LEventsTool

class TestD2LTool(unittest.TestCase):

    def setUp(self):
        self.tool = D2LEventsTool()

    def test_cache_validation(self):
        """Testa validação de cache"""
        self.assertFalse(self.tool._is_cache_valid())

        # Simula cache recente
        from datetime import datetime
        self.tool.cache["last_updated"] = datetime.now().isoformat()
        self.assertTrue(self.tool._is_cache_valid())

    def test_event_formatting(self):
        """Testa formatação de eventos"""
        mock_events = [
            {
                "name": "Test Event",
                "date": "2025-11-20",
                "time": "14:00",
                "location": "Room 101"
            }
        ]

        formatted = self.tool.format_events_for_agent(mock_events)
        self.assertIn("Test Event", formatted)
        self.assertIn("2025-11-20", formatted)

if __name__ == '__main__':
    unittest.main()
```

---

**Com esta integração, o D2L Scraper se torna uma ferramenta poderosa do seu agente Gemini!** 🎉
