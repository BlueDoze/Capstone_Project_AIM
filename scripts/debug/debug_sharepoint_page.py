"""
Script de debug para capturar HTML do SharePoint Events sem 2FA
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()

SHAREPOINT_EVENTS_LIST_GUID = "d1ad5108-61da-44a6-9b0a-d114a09c5e7e"

async def debug_sharepoint_page():
    """Captura HTML da página SharePoint para análise"""
    
    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME e D2L_PASSWORD no .env")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)  # MODO VISUAL
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
        )

        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        try:
            # Tentar acessar SharePoint Events
            sharepoint_url = f"https://fanshawecca.sharepoint.com/_layouts/15/Events.aspx?ListGuid={SHAREPOINT_EVENTS_LIST_GUID}"
            
            print(f"[1] Navegando para: {sharepoint_url}")
            await page.goto(sharepoint_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            print(f"[2] URL atual: {page.url}")
            
            # Se redirecionou para login, tentar autenticar
            if "login.microsoftonline.com" in page.url:
                print("[3] Login detectado, fazendo autenticação básica...")
                
                try:
                    # Preencher email
                    await page.fill("input#i0116", username)
                    await asyncio.sleep(1)
                    await page.click("input#idSIButton9")
                    await page.wait_for_load_state("domcontentloaded", timeout=20000)
                    await asyncio.sleep(2)

                    # Preencher senha
                    await page.fill("input#i0118", password)
                    await asyncio.sleep(1)
                    await page.click("input#idSIButton9")
                    await asyncio.sleep(3)

                    print("[4] Login concluído, aguardando redirecionamento...")
                    
                    # Se aparecer "Stay signed in?", clicar Yes
                    try:
                        await page.wait_for_selector("input#idSIButton9", timeout=5000)
                        await page.click("input#idSIButton9")
                        await asyncio.sleep(2)
                    except:
                        pass

                except Exception as e:
                    print(f"[!] Erro no login: {e}")

            # Aguardar página carregar (ou você fazer o 2FA manualmente)
            print("\n" + "="*80)
            print("⏸️  AGUARDANDO 60 SEGUNDOS")
            print("   Se aparecer 2FA, aprove no celular!")
            print("   O script vai capturar a página depois.")
            print("="*80 + "\n")
            
            await asyncio.sleep(60)  # 60 segundos para aprovar 2FA
            
            current_url = page.url
            print(f"[5] URL final: {current_url}")

            # Salvar HTML
            html_content = await page.content()
            html_file = Path("debug_sharepoint_page.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"[6] ✓ HTML salvo em: {html_file}")
            print(f"    Tamanho: {len(html_content)} bytes")

            # Salvar screenshot
            screenshot_file = Path("debug_sharepoint_page.png")
            await page.screenshot(path=str(screenshot_file), full_page=True)
            print(f"[7] ✓ Screenshot salvo em: {screenshot_file}")

            # Extrair alguns elementos para análise rápida
            print("\n[8] Análise rápida da página:")
            
            analysis = await page.evaluate("""
                () => {
                    const info = {
                        title: document.title,
                        is2FA: document.body.innerText.toLowerCase().includes('verify') || 
                               document.body.innerText.toLowerCase().includes('authenticator'),
                        hasCalendar: document.querySelector('[class*="calendar"]') !== null,
                        hasEvents: document.querySelector('[class*="event"]') !== null,
                        hasList: document.querySelector('[class*="list"]') !== null,
                        hasTable: document.querySelector('table') !== null,
                        classesFound: []
                    };
                    
                    // Coletar classes relevantes
                    const allElements = document.querySelectorAll('*');
                    const classSet = new Set();
                    allElements.forEach(el => {
                        if (el.className && typeof el.className === 'string') {
                            el.className.split(' ').forEach(cls => {
                                if (cls && (cls.includes('event') || cls.includes('calendar') || 
                                           cls.includes('list') || cls.includes('ms-'))) {
                                    classSet.add(cls);
                                }
                            });
                        }
                    });
                    
                    info.classesFound = Array.from(classSet).slice(0, 50);
                    
                    return info;
                }
            """)

            print(f"  - Title: {analysis['title']}")
            print(f"  - Is 2FA page: {analysis['is2FA']}")
            print(f"  - Has calendar elements: {analysis['hasCalendar']}")
            print(f"  - Has event elements: {analysis['hasEvents']}")
            print(f"  - Has list elements: {analysis['hasList']}")
            print(f"  - Has table: {analysis['hasTable']}")
            print(f"  - CSS classes encontradas ({len(analysis['classesFound'])}):")
            for cls in analysis['classesFound'][:20]:
                print(f"    • {cls}")

        except Exception as e:
            print(f"\n[!] ERRO: {e}")
            
            # Salvar HTML mesmo com erro
            try:
                html_content = await page.content()
                html_file = Path("debug_sharepoint_error.html")
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"    HTML de erro salvo em: {html_file}")
            except:
                pass

        finally:
            await browser.close()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("DEBUG SHAREPOINT PAGE - CAPTURA DE ESTRUTURA HTML")
    print("="*80 + "\n")
    
    asyncio.run(debug_sharepoint_page())
    
    print("\n" + "="*80)
    print("DEBUG CONCLUÍDO")
    print("="*80)
