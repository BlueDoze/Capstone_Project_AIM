"""
Script para extrair o conteúdo da página Home do curso D2L (Content área).
Endpoint: https://www.fanshaweonline.ca/d2l/le/content/{COURSE_ID}/Home
"""

import asyncio
import os
import json
import random
import argparse
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

async def try_login_if_needed(page, username, password):
    """Tenta fazer login apenas se necessário. Retorna True se logado com sucesso."""

    current_url = page.url

    # Se já está logado (não está em página de login), retorna sucesso
    if "login" not in current_url.lower() and "fanshaweonline.ca" in current_url:
        print("  ✓ Já está logado, pulando autenticação...")
        return True

    # Se está na página de login da Microsoft, fazer login
    if "login.microsoftonline.com" in current_url or "login" in current_url:
        print("  → Página de login detectada, fazendo autenticação...")

        # Verificar se campos de login existem
        try:
            email_field = await page.query_selector("input#i0116")
            if email_field:
                print("  → Preenchendo email...")
                await page.fill("input#i0116", username)
                await asyncio.sleep(random.uniform(0.8, 1.5))
                await page.click("input#idSIButton9")

                await page.wait_for_load_state("domcontentloaded", timeout=20000)
                await asyncio.sleep(random.uniform(1.5, 2.5))

                # Preencher senha
                password_field = await page.query_selector("input#i0118")
                if password_field:
                    print("  → Preenchendo senha...")
                    await page.fill("input#i0118", password)
                    await asyncio.sleep(random.uniform(0.8, 1.5))
                    await page.click("input#idSIButton9")
                    await asyncio.sleep(3)
        except Exception as e:
            print(f"  ⚠️  Campos de login não encontrados: {str(e)[:50]}")
            return True  # Continuar mesmo assim

    # Verificar "Stay signed in?"
    await asyncio.sleep(2)
    current_url = page.url

    if "login.microsoftonline.com" in current_url or "Stay signed in" in await page.content():
        try:
            stay_button = await page.query_selector("input#idSIButton9")
            if stay_button:
                button_value = await stay_button.get_attribute("value")
                if button_value and ("Yes" in button_value or "No" in button_value):
                    print("  → Detectada tela 'Stay signed in?' - clicando 'Yes'...")
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    await stay_button.click()
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                    await asyncio.sleep(random.uniform(1.5, 2.5))
        except:
            pass

    # Verificar se 2FA é necessário
    await asyncio.sleep(1)
    current_url = page.url

    if "login.microsoftonline.com" in current_url:
        # Pode ser 2FA - tentar detectar
        page_content = await page.content()

        # Verificar se é página de 2FA (procurar por indicadores)
        is_2fa_page = any(indicator in page_content.lower() for indicator in [
            "verify", "authentication", "approval", "microsoft authenticator",
            "security code", "two-factor"
        ])

        if is_2fa_page:
            print("  → 2FA detectado, aguardando aprovação...")
            try:
                success = await wait_for_2fa_approval(page, timeout=300000)
                if not success:
                    print("  ⚠️  2FA não aprovado, mas continuando...")
                    return True  # Continuar mesmo sem 2FA
            except Exception as e:
                print(f"  ⚠️  Erro no 2FA: {str(e)[:50]}, continuando...")
                return True  # Continuar mesmo com erro
        else:
            print("  ✓ Login completado sem 2FA")

    return True


async def extract_content_home(course_id="2001540", output_file=None, page=None, browser_context=None):
    """Extrai o conteúdo da página Home do curso D2L."""

    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    # Definir arquivo de saída
    if output_file is None:
        output_file = f'content_home_{course_id}.json'

    # Se página foi fornecida (login compartilhado), usar ela
    should_close_browser = False
    browser = None

    # Se não tem página fornecida, criar nova
    if page is None:
        should_close_browser = True
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

            try:
                print("="*80)
                print(f"EXTRATOR D2L - CONTEÚDO DA PÁGINA HOME (Curso: {course_id})")
                print("="*80)

                # ETAPA 1: Tentar acessar diretamente (pode já estar logado)
                print("\n[1/3] Tentando acessar página (verificando login)...")
                content_url = f"https://www.fanshaweonline.ca/d2l/home/{course_id}"
                await page.goto(content_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(2.0, 3.0))

                # Verificar se foi redirecionado para login
                if "login" in page.url.lower():
                    print("  → Login necessário, fazendo autenticação...")
                    await try_login_if_needed(page, username, password)

                    # Tentar acessar página novamente após login
                    await page.goto(content_url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(random.uniform(2.0, 3.0))
                else:
                    print("  ✓ Acesso direto bem-sucedido (sessão ativa)")

                print(f"\n✓ Página acessada! URL: {page.url[:60]}...\n")

                # ETAPA 2: Extrair conteúdo
                print("[2/2] Extraindo conteúdo da página...")

                # Extrair título da página
                page_title = await page.evaluate("""
                    () => {
                        return document.title || 'Sem título';
                    }
                """)

                # Extrair conteúdo principal
                main_content = await page.evaluate("""
                    () => {
                        const main = document.querySelector('[role="main"]') ||
                                     document.querySelector('.d2l-page-main') ||
                                     document.querySelector('main') ||
                                     document.body;

                        return main.innerText.trim();
                    }
                """)

                # Extrair estrutura de módulos/links
                content_structure = await page.evaluate("""
                    () => {
                        const modules = [];
                        const links = [];

                        // Procurar por módulos de conteúdo
                        const moduleElements = document.querySelectorAll('.d2l-le-TreeAccordionLeaf, .d2l-collapsepane, [role="treeitem"]');
                        moduleElements.forEach((elem, idx) => {
                            const title = elem.textContent.trim().substring(0, 200);
                            if (title && title.length > 0) {
                                modules.push({
                                    index: idx + 1,
                                    title: title
                                });
                            }
                        });

                        // Extrair links importantes
                        const linkElements = document.querySelectorAll('a[href*="/d2l/"]');
                        const seenUrls = new Set();
                        linkElements.forEach((link) => {
                            const href = link.href;
                            const text = link.textContent.trim();
                            if (href && text && !seenUrls.has(href) && text.length > 0 && text.length < 200) {
                                seenUrls.add(href);
                                links.push({
                                    text: text,
                                    url: href
                                });
                            }
                        });

                        return {
                            modules: modules,
                            links: links.slice(0, 50)  // Limitar a 50 links
                        };
                    }
                """)

                # Limpar conteúdo
                main_content = main_content.strip() if main_content else ""
                main_content = '\n'.join(line.strip() for line in main_content.split('\n') if line.strip())

                print(f"   ✅ Título: {page_title}")
                print(f"   ✅ Conteúdo principal: {len(main_content)} caracteres")
                print(f"   ✅ Módulos encontrados: {len(content_structure['modules'])}")
                print(f"   ✅ Links encontrados: {len(content_structure['links'])}")

                # SALVAR RESULTADO
                print("\n" + "="*80)
                print("SALVANDO RESULTADOS")
                print("="*80)

                output = {
                    "url": content_url,
                    "course_id": course_id,
                    "extracted_at": __import__('datetime').datetime.now().isoformat(),
                    "page_title": page_title,
                    "content": main_content,
                    "content_length": len(main_content),
                    "html_structure": {
                        "modules_count": len(content_structure['modules']),
                        "modules": content_structure['modules'],
                        "links_count": len(content_structure['links']),
                        "links": content_structure['links']
                    }
                }

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)

                print(f"\n✓ Arquivo salvo: {output_file}")
                print(f"✓ Título: {page_title}")
                print(f"✓ Conteúdo: {output['content_length']} caracteres")
                print(f"✓ Módulos: {output['html_structure']['modules_count']}")
                print(f"✓ Links: {output['html_structure']['links_count']}")

                return output

            except Exception as e:
                print(f"\n✗ ERRO FATAL: {str(e)}")
                raise

            finally:
                if should_close_browser and browser:
                    await browser.close()
    else:
        # Usar página compartilhada (login já feito)
        try:
            print("="*80)
            print(f"EXTRATOR D2L - CONTEÚDO DA PÁGINA HOME (Curso: {course_id})")
            print("="*80)

            # ETAPA 1: Tentar acessar diretamente (pode já estar logado)
            print("\n[1/3] Tentando acessar página (verificando login)...")
            content_url = f"https://www.fanshaweonline.ca/d2l/home/{course_id}"
            await page.goto(content_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 3.0))

            # Verificar se foi redirecionado para login
            if "login" in page.url.lower():
                print("  → Login necessário, fazendo autenticação...")
                await try_login_if_needed(page, username, password)

                # Tentar acessar página novamente após login
                await page.goto(content_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(2.0, 3.0))
            else:
                print("  ✓ Acesso direto bem-sucedido (sessão ativa)")

            print(f"\n✓ Página acessada! URL: {page.url[:60]}...\n")

            # ETAPA 2: Extrair conteúdo
            print("[2/2] Extraindo conteúdo da página...")

            # Extrair título da página
            page_title = await page.evaluate("""
                () => {
                    return document.title || 'Sem título';
                }
            """)

            # Extrair conteúdo principal
            main_content = await page.evaluate("""
                () => {
                    const main = document.querySelector('[role="main"]') ||
                                 document.querySelector('.d2l-page-main') ||
                                 document.querySelector('main') ||
                                 document.body;

                    return main.innerText.trim();
                }
            """)

            # Extrair estrutura de módulos/links
            content_structure = await page.evaluate("""
                () => {
                    const modules = [];
                    const links = [];

                    // Procurar por módulos de conteúdo
                    const moduleElements = document.querySelectorAll('.d2l-le-TreeAccordionLeaf, .d2l-collapsepane, [role="treeitem"]');
                    moduleElements.forEach((elem, idx) => {
                        const title = elem.textContent.trim().substring(0, 200);
                        if (title && title.length > 0) {
                            modules.push({
                                index: idx + 1,
                                title: title
                            });
                        }
                    });

                    // Extrair links importantes
                    const linkElements = document.querySelectorAll('a[href*="/d2l/"]');
                    const seenUrls = new Set();
                    linkElements.forEach((link) => {
                        const href = link.href;
                        const text = link.textContent.trim();
                        if (href && text && !seenUrls.has(href) && text.length > 0 && text.length < 200) {
                            seenUrls.add(href);
                            links.push({
                                text: text,
                                url: href
                            });
                        }
                    });

                    return {
                        modules: modules,
                        links: links.slice(0, 50)  // Limitar a 50 links
                    };
                }
            """)

            # Limpar conteúdo
            main_content = main_content.strip() if main_content else ""
            main_content = '\n'.join(line.strip() for line in main_content.split('\n') if line.strip())

            print(f"   ✅ Título: {page_title}")
            print(f"   ✅ Conteúdo principal: {len(main_content)} caracteres")
            print(f"   ✅ Módulos encontrados: {len(content_structure['modules'])}")
            print(f"   ✅ Links encontrados: {len(content_structure['links'])}")

            # SALVAR RESULTADO
            print("\n" + "="*80)
            print("SALVANDO RESULTADOS")
            print("="*80)

            output = {
                "url": content_url,
                "course_id": course_id,
                "extracted_at": __import__('datetime').datetime.now().isoformat(),
                "page_title": page_title,
                "content": main_content,
                "content_length": len(main_content),
                "html_structure": {
                    "modules_count": len(content_structure['modules']),
                    "modules": content_structure['modules'],
                    "links_count": len(content_structure['links']),
                    "links": content_structure['links']
                }
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Arquivo salvo: {output_file}")
            print(f"✓ Título: {page_title}")
            print(f"✓ Conteúdo: {output['content_length']} caracteres")
            print(f"✓ Módulos: {output['html_structure']['modules_count']}")
            print(f"✓ Links: {output['html_structure']['links_count']}")

            return output

        except Exception as e:
            print(f"\n✗ ERRO FATAL: {str(e)}")
            raise

if __name__ == "__main__":
    # Parse argumentos
    parser = argparse.ArgumentParser(description='Extrai conteúdo da página Home de um curso D2L')
    parser.add_argument('--course-id', type=str, default='2001540',
                        help='ID do curso D2L (padrão: 2001540)')
    parser.add_argument('--output', type=str, default=None,
                        help='Arquivo de saída (padrão: content_home_{course_id}.json)')
    args = parser.parse_args()

    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  EXTRATOR D2L - CONTEÚDO DA PÁGINA HOME".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print(f"\n📚 Curso ID: {args.course_id}\n")

    result = asyncio.run(extract_content_home(args.course_id, args.output))

    print("\n" + "="*80)
    print("CONCLUÍDO COM SUCESSO!")
    print("="*80)
    print(f"Curso: {args.course_id}")
    print(f"Arquivo gerado: {args.output or f'content_home_{args.course_id}.json'}")
    print(f"Título da página: {result['page_title']}")
    print(f"Conteúdo extraído: {result['content_length']} caracteres")
    print(f"Módulos encontrados: {result['html_structure']['modules_count']}")
    print(f"Links encontrados: {result['html_structure']['links_count']}")
    print("="*80 + "\n")
