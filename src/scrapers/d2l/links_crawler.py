"""
Script para percorrer todos os links extraídos de content_home_{course_id}.json,
acessar cada URL autenticada no D2L e salvar o conteúdo em arquivos JSON individuais.
"""

import asyncio
import os
import json
import random
import re
import argparse
from pathlib import Path
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()

# Configurações
DELAY_BETWEEN_PAGES = (2.0, 4.0)  # segundos entre requisições


def sanitize_filename(text: str) -> str:
    """Converte texto em nome de arquivo válido."""
    # Remover emojis e caracteres especiais
    text = re.sub(r'[^\w\s-]', '', text)
    # Substituir espaços por underscore
    text = text.replace(' ', '_')
    # Remover underscores múltiplos
    text = re.sub(r'_+', '_', text)
    # Limitar tamanho
    text = text[:100]
    # Remover underscores no início/fim
    text = text.strip('_')
    return text or "unnamed"


async def wait_for_2fa_approval(page: Page, timeout=300000):
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
                        const match = text.match(/\\b(\\d{2})\\b/);
                        if (match) {
                            return match[1];
                        }
                    }
                }

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

        if "login.microsoftonline.com" not in current_url and "fanshaweonline.ca" in current_url:
            print("\n✅ AUTENTICAÇÃO APROVADA COM SUCESSO!\n")
            return True

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

        dots = (dots + 1) % 4
        loading_animation = "." * dots + " " * (3 - dots)
        elapsed_sec = elapsed // 1000

        if elapsed % 2000 == 0:
            print(f"\r   Aguardando{loading_animation} ({elapsed_sec}s)", end="", flush=True)

        if elapsed % 30000 == 0 and elapsed > 0:
            code_reminder = f" - Código: {verification_code}" if verification_code else ""
            print(f"\n   💡 Lembrete: Verifique seu celular{code_reminder} - {elapsed_sec}s decorridos")

    print("\n\n❌ TIMEOUT: Aprovação não detectada após 5 minutos")
    print("   Por favor, tente novamente.\n")
    return False


async def login_d2l(page: Page, username: str, password: str) -> bool:
    """Realiza login no D2L com autenticação Microsoft SSO."""
    try:
        print("\n[LOGIN] Iniciando autenticação D2L...")
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

        await asyncio.sleep(3)

        # Verificar se precisa de 2FA
        print("   → Verificando se 2FA é necessário...")
        await asyncio.sleep(2)
        current_url = page.url

        if "login.microsoftonline.com" in current_url or "Stay signed in" in await page.content():
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
                success = await wait_for_2fa_approval(page, timeout=300000)
                if not success:
                    return False

        await asyncio.sleep(2)
        print(f"\n✓ Login completado!\n")
        return True

    except Exception as e:
        print(f"\n✗ ERRO no login: {str(e)}")
        return False


async def extract_page_content(page: Page, url: str, link_text: str) -> dict:
    """Extrai conteúdo de uma página D2L."""
    try:
        print(f"  → Acessando página...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(random.uniform(2.0, 4.0))

        # Extrair título da página
        page_title = await page.evaluate("() => document.title || 'Sem título'")

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

        # Extrair links da página
        links = await page.evaluate("""
            () => {
                const linkElements = document.querySelectorAll('a[href]');
                const seenUrls = new Set();
                const links = [];

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

                return links.slice(0, 50);
            }
        """)

        # Limpar conteúdo
        main_content = main_content.strip() if main_content else ""
        main_content = '\n'.join(line.strip() for line in main_content.split('\n') if line.strip())

        return {
            "link_text": link_text,
            "url": url,
            "extracted_at": __import__('datetime').datetime.now().isoformat(),
            "page_title": page_title,
            "content": main_content,
            "content_length": len(main_content),
            "html_structure": {
                "links_count": len(links),
                "links": links
            }
        }

    except Exception as e:
        print(f"  ✗ Erro ao extrair conteúdo: {str(e)[:100]}")
        return None


async def crawl_links(course_id="2001540", input_file=None, output_dir=None):
    """Percorre todos os links de content_home_{course_id}.json e extrai conteúdo."""

    # Definir valores padrão
    if input_file is None:
        input_file = f'content_home_{course_id}.json'

    if output_dir is None:
        output_dir = f'/home/luizeng/Documents/fanshawe_repo/Capstone_Project_AIM/data/course_{course_id}'

    # Verificar arquivo de entrada
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Arquivo {input_file} não encontrado!")

    # Carregar links
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    links = data.get('html_structure', {}).get('links', [])
    if not links:
        raise ValueError(f"Nenhum link encontrado em {input_file}")

    # Criar diretório de saída
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Credenciais
    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME e D2L_PASSWORD no .env")

    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  CRAWLER DE LINKS D2L".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print(f"\n📚 Curso ID: {course_id}")
    print(f"📁 Diretório de saída: {output_dir}")
    print(f"📊 Total de links para processar: {len(links)}\n")

    async with async_playwright() as p:
        # Browser INVISÍVEL
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
            # LOGIN ÚNICO
            login_success = await login_d2l(page, username, password)
            if not login_success:
                raise Exception("Falha no login D2L")

            # Estatísticas
            processed = 0
            failed = 0
            results = []

            print("="*80)
            print("PROCESSANDO LINKS")
            print("="*80 + "\n")

            # Processar cada link
            for idx, link in enumerate(links, 1):
                link_text = link.get('text', f'link_{idx}')
                link_url = link.get('url', '')

                if not link_url:
                    print(f"[{idx}/{len(links)}] ⚠️  PULADO: '{link_text}' (URL vazia)")
                    failed += 1
                    continue

                print(f"[{idx}/{len(links)}] 🔍 Processando: '{link_text}'")
                print(f"  URL: {link_url[:70]}...")

                # Extrair conteúdo
                content = await extract_page_content(page, link_url, link_text)

                if content:
                    # Salvar arquivo
                    filename = sanitize_filename(link_text) + ".json"
                    filepath = os.path.join(output_dir, filename)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(content, f, indent=2, ensure_ascii=False)

                    print(f"  ✅ Salvo: {filename}")
                    print(f"     Título: {content['page_title'][:60]}...")
                    print(f"     Conteúdo: {content['content_length']} caracteres")
                    print(f"     Links: {content['html_structure']['links_count']}")

                    processed += 1
                    results.append({
                        'link_text': link_text,
                        'filename': filename,
                        'status': 'success'
                    })
                else:
                    print(f"  ✗ FALHOU: Erro ao extrair conteúdo")
                    failed += 1
                    results.append({
                        'link_text': link_text,
                        'status': 'failed'
                    })

                # Delay entre páginas (anti-bot)
                if idx < len(links):
                    delay = random.uniform(*DELAY_BETWEEN_PAGES)
                    print(f"  ⏳ Aguardando {delay:.1f}s...\n")
                    await asyncio.sleep(delay)

            # RESUMO FINAL
            print("\n" + "="*80)
            print("RESUMO FINAL")
            print("="*80)
            print(f"✅ Processados com sucesso: {processed}")
            print(f"✗ Falharam: {failed}")
            print(f"📊 Total: {len(links)}")
            print(f"📁 Diretório de saída: {output_dir}/")
            print("="*80 + "\n")

            # Salvar resumo
            summary = {
                "course_id": course_id,
                "processed_at": __import__('datetime').datetime.now().isoformat(),
                "total_links": len(links),
                "successful": processed,
                "failed": failed,
                "results": results
            }

            with open(os.path.join(output_dir, "_summary.json"), 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            print(f"✓ Resumo salvo em: {output_dir}/_summary.json\n")

            return summary

        except Exception as e:
            print(f"\n✗ ERRO FATAL: {str(e)}")
            raise

        finally:
            await browser.close()


if __name__ == "__main__":
    # Parse argumentos
    parser = argparse.ArgumentParser(description='Crawl e extrai conteúdo de links D2L')
    parser.add_argument('--course-id', type=str, default='2001540',
                        help='ID do curso D2L (padrão: 2001540)')
    parser.add_argument('--input', type=str, default=None,
                        help='Arquivo JSON de entrada (padrão: content_home_{course_id}.json)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Diretório de saída (padrão: data/course_{course_id}/)')
    args = parser.parse_args()

    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  CRAWLER DE LINKS D2L - EXTRAÇÃO AUTOMÁTICA".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print("\n")

    summary = asyncio.run(crawl_links(args.course_id, args.input, args.output_dir))

    print("\n✅ CONCLUÍDO COM SUCESSO!\n")
