#!/usr/bin/env python3
"""
Script de teste rápido do D2L Scraper (sem menu interativo)
"""

import asyncio
import os
import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.services.d2l_scraper import D2LEventScraper


async def main():
    print("=" * 80)
    print("  D2L SCRAPER - TESTE RÁPIDO")
    print("=" * 80)

    # Verificar credenciais
    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        print("\n❌ ERRO: Credenciais não configuradas!")
        print("Configure D2L_USERNAME e D2L_PASSWORD no arquivo .env")
        return

    print(f"\n✓ Credenciais encontradas")
    print(f"  Username: {username[:3]}***{username[-2:]}")
    print(f"  Password: {'*' * len(password)}")

    # Criar scraper (modo headless)
    scraper = D2LEventScraper(username=username, password=password, headless=True)

    print("\n[Test] Iniciando scraping...")
    print("[Test] Isso pode levar 30-60 segundos...\n")

    try:
        # Executar scraping
        events = await scraper.scrape_events(course_id="2001540")

        print("\n" + "=" * 80)
        print(f"\n✓ Scraping concluído!")
        print(f"  Total de eventos encontrados: {len(events)}\n")

        # Exibir primeiros 5 eventos
        if events:
            print("PRIMEIROS EVENTOS EXTRAÍDOS:")
            print("=" * 80)
            for idx, event in enumerate(events[:5]):
                print(f"\n[Evento #{idx + 1}]")
                print(f"  Nome: {event.get('name', 'N/A')[:80]}")
                print(f"  Data: {event.get('date', 'N/A')}")
                print(f"  Hora: {event.get('time', 'N/A')}")
                print(f"  Local: {event.get('location', 'N/A')[:50]}")
        else:
            print("\n⚠️  Nenhum evento foi encontrado na página.")

        return events

    except Exception as e:
        print(f"\n❌ ERRO durante scraping: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(main())
