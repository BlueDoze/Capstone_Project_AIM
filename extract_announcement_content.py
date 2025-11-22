"""
Script para extrair o conteúdo completo dos 5 primeiros anúncios do D2L.
"""

import asyncio
import os
import json
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()

async def extract_top_5_announcements():
    """Extrai conteúdo completo dos 5 primeiros anúncios."""

    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME e D2L_PASSWORD no .env")

    # URLs dos 5 primeiros anúncios
    announcements_data = [
        {
            "title": "Reminder: Capstone Class & Agentic AI Workshop",
            "date": "Nov 18, 2025 10:15 AM",
            "url": "https://www.fanshaweonline.ca/d2l/le/news/2001542/2257918/view?ou=2001542"
        },
        {
            "title": "Building Agentic AI using IBM Tools - 18th Nov, Tuesday, 2-4 PM",
            "date": "Nov 13, 2025 1:24 PM",
            "url": "https://www.fanshaweonline.ca/d2l/le/news/2001542/2255777/view?ou=2001542"
        },
        {
            "title": "Gentle Reminder - Sprint 2",
            "date": "Nov 4, 2025 9:36 AM",
            "url": "https://www.fanshaweonline.ca/d2l/le/news/2001542/2249581/view?ou=2001542"
        },
        {
            "title": "Gentle Reminder - Building with Agentic AI: A Hands-on Workshop",
            "date": "Oct 28, 2025 9:47 AM",
            "url": "https://www.fanshaweonline.ca/d2l/le/news/2001542/2246212/view?ou=2001542"
        },
        {
            "title": "Sprint 2 Submission - reg",
            "date": "Oct 27, 2025 10:36 PM",
            "url": "https://www.fanshaweonline.ca/d2l/le/news/2001542/2246117/view?ou=2001542"
        }
    ]

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
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
            # ETAPA 1: Login
            print("[Extractor] Acessando página de login...")
            login_url = "https://www.fanshaweonline.ca/d2l/login"
            await page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 3.5))

            print("[Extractor] Preenchendo email...")
            await page.wait_for_selector("input#i0116", timeout=10000)
            await page.fill("input#i0116", username)
            await asyncio.sleep(random.uniform(0.8, 1.5))
            await page.click("input#idSIButton9")

            print("[Extractor] Aguardando tela de senha...")
            await page.wait_for_load_state("domcontentloaded", timeout=20000)
            await asyncio.sleep(random.uniform(1.5, 2.5))

            print("[Extractor] Preenchendo senha...")
            await page.wait_for_selector("input#i0118", timeout=10000)
            await page.fill("input#i0118", password)
            await asyncio.sleep(random.uniform(0.8, 1.5))
            await page.click("input#idSIButton9")

            print("[Extractor] Aguardando conclusão do login...")
            await page.wait_for_load_state("domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.5, 4.0))

            print("[Extractor] Login completado!\n")

            # ETAPA 2: Extrair conteúdo de cada anúncio
            results = []

            for idx, announcement in enumerate(announcements_data, 1):
                print(f"\n{'='*80}")
                print(f"Anúncio {idx}/5: {announcement['title'][:60]}...")
                print(f"{'='*80}")

                try:
                    # Acessar a página do anúncio
                    print(f"[Extractor] Acessando anúncio {idx}...")
                    await page.goto(announcement['url'], wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(random.uniform(1.5, 3.0))

                    # Extrair conteúdo completo
                    print(f"[Extractor] Extraindo conteúdo...")

                    # Extrair conteúdo do elemento d2l-html-block
                    content = await page.evaluate("""
                        () => {
                            // Procurar por d2l-html-block
                            const htmlBlock = document.querySelector('d2l-html-block');
                            if (htmlBlock) {
                                const htmlAttr = htmlBlock.getAttribute('html');
                                if (htmlAttr) {
                                    // Decodificar HTML entities e remover tags
                                    const temp = document.createElement('div');
                                    temp.innerHTML = htmlAttr;
                                    // Pegar texto limpo
                                    let text = temp.innerText;
                                    return text.trim();
                                }
                            }

                            // Fallback: tentar extrair texto visível
                            const main = document.querySelector('[role="main"]') || document.querySelector('.d2l-page-main');
                            if (main) {
                                // Remover elementos de navegação e metadados
                                const cloned = main.cloneNode(true);
                                const nav = cloned.querySelector('nav');
                                const breadcrumb = cloned.querySelector('[class*="breadcrumb"]');
                                const metadata = cloned.querySelector('[class*="metadata"]');
                                if (nav) nav.remove();
                                if (breadcrumb) breadcrumb.remove();
                                if (metadata) metadata.remove();
                                return cloned.innerText.trim();
                            }

                            return document.body.innerText;
                        }
                    """)

                    content = content.strip() if content else ""

                    # Limpar espaços em branco excessivos
                    content = '\n'.join(line.strip() for line in content.split('\n') if line.strip())

                    # Salvar resultado
                    result = {
                        "index": idx,
                        "title": announcement['title'],
                        "date": announcement['date'],
                        "url": announcement['url'],
                        "content": content
                    }
                    results.append(result)

                    print(f"[Extractor] ✓ Conteúdo extraído ({len(content)} caracteres)")
                    print(f"\nPrimeiros 200 caracteres:\n{content[:200]}...\n")

                except Exception as e:
                    print(f"[Extractor] ✗ Erro ao extrair: {str(e)}")
                    result = {
                        "index": idx,
                        "title": announcement['title'],
                        "date": announcement['date'],
                        "url": announcement['url'],
                        "content": f"ERRO: {str(e)}",
                        "error": True
                    }
                    results.append(result)

            # ETAPA 3: Salvar resultados em JSON
            print(f"\n{'='*80}")
            print("SALVANDO RESULTADOS")
            print(f"{'='*80}\n")

            output = {
                "total": len(results),
                "successful": sum(1 for r in results if 'error' not in r),
                "course": "INFO-6156-(01)-25F",
                "announcements": results
            }

            with open('announcement_contents.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"✓ {len(results)} anúncios processados")
            print(f"✓ Arquivo salvo: announcement_contents.json")
            print(f"✓ Tamanho total: {sum(len(r.get('content', '')) for r in results)} caracteres")

            return output

        except Exception as e:
            print(f"[Extractor] ERRO FATAL: {str(e)}")
            try:
                await page.screenshot(path="error_screenshot.png")
                print("[Extractor] Screenshot de erro salvo em error_screenshot.png")
            except:
                pass
            raise
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(extract_top_5_announcements())
    print(f"\n{'='*80}")
    print("RESUMO FINAL")
    print(f"{'='*80}")
    print(f"Total de anúncios: {result['total']}")
    print(f"Sucesso: {result['successful']}/{result['total']}")
