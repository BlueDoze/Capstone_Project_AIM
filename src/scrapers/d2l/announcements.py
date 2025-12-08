"""
Script para extrair a página home e os 5 primeiros anúncios do D2L com um único login.
"""

import asyncio
import os
import json
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()

async def wait_for_2fa_approval(page, timeout=300000):
    """Aguarda aprovação do 2FA detectando redirecionamento, mostrando código e preenchendo automaticamente."""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " 🔐 AUTENTICAÇÃO DE DOIS FATORES NECESSÁRIA ".center(78) + "║")
    print("╚" + "="*78 + "╝")
    print()

    # Tentar extrair e preencher o código de verificação automaticamente
    try:
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Procurar por código numérico na página
        verification_code = await page.evaluate("""
            () => {
                // Procurar por diferentes padrões de código
                const codeSelectors = [
                    '#idRichContext_DisplaySign',
                    '[data-value]',
                    '.text-title',
                    '.request-description-content',
                    'div[role="heading"]'
                ];

                for (const selector of codeSelectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        const text = element.innerText || element.textContent;
                        // Procurar por número de 2 dígitos
                        const match = text.match(/\\b(\\d{2})\\b/);
                        if (match) {
                            return match[1];
                        }
                    }
                }

                // Procurar em todo o body por padrão "número é XX"
                const bodyText = document.body.innerText;
                const patterns = [
                    /number is (\\d{2})/i,
                    /código.*?(\\d{2})/i,
                    /digite.*?(\\d{2})/i,
                    /enter.*?(\\d{2})/i
                ];

                for (const pattern of patterns) {
                    const match = bodyText.match(pattern);
                    if (match) {
                        return match[1];
                    }
                }

                return null;
            }
        """)

        if verification_code:
            print("╔" + "="*78 + "╗")
            print("║" + f"  🔢 CÓDIGO DE VERIFICAÇÃO DETECTADO: {verification_code}  ".center(78) + "║")
            print("╚" + "="*78 + "╝")
            print()

            # Tentar preencher o código automaticamente
            try:
                # Procurar campo de input para o código
                code_input_selectors = [
                    'input[name="otc"]',
                    'input[type="tel"]',
                    'input[aria-label*="code"]',
                    'input[placeholder*="code"]',
                    '#idTxtBx_SAOTCC_OTC'
                ]

                code_filled = False
                for selector in code_input_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                        print(f"✅ Campo de código encontrado: {selector}")
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                        await page.fill(selector, verification_code)
                        print(f"✅ Código {verification_code} preenchido automaticamente!")
                        await asyncio.sleep(random.uniform(0.5, 1.0))

                        # Procurar e clicar no botão de verificação
                        verify_button_selectors = [
                            'input[type="submit"]',
                            'button[type="submit"]',
                            '#idSubmit_SAOTCC_Continue'
                        ]

                        for btn_selector in verify_button_selectors:
                            try:
                                verify_button = await page.query_selector(btn_selector)
                                if verify_button:
                                    print(f"✅ Botão de verificação encontrado, clicando...")
                                    await asyncio.sleep(random.uniform(0.5, 1.0))
                                    await verify_button.click()
                                    print(f"✅ Código enviado automaticamente!")
                                    code_filled = True
                                    break
                            except:
                                continue

                        if code_filled:
                            break

                    except:
                        continue

                if not code_filled:
                    print("⚠️  Não foi possível preencher o código automaticamente.")
                    print(f"📱 Por favor, digite manualmente: {verification_code}")

            except Exception as e:
                print(f"⚠️  Erro ao preencher código automaticamente: {str(e)[:100]}")
                print(f"📱 Por favor, use o app Microsoft Authenticator:")
                print(f"   - Digite o código: {verification_code}")
                print(f"   - Ou toque em 'Aprovar'")

            print()
        else:
            print("📱 AÇÃO NECESSÁRIA:")
            print("   1. Abra o app Microsoft Authenticator no seu celular")
            print("   2. Procure pela notificação de aprovação")
            print("   3. Toque em 'Aprovar' ou digite o código se solicitado")
            print()

    except Exception as e:
        print("📱 AÇÃO NECESSÁRIA:")
        print("   1. Abra o app Microsoft Authenticator no seu celular")
        print("   2. Procure pela notificação de aprovação")
        print("   3. Toque em 'Aprovar'")
        print()

    print("⏳ Aguardando aprovação...\n")

    start_url = page.url
    elapsed = 0
    dots = 0
    last_code_check = 0

    while elapsed < timeout:
        current_url = page.url

        # Verifica se saiu da página de 2FA
        if "login.microsoftonline.com" not in current_url and "fanshaweonline.ca" in current_url:
            print("\n✅ AUTENTICAÇÃO APROVADA COM SUCESSO!\n")
            return True

        # Re-verificar código periodicamente (a cada 10s)
        if elapsed - last_code_check >= 10000:
            try:
                new_code = await page.evaluate("""
                    () => {
                        const element = document.querySelector('#idRichContext_DisplaySign');
                        if (element) {
                            const match = element.innerText.match(/\\b(\\d{2})\\b/);
                            return match ? match[1] : null;
                        }
                        return null;
                    }
                """)
                if new_code and new_code != verification_code:
                    print(f"\n   🔄 Código atualizado: {new_code}")
                    verification_code = new_code
            except:
                pass
            last_code_check = elapsed

        await asyncio.sleep(2)
        elapsed += 2000

        # Animação de "carregando"
        dots = (dots + 1) % 4
        loading_animation = "." * dots + " " * (3 - dots)
        elapsed_sec = elapsed // 1000

        if elapsed % 2000 == 0:  # A cada 2 segundos
            print(f"\r   Aguardando{loading_animation} ({elapsed_sec}s)", end="", flush=True)

        if elapsed % 30000 == 0 and elapsed > 0:  # Lembrete a cada 30 segundos
            code_reminder = f" - Código: {verification_code}" if verification_code else ""
            print(f"\n   💡 Lembrete: Verifique seu celular{code_reminder} - {elapsed_sec}s decorridos")

    print("\n\n❌ TIMEOUT: Aprovação não detectada após 5 minutos")
    print("   Por favor, tente novamente.\n")
    return False

async def extract_all_announcements():
    """Extrai a página home e os 5 primeiros anúncios com um único login."""

    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME e D2L_PASSWORD no .env")

    async with async_playwright() as p:
        # Browser INVISÍVEL - tudo via terminal
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

        all_announcements = []

        try:
            print("="*80)
            print("EXTRATOR D2L - HOME + 5 ANÚNCIOS - LOGIN ÚNICO")
            print("="*80)

            # ETAPA 1: Login
            print("\n[1/5] Iniciando login...")
            login_url = "https://www.fanshaweonline.ca/d2l/login"
            await page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 3.5))

            # Preencher email
            print("  → Preenchendo email...")
            await page.wait_for_selector("input#i0116", timeout=10000)
            await page.fill("input#i0116", username)
            await asyncio.sleep(random.uniform(0.8, 1.5))
            await page.click("input#idSIButton9")

            await page.wait_for_load_state("domcontentloaded", timeout=20000)
            await asyncio.sleep(random.uniform(1.5, 2.5))

            # Preencher senha
            print("  → Preenchendo senha...")
            await page.wait_for_selector("input#i0118", timeout=10000)
            await page.fill("input#i0118", password)
            await asyncio.sleep(random.uniform(0.8, 1.5))
            await page.click("input#idSIButton9")

            # Aguardar e detectar 2FA
            await asyncio.sleep(3)

            # Verificar se precisa de 2FA
            print("   → Verificando se 2FA é necessário...")
            await asyncio.sleep(2)
            current_url = page.url
            print(f"   → URL atual: {current_url[:60]}...")

            if "login.microsoftonline.com" in current_url or "Stay signed in" in await page.content():
                # Ainda na página da Microsoft - pode precisar de 2FA ou "Stay signed in"

                # Verificar se é tela "Stay signed in?"
                try:
                    stay_button = await page.query_selector("input#idSIButton9")
                    if stay_button:
                        button_value = await stay_button.get_attribute("value")
                        if button_value and ("Yes" in button_value or "No" in button_value):
                            print("   → Detectada tela 'Stay signed in?' - clicando 'Yes'...")
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                            await stay_button.click()
                            await page.wait_for_load_state("domcontentloaded", timeout=15000)
                            await asyncio.sleep(random.uniform(1.5, 2.5))
                except:
                    pass

                # Re-verificar URL após clicar
                current_url = page.url
                if "login.microsoftonline.com" in current_url:
                    # Ainda precisa de 2FA
                    success = await wait_for_2fa_approval(page, timeout=300000)  # 5 minutos
                    if not success:
                        raise Exception("Falha na aprovação do 2FA")

            await asyncio.sleep(2)
            print(f"\n✓ Login completado! URL: {page.url[:60]}...\n")

            # ETAPA 2: Acessar e extrair página home
            print("[2/5] Acessando página home...")
            home_url = "https://www.fanshaweonline.ca/d2l/home"
            await page.goto(home_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 3.5))
            print("✓ Página home carregada!\n")

            # Extrair conteúdo da home
            print("   → Extraindo conteúdo da home...", end="", flush=True)
            home_content = await page.evaluate("""
                () => {
                    // Tentar extrair conteúdo principal
                    const main = document.querySelector('[role="main"]') ||
                                 document.querySelector('.d2l-page-main') ||
                                 document.querySelector('main');

                    if (main) {
                        return main.innerText.trim();
                    }

                    return document.body.innerText.trim();
                }
            """)

            home_content = home_content.strip() if home_content else ""
            home_content = '\n'.join(line.strip() for line in home_content.split('\n') if line.strip())

            print(f" OK ({len(home_content)} caracteres)")
            print(f"   ✅ Conteúdo da home extraído!\n")

            # ETAPA 3: Acessar página de notícias
            print("[3/5] Acessando página de notícias...")
            news_url = "https://www.fanshaweonline.ca/d2l/lms/news/main.d2l?ou=2001542"
            await page.goto(news_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 3.5))
            print("✓ Página de notícias carregada!\n")

            # ETAPA 4: Extrair lista de anúncios
            print("[4/5] Extraindo lista de anúncios...")

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

            # ETAPA 5: Extrair conteúdo de cada anúncio (apenas 5 primeiros)
            announcements_to_extract = announcements_list[:5]
            print(f"[5/5] Extraindo conteúdo de 5 anúncios...")
            print("="*80 + "\n")

            for idx, announcement in enumerate(announcements_to_extract, 1):
                try:
                    # Barra de progresso visual
                    progress_bar_width = 40
                    progress = int((idx / len(announcements_to_extract)) * progress_bar_width)
                    bar = "█" * progress + "░" * (progress_bar_width - progress)
                    percentage = int((idx / len(announcements_to_extract)) * 100)

                    print(f"\n[{idx}/{len(announcements_to_extract)}] {bar} {percentage}%")
                    print(f"📄 {announcement['title'][:70]}")
                    print(f"📅 {announcement['date']}")

                    # Acessar página do anúncio
                    print(f"   → Acessando página...", end="", flush=True)
                    await page.goto(announcement['url'], wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    print(" OK")

                    # Extrair conteúdo
                    print(f"   → Extraindo conteúdo...", end="", flush=True)
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

                    print(f" OK ({len(content)} caracteres)")
                    print(f"   ✅ Sucesso!")

                    # Voltar para lista
                    await page.go_back()
                    await asyncio.sleep(random.uniform(0.8, 1.5))

                except Exception as e:
                    print(f" FALHOU")
                    print(f"   ❌ Erro: {str(e)[:100]}")
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
                        await page.goto(news_url, wait_until="domcontentloaded", timeout=20000)
                        await asyncio.sleep(random.uniform(1.0, 2.0))
                    except:
                        pass

            # Salvar resultados
            print("\n" + "="*80)
            print("SALVANDO RESULTADOS")
            print("="*80)

            output = {
                "total_announcements": len(all_announcements),
                "successful": sum(1 for a in all_announcements if 'error' not in a),
                "failed": sum(1 for a in all_announcements if 'error' in a),
                "course": "INFO-6156-(01)-25F",
                "extracted_at": __import__('datetime').datetime.now().isoformat(),
                "home_page": {
                    "url": home_url,
                    "content": home_content,
                    "content_length": len(home_content)
                },
                "announcements": all_announcements
            }

            # Criar diretório se não existir
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'announcements')
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, 'all_announcements.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Arquivo salvo: {output_path}")
            print(f"✓ Home page: {len(home_content)} caracteres")
            print(f"✓ Total: {output['total_announcements']} anúncios")
            print(f"✓ Sucesso: {output['successful']}")
            print(f"✓ Falhas: {output['failed']}")
            print(f"✓ Conteúdo total dos anúncios: {sum(a.get('content_length', 0) for a in all_announcements)} caracteres")

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
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'announcements')
                os.makedirs(output_dir, exist_ok=True)
                partial_path = os.path.join(output_dir, 'all_announcements_partial.json')
                with open(partial_path, 'w', encoding='utf-8') as f:
                    json.dump(partial_output, f, indent=2, ensure_ascii=False)
                print(f"✓ Resultados parciais salvos em: {partial_path}")

            raise

        finally:
            await browser.close()

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  EXTRATOR D2L - HOME + 5 ANÚNCIOS - LOGIN ÚNICO".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print("\n")

    result = asyncio.run(extract_all_announcements())

    print("\n" + "="*80)
    print("CONCLUÍDO COM SUCESSO!")
    print("="*80)
    print(f"Arquivo gerado: data/announcements/all_announcements.json")
    print(f"Home page extraída: {result['home_page']['content_length']} caracteres")
    print(f"Total de anúncios extraídos: {result['total_announcements']}")
    print("="*80 + "\n")
