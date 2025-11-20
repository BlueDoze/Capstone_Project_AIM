"""
Script para extrair TODOS os anúncios do D2L com um único login.
"""

import asyncio
import os
import json
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def wait_for_2fa_approval(page, timeout=120000):
    """Aguarda aprovação do 2FA detectando redirecionamento."""
    print("\n" + "="*80)
    print("🔐 AUTENTICAÇÃO DE DOIS FATORES DETECTADA")
    print("="*80)
    print("Por favor, aprove a solicitação no seu Microsoft Authenticator app.")
    print("Aguardando aprovação...")
    print("="*80 + "\n")

    start_url = page.url
    elapsed = 0

    while elapsed < timeout:
        current_url = page.url

        # Verifica se saiu da página de 2FA
        if "login.microsoftonline.com" not in current_url and "fanshaweonline.ca" in current_url:
            print("\n✓ Autenticação aprovada com sucesso!")
            return True

        await asyncio.sleep(2)
        elapsed += 2000

        if elapsed % 10000 == 0:  # A cada 10 segundos
            print(f"  Ainda aguardando... ({elapsed // 1000}s)")

    print("\n✗ Timeout aguardando aprovação do 2FA")
    return False

async def extract_all_announcements():
    """Extrai todos os anúncios com um único login."""

    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME e D2L_PASSWORD no .env")

    async with async_playwright() as p:
        # Browser VISÍVEL para aprovar 2FA
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        all_announcements = []

        try:
            print("="*80)
            print("EXTRATOR DE ANÚNCIOS D2L - LOGIN ÚNICO")
            print("="*80)

            # ETAPA 1: Login
            print("\n[1/4] Iniciando login...")
            login_url = "https://www.fanshaweonline.ca/d2l/login"
            await page.goto(login_url, wait_until="networkidle", timeout=30000)

            # Preencher email
            print("  → Preenchendo email...")
            await page.wait_for_selector("input#i0116", timeout=10000)
            await page.fill("input#i0116", username)
            await page.click("input#idSIButton9")

            await page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)

            # Preencher senha
            print("  → Preenchendo senha...")
            await page.wait_for_selector("input#i0118", timeout=10000)
            await page.fill("input#i0118", password)
            await page.click("input#idSIButton9")

            # Aguardar e detectar 2FA
            await asyncio.sleep(3)

            # Verificar se precisa de 2FA
            current_url = page.url
            if "login.microsoftonline.com" in current_url:
                # Ainda na página da Microsoft - pode precisar de 2FA
                success = await wait_for_2fa_approval(page, timeout=180000)  # 3 minutos
                if not success:
                    raise Exception("Falha na aprovação do 2FA")

            await asyncio.sleep(3)
            print(f"\n✓ Login completado! URL: {page.url}\n")

            # ETAPA 2: Acessar página de notícias
            print("[2/4] Acessando página de notícias...")
            news_url = "https://www.fanshaweonline.ca/d2l/lms/news/main.d2l?ou=2001542"
            await page.goto(news_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            print("✓ Página de notícias carregada!\n")

            # ETAPA 3: Extrair lista de anúncios
            print("[3/4] Extraindo lista de anúncios...")

            # Buscar todos os links de anúncios na página
            announcements_list = await page.evaluate("""
                () => {
                    const announcements = [];
                    const links = document.querySelectorAll('a.d2l-link-inline');

                    links.forEach((link, idx) => {
                        const title = link.textContent.trim();
                        const url = link.href;

                        // Pegar data da célula seguinte
                        const row = link.closest('tr');
                        let date = '';
                        if (row) {
                            const cells = row.querySelectorAll('td, th');
                            if (cells.length >= 2) {
                                date = cells[cells.length - 1].textContent.trim();
                            }
                        }

                        if (title && url && url.includes('/d2l/le/news/')) {
                            announcements.push({
                                title: title,
                                date: date,
                                url: url
                            });
                        }
                    });

                    return announcements;
                }
            """)

            print(f"✓ Encontrados {len(announcements_list)} anúncios!\n")

            # ETAPA 4: Extrair conteúdo de cada anúncio
            print(f"[4/4] Extraindo conteúdo de {len(announcements_list)} anúncios...")
            print("="*80 + "\n")

            for idx, announcement in enumerate(announcements_list, 1):
                try:
                    print(f"[{idx}/{len(announcements_list)}] {announcement['title'][:60]}...")

                    # Acessar página do anúncio
                    await page.goto(announcement['url'], wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(1)

                    # Extrair conteúdo
                    content = await page.evaluate("""
                        () => {
                            const htmlBlock = document.querySelector('d2l-html-block');
                            if (htmlBlock) {
                                const htmlAttr = htmlBlock.getAttribute('html');
                                if (htmlAttr) {
                                    const temp = document.createElement('div');
                                    temp.innerHTML = htmlAttr;
                                    return temp.innerText.trim();
                                }
                            }

                            // Fallback
                            const main = document.querySelector('[role="main"]');
                            if (main) {
                                return main.innerText.trim();
                            }

                            return '';
                        }
                    """)

                    content = content.strip() if content else ""
                    content = '\n'.join(line.strip() for line in content.split('\n') if line.strip())

                    # Salvar resultado
                    result = {
                        "index": idx,
                        "title": announcement['title'],
                        "date": announcement['date'],
                        "url": announcement['url'],
                        "content": content,
                        "content_length": len(content)
                    }
                    all_announcements.append(result)

                    print(f"    ✓ Extraído ({len(content)} caracteres)")

                    # Voltar para lista
                    await page.go_back()
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"    ✗ Erro: {str(e)}")
                    result = {
                        "index": idx,
                        "title": announcement['title'],
                        "date": announcement['date'],
                        "url": announcement['url'],
                        "content": f"ERRO: {str(e)}",
                        "error": True
                    }
                    all_announcements.append(result)

                    # Tentar voltar para lista
                    try:
                        await page.goto(news_url, wait_until="networkidle", timeout=15000)
                        await asyncio.sleep(1)
                    except:
                        pass

            # Salvar resultados
            print("\n" + "="*80)
            print("SALVANDO RESULTADOS")
            print("="*80)

            output = {
                "total": len(all_announcements),
                "successful": sum(1 for a in all_announcements if 'error' not in a),
                "failed": sum(1 for a in all_announcements if 'error' in a),
                "course": "INFO-6156-(01)-25F",
                "extracted_at": __import__('datetime').datetime.now().isoformat(),
                "announcements": all_announcements
            }

            with open('all_announcements.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Arquivo salvo: all_announcements.json")
            print(f"✓ Total: {output['total']} anúncios")
            print(f"✓ Sucesso: {output['successful']}")
            print(f"✓ Falhas: {output['failed']}")
            print(f"✓ Conteúdo total: {sum(a.get('content_length', 0) for a in all_announcements)} caracteres")

            return output

        except Exception as e:
            print(f"\n✗ ERRO FATAL: {str(e)}")

            # Tentar salvar o que foi extraído até agora
            if all_announcements:
                partial_output = {
                    "total": len(all_announcements),
                    "partial": True,
                    "error": str(e),
                    "announcements": all_announcements
                }
                with open('all_announcements_partial.json', 'w', encoding='utf-8') as f:
                    json.dump(partial_output, f, indent=2, ensure_ascii=False)
                print(f"✓ Resultados parciais salvos em: all_announcements_partial.json")

            raise

        finally:
            print("\nFechando browser em 5 segundos...")
            await asyncio.sleep(5)
            await browser.close()

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  EXTRATOR DE ANÚNCIOS D2L - TODOS OS ANÚNCIOS COM LOGIN ÚNICO".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print("\n")

    result = asyncio.run(extract_all_announcements())

    print("\n" + "="*80)
    print("CONCLUÍDO COM SUCESSO!")
    print("="*80)
    print(f"Arquivo gerado: all_announcements.json")
    print(f"Total de anúncios extraídos: {result['total']}")
    print("="*80 + "\n")
