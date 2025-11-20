#!/usr/bin/env python3
"""
Script de teste isolado para o D2L Event Scraper
Execute este script para testar o scraper independentemente do sistema principal.

Uso:
    python tests/test_d2l_scraper.py

Requisitos:
    - Configurar D2L_USERNAME e D2L_PASSWORD no arquivo .env
    - Instalar dependências: pip install -r requirements.txt
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path para imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[Test] Variáveis de ambiente carregadas do .env")
except ImportError:
    print("[Test] WARNING: python-dotenv não instalado. Configure variáveis de ambiente manualmente.")

from src.services.d2l_scraper import D2LEventScraper


def print_separator(char="=", length=80):
    """Imprime uma linha separadora"""
    print(char * length)


def print_header(text):
    """Imprime um cabeçalho formatado"""
    print_separator()
    print(f"  {text}")
    print_separator()


def print_event(event, index):
    """Imprime um evento de forma formatada"""
    print(f"\n[Evento #{index + 1}]")
    print(f"  Nome: {event.get('name', 'N/A')}")
    print(f"  Data: {event.get('date', 'N/A')}")
    print(f"  Hora: {event.get('time', 'N/A')}")
    print(f"  Local: {event.get('location', 'N/A')}")
    print(f"  Categoria: {event.get('category', 'N/A')}")

    description = event.get('description', '')
    if description:
        # Limitar descrição a 100 caracteres para display
        desc_preview = description[:100] + "..." if len(description) > 100 else description
        print(f"  Descrição: {desc_preview}")

    print(f"  Fonte: {event.get('source', 'N/A')}")
    print(f"  Scraped em: {event.get('scraped_at', 'N/A')}")


def save_events_to_json(events, filename="scraped_events.json"):
    """
    Salva eventos em arquivo JSON

    Args:
        events: Lista de eventos
        filename: Nome do arquivo (padrão: scraped_events.json)
    """
    output_path = root_dir / "data" / filename

    # Criar diretório data se não existir
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Estrutura compatível com campus_events.json
    output_data = {
        "metadata": {
            "source": "d2l_scraper",
            "scraped_at": datetime.now().isoformat(),
            "total_events": len(events),
            "scraper_version": "1.0.0"
        },
        "events": events
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n[Test] Eventos salvos em: {output_path}")
    return output_path


async def test_basic_scraping():
    """Teste básico de scraping"""
    print_header("TESTE 1: Scraping Básico de Eventos")

    try:
        # Verificar credenciais
        username = os.getenv("D2L_USERNAME")
        password = os.getenv("D2L_PASSWORD")

        if not username or not password:
            print("\n❌ ERRO: Credenciais não configuradas!")
            print("   Configure D2L_USERNAME e D2L_PASSWORD no arquivo .env")
            print("   Exemplo:")
            print("     D2L_USERNAME=seu_username")
            print("     D2L_PASSWORD=sua_senha")
            return None

        print(f"\n✓ Credenciais encontradas")
        print(f"  Username: {username[:3]}***{username[-2:]}")
        print(f"  Password: {'*' * len(password)}")

        # Criar scraper (modo não-headless para debug visual se necessário)
        # Altere headless=False para ver o navegador em ação
        scraper = D2LEventScraper(username=username, password=password, headless=True)

        print("\n[Test] Iniciando scraping...")
        print("[Test] Isso pode levar 30-60 segundos...\n")

        # Executar scraping
        events = await scraper.scrape_events(course_id="2001540")

        print_separator()
        print(f"\n✓ Scraping concluído!")
        print(f"  Total de eventos encontrados: {len(events)}\n")

        # Exibir eventos
        if events:
            print_header("EVENTOS EXTRAÍDOS")
            for idx, event in enumerate(events):
                print_event(event, idx)
        else:
            print("\n⚠️  Nenhum evento foi encontrado na página.")
            print("   Possíveis razões:")
            print("   - A página não contém eventos no momento")
            print("   - Os seletores HTML precisam ser ajustados")
            print("   - O conteúdo está em uma área diferente da página")

        return events

    except ValueError as e:
        print(f"\n❌ ERRO de configuração: {str(e)}")
        return None
    except Exception as e:
        print(f"\n❌ ERRO durante scraping: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_with_screenshot():
    """Teste com captura de screenshot para debug"""
    print_header("TESTE 2: Scraping com Screenshot para Debug")

    try:
        username = os.getenv("D2L_USERNAME")
        password = os.getenv("D2L_PASSWORD")

        if not username or not password:
            print("\n❌ Credenciais não configuradas. Pulando teste.")
            return None

        scraper = D2LEventScraper(username=username, password=password, headless=True)

        print("\n[Test] Executando scraping com screenshot...")
        screenshot_path = str(root_dir / "data" / "d2l_screenshot.png")

        events, saved_screenshot = await scraper.scrape_with_screenshot(
            course_id="2001540",
            screenshot_path=screenshot_path
        )

        print(f"\n✓ Screenshot salvo em: {saved_screenshot}")
        print(f"✓ Total de eventos: {len(events)}")

        return events

    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_different_course():
    """Teste com ID de curso diferente"""
    print_header("TESTE 3: Teste com ID de Curso Customizado")

    course_id = input("\nDigite o ID do curso D2L (ou Enter para pular): ").strip()

    if not course_id:
        print("[Test] Teste pulado.")
        return None

    try:
        username = os.getenv("D2L_USERNAME")
        password = os.getenv("D2L_PASSWORD")

        scraper = D2LEventScraper(username=username, password=password, headless=True)

        print(f"\n[Test] Scraping curso {course_id}...")
        events = await scraper.scrape_events(course_id=course_id)

        print(f"\n✓ Total de eventos: {len(events)}")

        return events

    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        return None


def display_menu():
    """Exibe menu de opções"""
    print_header("D2L EVENT SCRAPER - MENU DE TESTES")
    print("\nOpções disponíveis:")
    print("  1. Teste básico de scraping")
    print("  2. Scraping com screenshot (para debug)")
    print("  3. Teste com ID de curso customizado")
    print("  4. Executar todos os testes")
    print("  5. Modo interativo (visualizar navegador)")
    print("  0. Sair")
    print()


async def interactive_mode():
    """Modo interativo com visualização do navegador"""
    print_header("TESTE 5: Modo Interativo (Browser Visível)")

    try:
        username = os.getenv("D2L_USERNAME")
        password = os.getenv("D2L_PASSWORD")

        if not username or not password:
            print("\n❌ Credenciais não configuradas.")
            return None

        print("\n[Test] Abrindo navegador em modo visível...")
        print("[Test] Você poderá ver o processo de login e scraping!\n")

        # Criar scraper em modo NÃO-headless
        scraper = D2LEventScraper(username=username, password=password, headless=False)

        events = await scraper.scrape_events(course_id="2001540")

        print(f"\n✓ Total de eventos: {len(events)}")

        return events

    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        return None


async def run_all_tests():
    """Executa todos os testes sequencialmente"""
    print_header("EXECUTANDO TODOS OS TESTES")

    all_events = []

    # Teste 1: Básico
    events1 = await test_basic_scraping()
    if events1:
        all_events.extend(events1)

    print("\n" + "=" * 80 + "\n")

    # Teste 2: Com screenshot
    events2 = await test_with_screenshot()

    print("\n" + "=" * 80 + "\n")

    # Resumo final
    print_header("RESUMO DOS TESTES")
    print(f"\nTotal de eventos coletados: {len(all_events)}")

    if all_events:
        # Salvar eventos
        save_events_to_json(all_events)

    return all_events


async def main():
    """Função principal"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    D2L EVENT SCRAPER - TESTE ISOLADO                         ║
║                        Fanshawe Navigator Project                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Verificar se credenciais estão configuradas
    if not os.getenv("D2L_USERNAME") or not os.getenv("D2L_PASSWORD"):
        print("\n⚠️  AVISO: Credenciais não encontradas!")
        print("\nPara usar este scraper, você precisa:")
        print("  1. Criar um arquivo .env na raiz do projeto")
        print("  2. Adicionar suas credenciais do Fanshawe D2L:")
        print()
        print("     D2L_USERNAME=seu_username_fanshawe")
        print("     D2L_PASSWORD=sua_senha")
        print()
        print("  3. Instalar dependências:")
        print("     pip install playwright python-dotenv")
        print("     playwright install chromium")
        print()
        input("Pressione Enter para continuar mesmo assim (o teste falhará)...")

    while True:
        display_menu()
        choice = input("Escolha uma opção: ").strip()

        if choice == "0":
            print("\n[Test] Encerrando...\n")
            break
        elif choice == "1":
            events = await test_basic_scraping()
            if events:
                save_choice = input("\nSalvar eventos em JSON? (s/n): ").strip().lower()
                if save_choice == 's':
                    save_events_to_json(events)
        elif choice == "2":
            events = await test_with_screenshot()
            if events:
                save_choice = input("\nSalvar eventos em JSON? (s/n): ").strip().lower()
                if save_choice == 's':
                    save_events_to_json(events)
        elif choice == "3":
            events = await test_different_course()
            if events:
                save_choice = input("\nSalvar eventos em JSON? (s/n): ").strip().lower()
                if save_choice == 's':
                    save_events_to_json(events)
        elif choice == "4":
            events = await run_all_tests()
        elif choice == "5":
            events = await interactive_mode()
            if events:
                save_choice = input("\nSalvar eventos em JSON? (s/n): ").strip().lower()
                if save_choice == 's':
                    save_events_to_json(events)
        else:
            print("\n❌ Opção inválida. Tente novamente.\n")
            continue

        print("\n" + "=" * 80 + "\n")
        input("Pressione Enter para continuar...")
        print("\n" * 2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[Test] Interrompido pelo usuário. Encerrando...\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
