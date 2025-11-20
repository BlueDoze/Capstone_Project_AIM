"""
D2L/Brightspace Event Scraper for Fanshawe Online
Extrai eventos da plataforma D2L usando Playwright para navegação autenticada.
"""

import asyncio
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout


class D2LEventScraper:
    """
    Scraper para extrair eventos do sistema D2L/Brightspace da Fanshawe College.

    Usa Playwright para navegar na plataforma autenticada e extrair informações
    de eventos de forma estruturada.
    """

    def __init__(self, username: str = None, password: str = None, headless: bool = True):
        """
        Inicializa o scraper com credenciais de autenticação.

        Args:
            username: Username do D2L (padrão: D2L_USERNAME do .env)
            password: Password do D2L (padrão: D2L_PASSWORD do .env)
            headless: Executar browser em modo headless (padrão: True)
        """
        self.username = username or os.getenv("D2L_USERNAME")
        self.password = password or os.getenv("D2L_PASSWORD")
        self.headless = headless
        self.base_url = "https://www.fanshaweonline.ca"

        if not self.username or not self.password:
            raise ValueError(
                "Credenciais não fornecidas. Configure D2L_USERNAME e D2L_PASSWORD "
                "nas variáveis de ambiente ou passe como parâmetros."
            )

    async def scrape_events(self, course_id: str = "2001540") -> List[Dict[str, Any]]:
        """
        Scrape eventos da página de curso D2L.

        Args:
            course_id: ID do curso D2L (padrão: "2001540")

        Returns:
            Lista de dicionários com dados dos eventos

        Raises:
            Exception: Em caso de erro de login ou scraping
        """
        print(f"[D2L Scraper] Iniciando scraping para curso {course_id}...")

        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            try:
                # Etapa 1: Login
                print("[D2L Scraper] Fazendo login...")
                await self._login(page)
                print("[D2L Scraper] Login bem-sucedido!")

                # Etapa 2: Navegar para a página do curso
                print(f"[D2L Scraper] Navegando para curso {course_id}...")
                course_url = f"{self.base_url}/d2l/le/content/{course_id}/Home"
                await page.goto(course_url, wait_until="networkidle", timeout=30000)
                print("[D2L Scraper] Página do curso carregada!")

                # Etapa 3: Extrair eventos
                print("[D2L Scraper] Extraindo eventos da página...")
                events = await self._extract_events(page)
                print(f"[D2L Scraper] {len(events)} eventos extraídos com sucesso!")

                return events

            except Exception as e:
                print(f"[D2L Scraper] ERRO durante scraping: {str(e)}")
                # Capturar screenshot para debug
                try:
                    await page.screenshot(path="debug_screenshot.png")
                    print("[D2L Scraper] Screenshot de debug salvo em debug_screenshot.png")
                except:
                    pass
                raise
            finally:
                await browser.close()

    async def _login(self, page: Page) -> None:
        """
        Realiza login no sistema D2L via Microsoft SSO.

        O Fanshawe Online usa autenticação Microsoft Azure AD,
        então o fluxo de login é redirecionado para login.microsoftonline.com.

        Args:
            page: Página do Playwright

        Raises:
            Exception: Se login falhar
        """
        try:
            # Navegar para página de login
            login_url = f"{self.base_url}/d2l/login"
            print(f"[D2L Scraper] Navegando para: {login_url}")
            await page.goto(login_url, wait_until="networkidle", timeout=30000)

            current_url = page.url
            print(f"[D2L Scraper] URL atual após redirect: {current_url}")

            # Aguardar um pouco para página carregar completamente
            await asyncio.sleep(2)

            # ETAPA 1: Preencher email (Microsoft SSO)
            # O Fanshawe redireciona para login.microsoftonline.com
            print("[D2L Scraper] Aguardando campo de email...")

            # Campo de email do Microsoft (id="i0116", name="loginfmt")
            await page.wait_for_selector("input#i0116", timeout=10000)
            print("[D2L Scraper] Campo de email encontrado (Microsoft SSO)")

            await page.fill("input#i0116", self.username)
            print(f"[D2L Scraper] Email preenchido: {self.username[:3]}***")

            # Clicar no botão "Next" (id="idSIButton9")
            await page.click("input#idSIButton9")
            print("[D2L Scraper] Botão 'Next' clicado")

            # Aguardar navegação para tela de senha
            await page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)

            # ETAPA 2: Preencher senha (Microsoft SSO)
            print("[D2L Scraper] Aguardando campo de senha...")

            # Campo de senha do Microsoft (id="i0118", name="passwd")
            await page.wait_for_selector("input#i0118", timeout=10000)
            print("[D2L Scraper] Campo de senha encontrado")

            await page.fill("input#i0118", self.password)
            print("[D2L Scraper] Senha preenchida")

            # Clicar no botão "Sign in" (id="idSIButton9")
            await page.click("input#idSIButton9")
            print("[D2L Scraper] Botão 'Sign in' clicado")

            # Aguardar login completar
            await page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(2)

            # ETAPA 3: Verificar se há tela "Stay signed in?"
            print("[D2L Scraper] Verificando tela 'Stay signed in?'...")
            try:
                # Botão "No" geralmente tem id="idBtn_Back"
                stay_signed_in_button = await page.query_selector("input#idSIButton9")
                if stay_signed_in_button:
                    button_text = await page.text_content("div#lightbox")
                    if "stay signed in" in button_text.lower():
                        print("[D2L Scraper] Tela 'Stay signed in?' detectada - clicando 'Yes'")
                        await stay_signed_in_button.click()
                        await page.wait_for_load_state("networkidle", timeout=15000)
            except:
                # Se não houver tela "stay signed in", continuar normalmente
                pass

            # Aguardar redirecionamento de volta para D2L
            await asyncio.sleep(3)
            current_url = page.url
            print(f"[D2L Scraper] Login completado. URL atual: {current_url}")

            # Verificar se login foi bem-sucedido
            # Após login, deve estar na URL do D2L (fanshaweonline.ca/d2l)
            if "fanshaweonline.ca/d2l" not in current_url:
                raise Exception(
                    f"Login pode ter falhado. URL atual não é do D2L: {current_url}\n"
                    "Verifique suas credenciais."
                )

            print("[D2L Scraper] Login verificado com sucesso!")

        except PlaywrightTimeout as e:
            # Capturar screenshot para debug em caso de timeout
            try:
                await page.screenshot(path="login_error_screenshot.png")
                print(f"[D2L Scraper] Screenshot de erro salvo em login_error_screenshot.png")
            except:
                pass
            raise Exception(f"Timeout durante login: {str(e)}")
        except Exception as e:
            # Capturar screenshot para debug em caso de erro
            try:
                await page.screenshot(path="login_error_screenshot.png")
                print(f"[D2L Scraper] Screenshot de erro salvo em login_error_screenshot.png")
            except:
                pass
            raise Exception(f"Erro durante login: {str(e)}")

    async def _extract_events(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extrai dados de eventos da página D2L.

        Args:
            page: Página do Playwright já navegada ao curso

        Returns:
            Lista de eventos extraídos
        """
        events = []

        try:
            # Aguardar conteúdo principal carregar
            await page.wait_for_selector("[role='main'], .d2l-page-main, #ContentView", timeout=15000)

            # Aguardar um pouco para JavaScript dinâmico carregar
            await asyncio.sleep(2)

            # Obter HTML completo para análise
            html_content = await page.content()

            # Estratégia 1: Procurar por elementos de calendário/eventos
            calendar_selectors = [
                ".d2l-calendar-event",
                "[class*='calendar'][class*='event']",
                "[class*='upcoming-event']",
                ".d2l-widget-header:has-text('Event') ~ .d2l-widget-content",
                "[data-location*='event']"
            ]

            event_elements = []
            for selector in calendar_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"[D2L Scraper] Encontrados {len(elements)} elementos com seletor: {selector}")
                        event_elements.extend(elements)
                except:
                    continue

            # Estratégia 2: Procurar por listas de itens de conteúdo
            content_selectors = [
                ".d2l-datalist-item",
                "[class*='content-item']",
                ".d2l-le-TreeListItem",
                "li[role='treeitem']"
            ]

            for selector in content_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"[D2L Scraper] Encontrados {len(elements)} itens de conteúdo: {selector}")
                        event_elements.extend(elements)
                except:
                    continue

            # Processar cada elemento encontrado
            for idx, element in enumerate(event_elements):
                try:
                    event = await self._parse_event_element(element, page)
                    if event and event.get('name'):  # Apenas adicionar se tiver ao menos um nome
                        events.append(event)
                        print(f"[D2L Scraper] Evento {idx+1} extraído: {event['name'][:50]}...")
                except Exception as e:
                    print(f"[D2L Scraper] Erro ao processar elemento {idx+1}: {str(e)}")
                    continue

            # Se não encontramos eventos, tentar extração genérica de texto
            if not events:
                print("[D2L Scraper] Nenhum evento encontrado com seletores específicos. Tentando extração genérica...")
                events = await self._generic_text_extraction(page)

        except Exception as e:
            print(f"[D2L Scraper] Erro durante extração de eventos: {str(e)}")

        return events

    async def _parse_event_element(self, element, page: Page) -> Optional[Dict[str, Any]]:
        """
        Extrai dados estruturados de um elemento de evento.

        Args:
            element: Elemento HTML do Playwright
            page: Página do Playwright (para contexto)

        Returns:
            Dicionário com dados do evento ou None
        """
        try:
            # Obter texto completo do elemento
            text_content = await element.text_content()
            if not text_content or len(text_content.strip()) < 3:
                return None

            text_content = text_content.strip()

            # Tentar obter subelementos
            title_element = await element.query_selector("h1, h2, h3, h4, .d2l-heading, [class*='title']")
            title = await title_element.text_content() if title_element else text_content.split('\n')[0]

            # Extrair datas usando regex
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',  # 2025-11-20
                r'\d{2}/\d{2}/\d{4}',  # 11/20/2025
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}',  # Nov 20, 2025
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'  # 20/11/25
            ]

            extracted_date = None
            for pattern in date_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    extracted_date = match.group(0)
                    break

            # Extrair horários
            time_pattern = r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?'
            time_matches = re.findall(time_pattern, text_content, re.IGNORECASE)
            extracted_time = ', '.join(time_matches) if time_matches else None

            # Procurar localização (palavras-chave comuns)
            location_keywords = ['Room', 'Building', 'Hall', 'Campus', 'Online', 'Virtual', 'SC', 'F Building']
            extracted_location = None
            for keyword in location_keywords:
                if keyword.lower() in text_content.lower():
                    # Extrair frase contendo a palavra-chave
                    match = re.search(rf'([^\n.]*{keyword}[^\n.]*)', text_content, re.IGNORECASE)
                    if match:
                        extracted_location = match.group(1).strip()
                        break

            if not extracted_location:
                extracted_location = "Fanshawe College"

            # Criar estrutura de evento
            event = {
                "name": title.strip() if title else "Untitled Event",
                "date": extracted_date or "TBD",
                "time": extracted_time or "All Day",
                "location": extracted_location,
                "description": text_content[:200] + "..." if len(text_content) > 200 else text_content,
                "category": "academic",
                "source": "d2l_scraper",
                "scraped_at": datetime.now().isoformat()
            }

            return event

        except Exception as e:
            print(f"[D2L Scraper] Erro ao parsear elemento: {str(e)}")
            return None

    async def _generic_text_extraction(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extração genérica baseada em texto quando seletores específicos falham.

        Args:
            page: Página do Playwright

        Returns:
            Lista de eventos extraídos de forma genérica
        """
        events = []

        try:
            # Obter todo o texto visível da área de conteúdo
            main_content = await page.query_selector("[role='main'], .d2l-page-main, #ContentView, main")

            if main_content:
                text = await main_content.text_content()

                # Procurar por padrões que indiquem eventos
                # Por exemplo, linhas com datas
                lines = text.split('\n')

                for line in lines:
                    line = line.strip()
                    if len(line) < 10:  # Ignorar linhas muito curtas
                        continue

                    # Se a linha contém uma data, pode ser um evento
                    if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}', line):
                        event = {
                            "name": line[:100],
                            "date": "Check description",
                            "time": "TBD",
                            "location": "Fanshawe College",
                            "description": line,
                            "category": "academic",
                            "source": "d2l_generic_extraction",
                            "scraped_at": datetime.now().isoformat()
                        }
                        events.append(event)

                        if len(events) >= 20:  # Limitar a 20 eventos genéricos
                            break

        except Exception as e:
            print(f"[D2L Scraper] Erro na extração genérica: {str(e)}")

        return events

    async def scrape_with_screenshot(self, course_id: str = "2001540", screenshot_path: str = "d2l_page.png") -> tuple:
        """
        Scrape eventos e salva screenshot da página para debug.

        Args:
            course_id: ID do curso D2L
            screenshot_path: Caminho para salvar screenshot

        Returns:
            Tupla (eventos, caminho_screenshot)
        """
        print(f"[D2L Scraper] Iniciando scraping com screenshot...")

        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            try:
                await self._login(page)

                course_url = f"{self.base_url}/d2l/le/content/{course_id}/Home"
                await page.goto(course_url, wait_until="networkidle", timeout=30000)

                # Capturar screenshot
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"[D2L Scraper] Screenshot salvo em: {screenshot_path}")

                events = await self._extract_events(page)

                return events, screenshot_path

            finally:
                await browser.close()
