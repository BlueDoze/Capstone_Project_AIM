"""
Script para extrair informações do professor da página Home do curso D2L.
Extrai: nome, email, office hours, office location do widget "Professor Information".
"""

import asyncio
import os
import json
import random
import argparse
from pathlib import Path
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


async def extract_professor_info(course_id="2001540", output_file=None, page=None, debug=False):
    """
    Extrai informações do professor do widget 'Professor Information' na página Home do curso.
    
    Args:
        course_id: ID do curso D2L
        output_file: Caminho para salvar o JSON (padrão: data/course_{COURSE_ID}/professor_info.json)
        page: Objeto page do Playwright (opcional, para reutilizar sessão)
        debug: Se True, salva screenshot para debugging
    
    Returns:
        Dict com informações do professor
    """
    
    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    # Definir arquivo de saída
    if output_file is None:
        course_dir = Path(f'data/course_{course_id}')
        course_dir.mkdir(parents=True, exist_ok=True)
        output_file = course_dir / 'professor_info.json'
    else:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

    # Se página foi fornecida (login compartilhado), usar ela
    should_close_browser = False
    browser = None

    # Se não tem página fornecida, criar nova
    if page is None:
        should_close_browser = True
        async with async_playwright() as p:
            # Browser em modo headless
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
                return await _extract_professor_info_impl(
                    page, course_id, output_file, username, password, debug
                )
            finally:
                if should_close_browser and browser:
                    await browser.close()
    else:
        # Usar página compartilhada (login já feito)
        return await _extract_professor_info_impl(
            page, course_id, output_file, username, password, debug
        )


async def _extract_professor_info_impl(page, course_id, output_file, username, password, debug):
    """Implementação interna da extração de informações do professor."""
    
    print("="*80)
    print(f"EXTRATOR D2L - INFORMAÇÕES DO PROFESSOR (Curso: {course_id})")
    print("="*80)

    # ETAPA 1: Acessar página home
    print("\n[1/3] Acessando página home do curso...")
    home_url = f"https://www.fanshaweonline.ca/d2l/home/{course_id}"
    await page.goto(home_url, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(random.uniform(2.0, 3.0))

    # Verificar se foi redirecionado para login
    if "login" in page.url.lower():
        print("  → Login necessário, fazendo autenticação...")
        await try_login_if_needed(page, username, password)

        # Tentar acessar página novamente após login
        await page.goto(home_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(random.uniform(2.0, 3.0))
    else:
        print("  ✓ Acesso direto bem-sucedido (sessão ativa)")

    print(f"\n✓ Página acessada! URL: {page.url[:60]}...\n")

    # ETAPA 2: Aguardar widget carregar
    print("[2/3] Aguardando widget 'Professor Information' carregar...")
    
    # Aguardar mais tempo para JavaScript renderizar completamente
    await asyncio.sleep(random.uniform(4.0, 6.0))
    
    # Tentar múltiplas vezes com delays
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Aguardar por qualquer indicador do widget
            await page.wait_for_selector('[role="complementary"], .d2l-widget, d2l-widget', timeout=5000)
            print(f"  ✓ Widget encontrado (tentativa {attempt + 1}/{max_attempts})")
            # Aguardar mais um pouco para conteúdo interno carregar
            await asyncio.sleep(random.uniform(2.0, 3.0))
            break
        except:
            if attempt < max_attempts - 1:
                print(f"  → Widget ainda não carregado, aguardando... (tentativa {attempt + 1}/{max_attempts})")
                await asyncio.sleep(3)
            else:
                print(f"  ⚠️  Widget não detectado após {max_attempts} tentativas, tentando extração mesmo assim...")
    
    # Aguardar conteúdo dinâmico adicional carregar
    await asyncio.sleep(random.uniform(2.0, 3.0))

    # ETAPA 3: Extrair informações do professor
    print("\n[3/3] Extraindo informações do professor...")
    
    professor_data = await page.evaluate("""
        () => {
            const result = {
                name: null,
                email: null,
                office: null,
                office_hours: null,
                raw_text: null,
                extraction_method: null,
                debug_info: []
            };
            
            // Debug: Listar todos os widgets na página
            const allWidgets = document.querySelectorAll('.d2l-widget, d2l-widget, [role="complementary"]');
            result.debug_info.push(`Total widgets found: ${allWidgets.length}`);
            
            // Estratégia 1: Procurar por widget com "Professor Information"
            const widgetSelectors = [
                // Seletores específicos para widget de professor
                'div[class*="professor"]',
                'div[class*="instructor"]',
                '[aria-label*="Professor"]',
                '[aria-label*="Instructor"]',
                // Seletores genéricos de widgets D2L
                '.d2l-widget',
                'd2l-widget',
                '[role="complementary"]'
            ];
            
            let professorWidget = null;
            let widgetTexts = [];
            
            for (const selector of widgetSelectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    result.debug_info.push(`Selector '${selector}': found ${elements.length} elements`);
                    
                    for (const elem of elements) {
                        const text = elem.innerText || elem.textContent || '';
                        widgetTexts.push(`${selector}: ${text.substring(0, 100)}`);
                        
                        if (text.includes('Professor') || text.includes('Instructor')) {
                            professorWidget = elem;
                            result.extraction_method = `widget_selector:${selector}`;
                            result.debug_info.push(`Found professor widget with selector: ${selector}`);
                            break;
                        }
                    }
                    if (professorWidget) break;
                } catch (e) {
                    result.debug_info.push(`Error with selector '${selector}': ${e.message}`);
                    continue;
                }
            }
            
            result.debug_info.push(`Widget texts: ${JSON.stringify(widgetTexts).substring(0, 200)}`);
            
            // Estratégia 2: Tentar acessar shadow DOM
            if (!professorWidget) {
                try {
                    const customElements = document.querySelectorAll('*');
                    result.debug_info.push(`Checking shadow DOM in ${customElements.length} elements`);
                    
                    for (const elem of customElements) {
                        if (elem.shadowRoot) {
                            const shadowText = elem.shadowRoot.textContent || '';
                            if (shadowText.includes('Professor') || shadowText.includes('Instructor')) {
                                professorWidget = elem.shadowRoot;
                                result.extraction_method = 'shadow_dom';
                                result.debug_info.push('Found in shadow DOM');
                                break;
                            }
                        }
                    }
                } catch (e) {
                    result.debug_info.push(`Shadow DOM error: ${e.message}`);
                }
            }
            
            // Estratégia 3: Buscar diretamente na área principal por texto estruturado
            if (!professorWidget) {
                const bodyText = document.body.innerText;
                result.debug_info.push(`Body text length: ${bodyText.length}`);
                
                if (bodyText.includes('Professor Information') || bodyText.includes('Instructor')) {
                    // Tentar encontrar o container que tem as informações visíveis
                    const mainContent = document.querySelector('[role="main"]') || document.body;
                    professorWidget = mainContent;
                    result.extraction_method = 'full_page_scan';
                    result.debug_info.push('Using full page scan');
                }
            }
            
            if (professorWidget) {
                const text = professorWidget.innerText || professorWidget.textContent || '';
                result.raw_text = text.substring(0, 2000);  // Aumentar para 2000 caracteres
                
                result.debug_info.push(`Widget text length: ${text.length}`);
                result.debug_info.push(`Widget text preview: ${text.substring(0, 300)}`);
                
                // Extrair nome (após "Name:" ou antes de newline após "Professor Information")
                const namePatterns = [
                    /Name:\\s*([^\\n]+)/i,
                    /Professor:\\s*([^\\n]+)/i,
                    /Instructor:\\s*([^\\n]+)/i,
                    /Professor Information[^\\n]*\\n+\\s*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)/i,
                    /(?:Professor|Instructor|Dr\\.|Prof\\.)\\s+([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)/
                ];
                
                for (const pattern of namePatterns) {
                    const match = text.match(pattern);
                    if (match && match[1]) {
                        const extractedName = match[1].trim();
                        // Validar: não pode ser "Information" ou "Loading"
                        if (extractedName !== 'Information' && extractedName !== 'Loading' && 
                            extractedName.length > 3 && extractedName.length < 100) {
                            result.name = extractedName;
                            result.debug_info.push(`Name extracted with pattern: ${pattern}`);
                            break;
                        }
                    }
                }
                
                // Extrair email (procurar por link mailto: ou padrão de email)
                const emailLink = professorWidget.querySelector('a[href^="mailto:"]');
                if (emailLink) {
                    result.email = emailLink.href.replace('mailto:', '').trim();
                    result.debug_info.push('Email found in mailto link');
                } else {
                    const emailMatch = text.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\\.[a-zA-Z]+)/);
                    if (emailMatch) {
                        result.email = emailMatch[1];
                        result.debug_info.push('Email extracted from text');
                    }
                }
                
                // Extrair office
                const officePatterns = [
                    /Office:\\s*([^\\n]+)/i,
                    /Office Location:\\s*([^\\n]+)/i,
                    /Room:\\s*([^\\n]+)/i
                ];
                
                for (const pattern of officePatterns) {
                    const match = text.match(pattern);
                    if (match && match[1]) {
                        result.office = match[1].trim();
                        result.debug_info.push(`Office extracted with pattern: ${pattern}`);
                        break;
                    }
                }
                
                // Extrair office hours
                const hoursPatterns = [
                    /Office Hours?:\\s*([^\\n]+(?:\\n(?!Email|Office:)[^\\n]+)*)/i,
                    /Hours?:\\s*([^\\n]+)/i,
                    /Availability:\\s*([^\\n]+)/i
                ];
                
                for (const pattern of hoursPatterns) {
                    const match = text.match(pattern);
                    if (match && match[1]) {
                        result.office_hours = match[1].trim();
                        result.debug_info.push(`Office hours extracted with pattern: ${pattern}`);
                        break;
                    }
                }
            } else {
                result.extraction_method = 'widget_not_found';
                result.debug_info.push('Professor widget not found anywhere');
            }
            
            return result;
        }
    """)
    
    # Debug screenshot se solicitado
    if debug:
        screenshot_path = f"debug_professor_{course_id}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"  📸 Screenshot salvo: {screenshot_path}")
    
    # Processar e limpar dados
    professor_info = {
        "course_id": course_id,
        "extracted_at": __import__('datetime').datetime.now().isoformat(),
        "source_url": home_url,
        "extraction_method": professor_data.get("extraction_method"),
        "name": professor_data.get("name"),
        "email": professor_data.get("email"),
        "office": professor_data.get("office"),
        "office_hours": professor_data.get("office_hours"),
        "raw_text_preview": professor_data.get("raw_text", "")[:500] if professor_data.get("raw_text") else None,
        "debug_info": professor_data.get("debug_info", [])
    }
    
    print(f"\n   Método de extração: {professor_info['extraction_method']}")
    print(f"   Nome: {professor_info['name'] or 'Não encontrado'}")
    print(f"   Email: {professor_info['email'] or 'Não encontrado'}")
    print(f"   Office: {professor_info['office'] or 'Não encontrado'}")
    print(f"   Office Hours: {professor_info['office_hours'] or 'Não encontrado'}")
    
    if debug and professor_info.get('debug_info'):
        print(f"\n   Debug info:")
        for info in professor_info['debug_info'][:10]:  # Mostrar primeiras 10 linhas
            print(f"   - {info}")
    
    if professor_info['raw_text_preview']:
        print(f"\n   Texto bruto extraído (preview):")
        print(f"   {professor_info['raw_text_preview'][:200]}...")
    
    # SALVAR RESULTADO
    print("\n" + "="*80)
    print("SALVANDO RESULTADOS")
    print("="*80)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(professor_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Arquivo salvo: {output_file}")
    print(f"✓ Nome do professor: {professor_info['name'] or 'NÃO EXTRAÍDO'}")
    print(f"✓ Email: {professor_info['email'] or 'NÃO EXTRAÍDO'}")
    
    return professor_info


if __name__ == "__main__":
    # Parse argumentos
    parser = argparse.ArgumentParser(description='Extrai informações do professor da página Home do curso D2L')
    parser.add_argument('--course-id', type=str, default='2001540',
                        help='ID do curso D2L (padrão: 2001540)')
    parser.add_argument('--output', type=str, default=None,
                        help='Arquivo de saída (padrão: data/course_{course_id}/professor_info.json)')
    parser.add_argument('--debug', action='store_true',
                        help='Ativar modo debug (salva screenshots)')
    args = parser.parse_args()

    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  EXTRATOR D2L - INFORMAÇÕES DO PROFESSOR".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print(f"\n👨‍🏫 Curso ID: {args.course_id}\n")

    result = asyncio.run(extract_professor_info(args.course_id, args.output, debug=args.debug))

    print("\n" + "="*80)
    if result['name']:
        print("CONCLUÍDO COM SUCESSO!")
    else:
        print("CONCLUÍDO - MAS NOME NÃO FOI EXTRAÍDO")
    print("="*80)
    print(f"Curso: {args.course_id}")
    print(f"Arquivo gerado: {args.output or f'data/course_{args.course_id}/professor_info.json'}")
    print(f"Professor: {result['name'] or 'NÃO ENCONTRADO'}")
    print(f"Email: {result['email'] or 'NÃO ENCONTRADO'}")
    print(f"Método: {result['extraction_method']}")
    print("="*80 + "\n")
