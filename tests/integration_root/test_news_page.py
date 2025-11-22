"""
Script para acessar a página de notícias do D2L após login
e extrair informações.
"""

import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def extract_announcements_detailed(page):
    """Extrai anúncios com conteúdo completo clicando em cada um."""
    announcements = []

    try:
        # Aguardar tabela de anúncios carregar
        await page.wait_for_selector("table", timeout=10000)

        # Obter todas as linhas da tabela (exceto header)
        rows = await page.query_selector_all("table tbody tr")

        print(f"[News Scraper] Encontradas {len(rows)} linhas de anúncios")

        for idx, row in enumerate(rows):
            try:
                # Extrair título e link
                title_element = await row.query_selector("td:first-child a")
                if not title_element:
                    continue

                title = await title_element.text_content()
                title = title.strip() if title else ""

                # Extrair data
                date_element = await row.query_selector("td:nth-child(2)")
                date = await date_element.text_content() if date_element else ""
                date = date.strip() if date else ""

                if not title:
                    continue

                # Clicar no título para abrir o anúncio completo
                print(f"[News Scraper] Abrindo anúncio {idx + 1}: {title[:50]}...")
                await title_element.click()

                # Aguardar conteúdo carregar
                await asyncio.sleep(1)

                # Extrair conteúdo completo
                try:
                    content_area = await page.query_selector(".d2l-page-main, [role='main'], .content")
                    if content_area:
                        content = await content_area.text_content()
                    else:
                        content = await page.evaluate("() => document.body.innerText")

                    content = content.strip() if content else ""
                except:
                    content = ""

                # Salvar anúncio
                announcement = {
                    "title": title,
                    "date": date,
                    "content": content,
                    "index": idx + 1
                }
                announcements.append(announcement)

                # Voltar à lista de anúncios
                await page.go_back()
                await asyncio.sleep(1)

            except Exception as e:
                print(f"[News Scraper] Erro ao processar anúncio {idx + 1}: {str(e)}")
                try:
                    await page.go_back()
                    await asyncio.sleep(0.5)
                except:
                    pass
                continue

        return announcements

    except Exception as e:
        print(f"[News Scraper] Erro ao extrair anúncios: {str(e)}")
        return announcements

async def scrape_news_page():
    """Acessa página de notícias e extrai informações."""

    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME e D2L_PASSWORD no .env")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            # ETAPA 1: Login
            print("[News Scraper] Acessando página de login...")
            login_url = "https://www.fanshaweonline.ca/d2l/login"
            await page.goto(login_url, wait_until="networkidle", timeout=30000)

            print("[News Scraper] Preenchendo email...")
            await page.wait_for_selector("input#i0116", timeout=10000)
            await page.fill("input#i0116", username)
            await page.click("input#idSIButton9")

            print("[News Scraper] Aguardando tela de senha...")
            await page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)

            print("[News Scraper] Preenchendo senha...")
            await page.wait_for_selector("input#i0118", timeout=10000)
            await page.fill("input#i0118", password)
            await page.click("input#idSIButton9")

            print("[News Scraper] Aguardando conclusão do login...")
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except:
                print("[News Scraper] Timeout na espera de networkidle, continuando mesmo assim...")
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
            await asyncio.sleep(3)

            current_url = page.url
            print(f"[News Scraper] Login completado. URL atual: {current_url}")

            # ETAPA 2: Acessar página de notícias
            news_url = "https://www.fanshaweonline.ca/d2l/lms/news/main.d2l?ou=2001542"
            print(f"[News Scraper] Acessando página de notícias: {news_url}")
            await page.goto(news_url, wait_until="networkidle", timeout=30000)

            # Aguardar conteúdo carregar
            await asyncio.sleep(2)

            # ETAPA 3: Capturar conteúdo da página
            print("[News Scraper] Capturando conteúdo da página...")

            # Capturar screenshot
            await page.screenshot(path="news_page_screenshot.png", full_page=True)
            print("[News Scraper] Screenshot salvo em news_page_screenshot.png")

            # Extrair HTML completo
            html_content = await page.content()

            # Extrair texto visível
            visible_text = await page.evaluate("() => document.body.innerText")

            # Salvar HTML para análise
            with open("news_page_content.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("[News Scraper] HTML salvo em news_page_content.html")

            # Salvar texto visível
            with open("news_page_text.txt", "w", encoding="utf-8") as f:
                f.write(visible_text)
            print("[News Scraper] Texto visível salvo em news_page_text.txt")

            # Extrair anúncios com detalhes completos
            print("[News Scraper] Extraindo detalhes dos anúncios...")
            announcements = await extract_announcements_detailed(page)

            # Salvar anúncios em formato estruturado
            import json
            with open("news_announcements.json", "w", encoding="utf-8") as f:
                json.dump(announcements, f, indent=2, ensure_ascii=False)
            print(f"[News Scraper] {len(announcements)} anúncios extraídos e salvos em news_announcements.json")

            # Extrair informações estruturadas
            print("\n" + "="*80)
            print("INFORMAÇÕES DA PÁGINA DE NOTÍCIAS")
            print("="*80)
            print(visible_text)
            print("="*80 + "\n")

            return {
                "url": news_url,
                "html_file": "news_page_content.html",
                "text_file": "news_page_text.txt",
                "screenshot": "news_page_screenshot.png",
                "visible_text": visible_text
            }

        except Exception as e:
            print(f"[News Scraper] ERRO: {str(e)}")
            try:
                await page.screenshot(path="error_screenshot.png")
                print("[News Scraper] Screenshot de erro salvo em error_screenshot.png")
            except:
                pass
            raise
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(scrape_news_page())
    print("\n✓ Scraping concluído com sucesso!")
    print(f"Arquivos gerados:")
    print(f"  - HTML: {result['html_file']}")
    print(f"  - Texto: {result['text_file']}")
    print(f"  - Screenshot: {result['screenshot']}")
