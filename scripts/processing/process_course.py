"""
Script orquestrador para processar cursos D2L completos.
Faz LOGIN UMA ÚNICA VEZ e reutiliza a sessão para todos os cursos.

Uso:
    # Processar um curso
    python3 process_course.py --course-id 2001539

    # Processar múltiplos cursos (login único compartilhado)
    python3 process_course.py --course-ids 2001540 2001539
"""

import asyncio
import argparse
import sys
import os
import random
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

# Importar funções dos scripts existentes
from extract_content_home import extract_content_home, try_login_if_needed
from extract_links_crawler import crawl_links

load_dotenv()


async def process_single_course_with_shared_browser(course_id: str, page, browser_context):
    """Processa um único curso usando browser compartilhado (já logado)."""

    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + f"  PROCESSANDO CURSO: {course_id}".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝\n")

    try:
        # ETAPA 1: Extrair página Home (usando browser compartilhado)
        print("="*80)
        print(f"ETAPA 1/2: EXTRAINDO PÁGINA HOME DO CURSO {course_id}")
        print("="*80 + "\n")

        output_file = f'content_home_{course_id}.json'
        home_data = await extract_content_home(course_id, output_file, page, browser_context)

        print(f"\n✅ Home page extraída com sucesso!")
        print(f"   - Arquivo: {output_file}")
        print(f"   - Links encontrados: {home_data['html_structure']['links_count']}\n")

        # ETAPA 2: Crawl dos links (usando browser compartilhado)
        print("="*80)
        print(f"ETAPA 2/2: CRAWLING DE LINKS DO CURSO {course_id}")
        print("="*80 + "\n")

        output_dir = f'/home/luizeng/Documents/fanshawe_repo/Capstone_Project_AIM/data/course_{course_id}'
        summary = await crawl_links(course_id, output_file, output_dir)

        print(f"\n✅ Crawler completado!")
        print(f"   - Links processados: {summary['successful']}/{summary['total_links']}")
        print(f"   - Diretório: {output_dir}\n")

        # RESUMO FINAL DO CURSO
        print("\n" + "╔" + "="*78 + "╗")
        print("║" + " "*78 + "║")
        print("║" + f"  ✅ CURSO {course_id} PROCESSADO COM SUCESSO!".center(78) + "║")
        print("║" + " "*78 + "║")
        print("╚" + "="*78 + "╝")
        print(f"\n📊 Estatísticas:")
        print(f"   - Página home: {output_file}")
        print(f"   - Links crawled: {summary['successful']}/{summary['total_links']}")
        print(f"   - Falhas: {summary['failed']}")
        print(f"   - Diretório: {output_dir}")
        print("="*80 + "\n")

        return {
            'course_id': course_id,
            'status': 'success',
            'home_file': output_file,
            'output_dir': output_dir,
            'links_processed': summary['successful'],
            'links_failed': summary['failed'],
            'total_links': summary['total_links']
        }

    except Exception as e:
        print(f"\n❌ ERRO ao processar curso {course_id}:")
        print(f"   {str(e)}\n")

        return {
            'course_id': course_id,
            'status': 'failed',
            'error': str(e)
        }


async def process_all_courses_with_single_login(course_ids: list):
    """Processa todos os cursos com UM ÚNICO LOGIN compartilhado."""

    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  PROCESSAMENTO DE CURSOS D2L - LOGIN ÚNICO".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print(f"\n📚 Total de cursos a processar: {len(course_ids)}")
    print(f"   IDs: {', '.join(course_ids)}")
    print(f"   🔑 Modo: LOGIN ÚNICO (reutilizado para todos os cursos)\n")

    # Obter credenciais
    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME e D2L_PASSWORD no .env")

    async with async_playwright() as p:
        # Criar browser ÚNICO
        print("🌐 Criando browser compartilhado...")
        browser = await p.firefox.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            locale='en-US',
            timezone_id='America/Toronto',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        )

        # Bloquear recursos desnecessários
        await context.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font", "media"] else route.continue_())

        page = await context.new_page()

        # Aplicar stealth mode
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        try:
            # FAZER LOGIN UMA ÚNICA VEZ
            print("🔑 Fazendo login no D2L (UMA ÚNICA VEZ)...\n")

            # Acessar página de login
            await page.goto("https://www.fanshaweonline.ca/d2l/home", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 3.0))

            # Tentar fazer login
            await try_login_if_needed(page, username, password)

            print("\n✅ LOGIN CONCLUÍDO! Sessão será reutilizada para todos os cursos.\n")
            print("="*80 + "\n")

            # PROCESSAR TODOS OS CURSOS (sequencialmente, usando mesma sessão)
            results = []
            for idx, course_id in enumerate(course_ids, 1):
                print(f"\n{'='*80}")
                print(f"CURSO {idx}/{len(course_ids)}")
                print(f"{'='*80}\n")

                result = await process_single_course_with_shared_browser(course_id, page, context)
                results.append(result)

            # RESUMO FINAL GERAL
            print("\n" + "╔" + "="*78 + "╗")
            print("║" + " "*78 + "║")
            print("║" + "  RESUMO FINAL - TODOS OS CURSOS".center(78) + "║")
            print("║" + " "*78 + "║")
            print("╚" + "="*78 + "╝\n")

            successful = [r for r in results if r['status'] == 'success']
            failed = [r for r in results if r['status'] == 'failed']

            print(f"✅ Cursos processados com sucesso: {len(successful)}/{len(course_ids)}")
            for r in successful:
                print(f"   - {r['course_id']}: {r['links_processed']}/{r['total_links']} links")

            if failed:
                print(f"\n❌ Cursos com falha: {len(failed)}")
                for r in failed:
                    print(f"   - {r['course_id']}: {r.get('error', 'Erro desconhecido')[:60]}...")

            print(f"\n{'='*80}\n")

            return results

        finally:
            await browser.close()
            print("🔒 Browser fechado.\n")


def main():
    """Função principal."""

    parser = argparse.ArgumentParser(
        description='Processa cursos D2L com LOGIN ÚNICO: extrai home page e faz crawl de links',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Processar um único curso
  python3 process_course.py --course-id 2001539

  # Processar múltiplos cursos com LOGIN ÚNICO
  python3 process_course.py --course-ids 2001540 2001539

  # Processar 5 cursos com LOGIN ÚNICO
  python3 process_course.py --course-ids 2001540 2001539 2001541 2001542 2001543

NOTA: O sistema faz LOGIN UMA ÚNICA VEZ e reutiliza a sessão para todos os cursos.
      Isso economiza tempo e evita múltiplas autenticações 2FA.
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--course-id', type=str,
                       help='ID de um único curso a processar')
    group.add_argument('--course-ids', nargs='+', type=str,
                       help='IDs de múltiplos cursos a processar (separados por espaço)')

    args = parser.parse_args()

    # Determinar lista de cursos
    if args.course_id:
        course_ids = [args.course_id]
    else:
        course_ids = args.course_ids

    # Processar TODOS os cursos com login único
    results = asyncio.run(process_all_courses_with_single_login(course_ids))

    # Exit code baseado em falhas
    failed_count = len([r for r in results if r['status'] == 'failed'])
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário.\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ ERRO FATAL: {str(e)}\n")
        sys.exit(1)
