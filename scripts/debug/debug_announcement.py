"""
Script de debug para inspecionar a estrutura de um anúncio.
"""

import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def debug_announcement():
    """Debug de um anúncio para entender a estrutura HTML."""

    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME e D2L_PASSWORD no .env")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            # Login
            print("[Debug] Fazendo login...")
            login_url = "https://www.fanshaweonline.ca/d2l/login"
            await page.goto(login_url, wait_until="networkidle", timeout=30000)

            await page.wait_for_selector("input#i0116", timeout=10000)
            await page.fill("input#i0116", username)
            await page.click("input#idSIButton9")

            await page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)

            await page.wait_for_selector("input#i0118", timeout=10000)
            await page.fill("input#i0118", password)
            await page.click("input#idSIButton9")

            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except:
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
            await asyncio.sleep(3)

            print("[Debug] Login concluído!")

            # Acessar primeiro anúncio
            url = "https://www.fanshaweonline.ca/d2l/le/news/2001542/2257918/view?ou=2001542"
            print(f"[Debug] Acessando: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # Capturar screenshot
            await page.screenshot(path="debug_announcement_page.png", full_page=True)
            print("[Debug] Screenshot salvo: debug_announcement_page.png")

            # Extrair HTML
            html = await page.content()
            with open("debug_announcement_html.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("[Debug] HTML salvo: debug_announcement_html.html")

            # Inspecionar estrutura com JavaScript
            print("\n[Debug] Inspecionando estrutura da página...")

            # Procurar elementos com classe d2l
            elements = await page.evaluate("""
                () => {
                    const result = {};

                    // Procurar por todos os divs com classes D2L
                    const divs = document.querySelectorAll('[class*="d2l"]');
                    result.d2l_divs = divs.length;

                    // Procurar especificamente por conteúdo
                    const mainContent = document.querySelector('[role="main"]');
                    if (mainContent) {
                        result.main_role = mainContent.className;
                        result.main_text_preview = mainContent.innerText.substring(0, 200);
                    }

                    // Procurar por widget
                    const widget = document.querySelector('.d2l-widget');
                    if (widget) {
                        result.widget_found = true;
                        result.widget_text_preview = widget.innerText.substring(0, 200);
                    }

                    // Procurar por HTML block
                    const htmlBlock = document.querySelector('.d2l-html-block');
                    if (htmlBlock) {
                        result.html_block_found = true;
                        result.html_block_text = htmlBlock.innerText;
                    }

                    // Procurar por qualquer elemento com "announcement" na classe
                    const announcements = document.querySelectorAll('[class*="announcement"], [class*="news"]');
                    result.announcement_elements = announcements.length;
                    if (announcements.length > 0) {
                        result.first_announcement_class = announcements[0].className;
                        result.first_announcement_text = announcements[0].innerText.substring(0, 300);
                    }

                    // Procurar por p tags
                    const paragraphs = document.querySelectorAll('p');
                    result.paragraphs = paragraphs.length;
                    if (paragraphs.length > 0) {
                        result.first_paragraph = paragraphs[0].innerText;
                    }

                    return result;
                }
            """)

            print("\nResultados da inspeção:")
            for key, value in elements.items():
                print(f"  {key}: {value}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_announcement())
