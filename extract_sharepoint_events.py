"""
Script para extrair eventos do calendário SharePoint da Fanshawe.
Endpoint: https://fanshawecca.sharepoint.com/_layouts/15/Events.aspx
"""

import asyncio
import os
import json
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()

# SharePoint Events List GUID (hardcoded)
SHAREPOINT_EVENTS_LIST_GUID = "d1ad5108-61da-44a6-9b0a-d114a09c5e7e"
MAX_EVENTS_LIMIT = 100

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

        # Verifica se saiu da página de 2FA (aceitar ambos fanshaweonline.ca e sharepoint.com)
        if "login.microsoftonline.com" not in current_url and ("fanshaweonline.ca" in current_url or "sharepoint.com" in current_url):
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
    if "login" not in current_url.lower() and ("fanshaweonline.ca" in current_url or "sharepoint.com" in current_url):
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


async def extract_sharepoint_events(start_date=None, end_date=None, output_file=None, debug=False):
    """
    Extrai eventos do calendário SharePoint da Fanshawe.
    
    Args:
        start_date: Data inicial no formato YYYY-MM-DD (padrão: hoje)
        end_date: Data final no formato YYYY-MM-DD (padrão: hoje + 30 dias)
        output_file: Caminho customizado para salvar JSON
        debug: Se True, salva screenshot para debugging
    
    Returns:
        Dict com eventos e metadata
    """
    
    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME e D2L_PASSWORD no .env")

    # Definir datas padrão
    if start_date is None:
        start_date = datetime.now().strftime("%Y-%m-%d")
    if end_date is None:
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    # Definir arquivo de saída
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path('data/sharepoint_events')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f'events_{timestamp}.json'
    else:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

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

        events = []

        try:
            print("="*80)
            print("EXTRATOR SHAREPOINT - EVENTOS DO CALENDÁRIO")
            print("="*80)

            # ETAPA 1: Construir URL do SharePoint
            sharepoint_url = f"https://fanshawecca.sharepoint.com/_layouts/15/Events.aspx?ListGuid={SHAREPOINT_EVENTS_LIST_GUID}&StartDate={start_date}&EndDate={end_date}&AudienceTarget=false"
            
            print(f"\n[1/4] Navegando para SharePoint...")
            print(f"  → URL: {sharepoint_url[:80]}...")
            print(f"  → Período: {start_date} até {end_date}")
            
            await page.goto(sharepoint_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 3.5))

            # ETAPA 2: Autenticação
            print("\n[2/4] Verificando autenticação...")
            
            # Verificar se foi redirecionado para login
            if "login" in page.url.lower():
                await try_login_if_needed(page, username, password)
                
                # Tentar acessar página novamente após login
                await page.goto(sharepoint_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(2.0, 3.5))
            else:
                print("  ✓ Acesso direto bem-sucedido (sessão ativa)")

            print(f"\n✓ Página carregada! URL: {page.url[:60]}...\n")

            # ETAPA 3: Aguardar eventos carregarem
            print("[3/4] Aguardando eventos carregarem...")
            await asyncio.sleep(random.uniform(3.0, 5.0))

            # Debug screenshot se solicitado
            if debug:
                screenshot_path = "debug_sharepoint_events.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"  📸 Screenshot salvo: {screenshot_path}")

            # ETAPA 4: Extrair eventos com múltiplas estratégias
            print("\n[4/4] Extraindo eventos...")
            
            events_data = await page.evaluate(f"""
                () => {{
                    const MAX_EVENTS = {MAX_EVENTS_LIMIT};
                    const events = [];
                    let extractionMethod = null;
                    
                    // Estratégia 1: Card-based events (SharePoint Modern Events Web Part)
                    try {{
                        const eventCards = document.querySelectorAll('[data-automation-id="event-card-fluent"]');
                        if (eventCards.length > 0) {{
                            extractionMethod = 'modern_event_cards';
                            eventCards.forEach((card, idx) => {{
                                if (idx >= MAX_EVENTS) return;
                                
                                // Título do evento
                                const titleElem = card.querySelector('[data-automation-id="event-card-title"]');
                                const title = titleElem ? titleElem.textContent.trim() : '';
                                
                                // Data/hora
                                const dateElems = card.querySelectorAll('span[class*="date"]');
                                let dateText = '';
                                dateElems.forEach(elem => {{
                                    const text = elem.textContent.trim();
                                    if (text && text.match(/[A-Z][a-z]{{2}},|\\d{{1,2}}:\\d{{2}}/)) {{
                                        dateText = text;
                                    }}
                                }});
                                
                                // Localização
                                const locationElems = card.querySelectorAll('span[class*="location"]');
                                let location = '';
                                locationElems.forEach(elem => {{
                                    const text = elem.textContent.trim();
                                    if (text && text.length > 3) {{
                                        location = text;
                                    }}
                                }});
                                
                                // Categoria
                                const categoryElems = card.querySelectorAll('span[class*="category"]');
                                let category = '';
                                categoryElems.forEach(elem => {{
                                    const text = elem.textContent.trim();
                                    if (text && text.length > 1) {{
                                        category = text;
                                    }}
                                }});
                                
                                // Link do evento (tentar extrair do card container)
                                const parentLink = card.closest('[role="button"]');
                                let link = '';
                                if (parentLink) {{
                                    const ariaLabel = parentLink.getAttribute('aria-label');
                                    // Link pode estar em aria-label ou precisamos construir
                                    link = window.location.href; // Base URL por enquanto
                                }}
                                
                                if (title) {{
                                    events.push({{
                                        title: title,
                                        date: dateText,
                                        location: location,
                                        category: category,
                                        link: link,
                                        description: ''
                                    }});
                                }}
                            }});
                        }}
                    }} catch (e) {{
                        console.log('Strategy 1 failed:', e);
                    }}
                    
                    // Estratégia 2: List cells com role="listitem"
                    if (events.length === 0) {{
                        try {{
                            const listCells = document.querySelectorAll('[data-automationid="ListCell"]');
                            if (listCells.length > 0) {{
                                extractionMethod = 'list_cell_items';
                                listCells.forEach((cell, idx) => {{
                                    if (idx >= MAX_EVENTS) return;
                                    
                                    // Buscar título
                                    const titleElem = cell.querySelector('span[class*="title"]');
                                    const title = titleElem ? titleElem.textContent.trim() : '';
                                    
                                    // Buscar data
                                    const dateSpans = cell.querySelectorAll('span');
                                    let dateText = '';
                                    dateSpans.forEach(span => {{
                                        const text = span.textContent;
                                        if (text.match(/[A-Z][a-z]{{2}},.*\\d{{1,2}}:\\d{{2}}/)) {{
                                            dateText = text;
                                        }}
                                    }});
                                    
                                    // Buscar localização
                                    let location = '';
                                    dateSpans.forEach(span => {{
                                        const text = span.textContent.trim();
                                        if (text && !text.match(/^[A-Z]{{3}}$/) && !text.match(/\\d{{1,2}}:\\d{{2}}/) && text.length > 5) {{
                                            if (!location || text.length > location.length) {{
                                                location = text;
                                            }}
                                        }}
                                    }});
                                    
                                    if (title) {{
                                        events.push({{
                                            title: title,
                                            date: dateText,
                                            location: location,
                                            category: '',
                                            link: '',
                                            description: ''
                                        }});
                                    }}
                                }});
                            }}
                        }} catch (e) {{
                            console.log('Strategy 2 failed:', e);
                        }}
                    }}
                    
                    // Estratégia 3: Aria-label parsing (fallback)
                    if (events.length === 0) {{
                        try {{
                            const ariaItems = document.querySelectorAll('[aria-label*="Event"]');
                            if (ariaItems.length > 0) {{
                                extractionMethod = 'aria_label_parsing';
                                ariaItems.forEach((item, idx) => {{
                                    if (idx >= MAX_EVENTS) return;
                                    
                                    const ariaLabel = item.getAttribute('aria-label');
                                    if (ariaLabel) {{
                                        // Parse do aria-label (ex: "Events Event Open House. Starts on...")
                                        const titleMatch = ariaLabel.match(/Event\\s+([^.]+)\\./);
                                        const dateMatch = ariaLabel.match(/Starts on\\s+([^.]+)/);
                                        const locationMatch = ariaLabel.match(/at\\s+([^.]+)\\./);
                                        
                                        const title = titleMatch ? titleMatch[1].trim() : '';
                                        const dateText = dateMatch ? dateMatch[1].trim() : '';
                                        const location = locationMatch ? locationMatch[1].trim() : '';
                                        
                                        if (title) {{
                                            events.push({{
                                                title: title,
                                                date: dateText,
                                                location: location,
                                                category: '',
                                                link: '',
                                                description: ''
                                            }});
                                        }}
                                    }}
                                }});
                            }}
                        }} catch (e) {{
                            console.log('Strategy 3 failed:', e);
                        }}
                    }}
                    
                    return {{
                        events: events.slice(0, MAX_EVENTS),
                        extractionMethod: extractionMethod,
                        totalFound: events.length
                    }};
                }}
            """)

            events = events_data.get('events', [])
            extraction_method = events_data.get('extractionMethod')
            total_found = events_data.get('totalFound', 0)

            print(f"  ✓ Método de extração: {extraction_method or 'unknown'}")
            print(f"  ✓ Eventos encontrados: {len(events)}")
            
            if total_found >= MAX_EVENTS_LIMIT:
                print(f"\n⚠️  AVISO: Limite máximo de eventos ({MAX_EVENTS_LIMIT}) atingido!")
                print(f"    Pode haver mais eventos neste período.")
                print(f"    Considere usar um intervalo de datas menor.\n")

            # Processar e estruturar eventos
            processed_events = []
            for idx, event in enumerate(events, 1):
                processed_event = {
                    "id": f"sp_evt_{idx:03d}",
                    "name": event.get('title', ''),
                    "date": event.get('date', ''),
                    "time": "",  # Extrair do campo date se presente
                    "location": event.get('location', ''),
                    "description": event.get('description', '')[:200],
                    "category": "sharepoint",
                    "source": "sharepoint",
                    "link": event.get('link', '')
                }
                processed_events.append(processed_event)

            # SALVAR RESULTADO
            print("\n" + "="*80)
            print("SALVANDO RESULTADOS")
            print("="*80)

            output = {
                "metadata": {
                    "source": "sharepoint_scraper",
                    "scraped_at": datetime.now().isoformat(),
                    "total_events": len(processed_events),
                    "endpoint": sharepoint_url,
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "max_events_limit": MAX_EVENTS_LIMIT,
                    "extraction_method": extraction_method
                },
                "events": processed_events
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Arquivo salvo: {output_file}")
            print(f"✓ Total de eventos: {len(processed_events)}")
            print(f"✓ Período: {start_date} até {end_date}")
            print(f"✓ Método de extração: {extraction_method or 'unknown'}")

            return output

        except Exception as e:
            print(f"\n✗ ERRO FATAL: {str(e)}")
            
            # Tentar salvar resultados parciais
            if events:
                partial_output = {
                    "metadata": {
                        "source": "sharepoint_scraper",
                        "scraped_at": datetime.now().isoformat(),
                        "partial": True,
                        "error": str(e),
                        "total_events": len(events)
                    },
                    "events": events
                }
                
                partial_file = Path('data/sharepoint_events/events_partial.json')
                partial_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(partial_file, 'w', encoding='utf-8') as f:
                    json.dump(partial_output, f, indent=2, ensure_ascii=False)
                
                print(f"✓ Resultados parciais salvos em: {partial_file}")
            
            raise

        finally:
            await browser.close()


if __name__ == "__main__":
    # Parse argumentos
    parser = argparse.ArgumentParser(description='Extrai eventos do calendário SharePoint da Fanshawe')
    parser.add_argument('--start-date', type=str, default=None,
                        help='Data inicial (YYYY-MM-DD, padrão: hoje)')
    parser.add_argument('--end-date', type=str, default=None,
                        help='Data final (YYYY-MM-DD, padrão: hoje + 30 dias)')
    parser.add_argument('--output', type=str, default=None,
                        help='Arquivo de saída customizado')
    parser.add_argument('--debug', action='store_true',
                        help='Ativar modo debug (salva screenshots)')
    args = parser.parse_args()

    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  EXTRATOR SHAREPOINT - CALENDÁRIO DE EVENTOS".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    start = args.start_date or datetime.now().strftime("%Y-%m-%d")
    end = args.end_date or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    print(f"\n📅 Período: {start} até {end}\n")

    result = asyncio.run(extract_sharepoint_events(
        start_date=args.start_date,
        end_date=args.end_date,
        output_file=args.output,
        debug=args.debug
    ))

    print("\n" + "="*80)
    print("CONCLUÍDO COM SUCESSO!")
    print("="*80)
    print(f"Total de eventos: {result['metadata']['total_events']}")
    print(f"Período: {result['metadata']['date_range']['start_date']} até {result['metadata']['date_range']['end_date']}")
    print(f"Arquivo: {args.output or 'data/sharepoint_events/events_*.json'}")
    print("="*80 + "\n")
