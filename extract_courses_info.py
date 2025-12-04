#!/usr/bin/env python3
"""
Script para extrair informações de múltiplos cursos D2L.
Processa lista de URLs de cursos e extrai conteúdo de cada um.
"""

import asyncio
import os
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Lista de URLs de cursos para processar
COURSE_URLS = [
    "https://www.fanshaweonline.ca/d2l/home/2001540",
    "https://www.fanshaweonline.ca/d2l/home/906769",
    "https://www.fanshaweonline.ca/d2l/home/2001539",
    "https://www.fanshaweonline.ca/d2l/home/2001542",
    "https://www.fanshaweonline.ca/d2l/home/2014765",
    "https://www.fanshaweonline.ca/d2l/home/2001541",
    "https://www.fanshaweonline.ca/d2l/home/2001538"
]

OUTPUT_DIR = "/home/luizeng/Documents/fanshawe_repo/Capstone_Project_AIM/data/courses_info"
DELAY_BETWEEN_COURSES = (3.0, 5.0)  # segundos entre cursos


async def wait_for_2fa(page: Page, timeout=90000):
    """Aguarda aprovação 2FA com detecção de código."""
    print("\n🔐 2FA DETECTADO - Aguardando aprovação...")
    
    try:
        verification_code = await page.evaluate("""
            () => {
                const elem = document.querySelector('#idRichContext_DisplaySign');
                if (elem) {
                    const match = elem.innerText.match(/\\b(\\d{2})\\b/);
                    return match ? match[1] : null;
                }
                return null;
            }
        """)
        
        if verification_code:
            print(f"📱 CÓDIGO: {verification_code}")
    except:
        pass
    
    print("⏳ Aprove no celular...")
    
    elapsed = 0
    while elapsed < timeout:
        current_url = page.url
        if "login.microsoftonline.com" not in current_url and "fanshaweonline.ca" in current_url:
            print("✅ 2FA aprovado!\n")
            return True
        
        await asyncio.sleep(2)
        elapsed += 2000
        
        if elapsed % 10000 == 0:
            print(f"   ... {elapsed // 1000}s")
    
    return False


async def login_d2l(page: Page, username: str, password: str) -> bool:
    """Realiza login no D2L."""
    try:
        print("\n[LOGIN] Autenticando no D2L...")
        await page.goto("https://www.fanshaweonline.ca/d2l/login", timeout=60000)
        await asyncio.sleep(2)

        # Preencher email
        print("  → Email...")
        await page.wait_for_selector("input#i0116", timeout=10000)
        await page.fill("input#i0116", username)
        await asyncio.sleep(1)
        await page.click("input#idSIButton9")
        await asyncio.sleep(2)

        # Preencher senha
        print("  → Senha...")
        await page.wait_for_selector("input#i0118", timeout=10000)
        await page.fill("input#i0118", password)
        await asyncio.sleep(1)
        await page.click("input#idSIButton9")
        await asyncio.sleep(3)

        # Verificar 2FA
        current_url = page.url
        if "login.microsoftonline.com" in current_url:
            # Clicar "Stay signed in?" se aparecer
            try:
                await page.click("input#idSIButton9", timeout=3000)
                await asyncio.sleep(2)
            except:
                pass
            
            if "login.microsoftonline.com" in page.url:
                success = await wait_for_2fa(page)
                if not success:
                    return False

        print("✅ Login concluído!\n")
        return True

    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return False


async def extract_course_info(page: Page, course_url: str, course_id: str):
    """Extrai informações de um curso específico."""
    print(f"📚 Acessando curso {course_id}...")
    
    try:
        await page.goto(course_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4)  # Aguardar carregamento
        
        # Extrair informações do curso
        course_data = await page.evaluate("""
            () => {
                const data = {
                    title: null,
                    code: null,
                    widgets: [],
                    links: [],
                    announcements: [],
                    content: null
                };
                
                // Título do curso
                const titleSelectors = [
                    'h1.d2l-page-title',
                    'h1[role="heading"]',
                    '.d2l-navigation-s-header-text',
                    'title'
                ];
                
                for (const selector of titleSelectors) {
                    const elem = document.querySelector(selector);
                    if (elem && elem.textContent.trim()) {
                        data.title = elem.textContent.trim();
                        break;
                    }
                }
                
                if (!data.title) {
                    data.title = document.title;
                }
                
                // Procurar código do curso (padrão: INFO-6154-(01)-25F)
                const codePattern = /\\b([A-Z]{3,5}-\\d{4}-\\(\\d{2}\\)-\\d{2}[A-Z])\\b/;
                const pageText = document.body.innerText;
                const codeMatch = pageText.match(codePattern);
                if (codeMatch) {
                    data.code = codeMatch[1];
                }
                
                // Widgets na página
                const widgets = document.querySelectorAll('.d2l-widget');
                widgets.forEach((widget, idx) => {
                    const heading = widget.querySelector('h2, h3, h4');
                    const widgetInfo = {
                        index: idx + 1,
                        title: heading ? heading.textContent.trim() : 'Sem título',
                        type: widget.className
                    };
                    data.widgets.push(widgetInfo);
                });
                
                // Links na página
                const links = document.querySelectorAll('a[href*="/d2l/"]');
                const linkSet = new Set();
                links.forEach(link => {
                    const href = link.href;
                    const text = link.textContent.trim();
                    if (href && text && href.includes('/d2l/')) {
                        linkSet.add(JSON.stringify({
                            text: text.substring(0, 100),
                            url: href
                        }));
                    }
                });
                
                data.links = Array.from(linkSet).map(item => JSON.parse(item)).slice(0, 50);
                
                // Procurar anúncios
                const announcementSelectors = [
                    '.d2l-htmlblock',
                    '[class*="announcement"]',
                    'd2l-html-block'
                ];
                
                for (const selector of announcementSelectors) {
                    const elems = document.querySelectorAll(selector);
                    elems.forEach((elem, idx) => {
                        if (idx < 5) {  // Máximo 5 anúncios
                            const text = elem.textContent.trim().substring(0, 200);
                            if (text.length > 20) {
                                data.announcements.push(text);
                            }
                        }
                    });
                    
                    if (data.announcements.length > 0) break;
                }
                
                // Conteúdo geral
                data.content = {
                    text_length: document.body.innerText.length,
                    total_links: document.querySelectorAll('a').length,
                    total_images: document.querySelectorAll('img').length
                };
                
                return data;
            }
        """)
        
        # Adicionar metadados
        course_data['course_id'] = course_id
        course_data['url'] = course_url
        course_data['extracted_at'] = datetime.now().isoformat()
        
        print(f"  ✅ Título: {course_data['title'][:60]}...")
        if course_data['code']:
            print(f"  ✅ Código: {course_data['code']}")
        print(f"  ✅ Widgets: {len(course_data['widgets'])}")
        print(f"  ✅ Links: {len(course_data['links'])}")
        print(f"  ✅ Anúncios: {len(course_data['announcements'])}")
        
        return course_data
        
    except Exception as e:
        print(f"  ❌ Erro ao extrair: {e}")
        return {
            'course_id': course_id,
            'url': course_url,
            'error': str(e),
            'extracted_at': datetime.now().isoformat()
        }


async def main():
    """Processa todos os cursos."""
    
    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")
    
    if not username or not password:
        print("❌ Configure D2L_USERNAME e D2L_PASSWORD no .env")
        return
    
    # Criar diretório de saída
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    print("╔" + "="*78 + "╗")
    print("║" + "  EXTRATOR DE INFORMAÇÕES DE CURSOS D2L  ".center(80) + "║")
    print("╚" + "="*78 + "╝\n")
    print(f"📊 Total de cursos: {len(COURSE_URLS)}")
    print(f"📁 Diretório: {OUTPUT_DIR}\n")
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'DNT': '1'
            }
        )
        
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Login uma vez
        login_success = await login_d2l(page, username, password)
        if not login_success:
            print("❌ Falha no login")
            await browser.close()
            return
        
        # Processar cada curso
        all_courses = []
        processed = 0
        failed = 0
        
        for idx, url in enumerate(COURSE_URLS, 1):
            course_id = url.split('/')[-1]
            
            print(f"\n[{idx}/{len(COURSE_URLS)}] " + "─"*70)
            
            course_data = await extract_course_info(page, url, course_id)
            all_courses.append(course_data)
            
            if 'error' not in course_data:
                processed += 1
                
                # Salvar arquivo individual
                filepath = os.path.join(OUTPUT_DIR, f"course_{course_id}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(course_data, f, indent=2, ensure_ascii=False)
                print(f"  💾 Salvo: course_{course_id}.json")
            else:
                failed += 1
            
            # Delay entre cursos
            if idx < len(COURSE_URLS):
                delay = random.uniform(*DELAY_BETWEEN_COURSES)
                print(f"  ⏳ Aguardando {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        # Salvar resumo geral
        summary = {
            'extracted_at': datetime.now().isoformat(),
            'total_courses': len(COURSE_URLS),
            'processed': processed,
            'failed': failed,
            'courses': all_courses
        }
        
        summary_path = os.path.join(OUTPUT_DIR, "courses_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*80)
        print("RESUMO FINAL")
        print("="*80)
        print(f"✅ Processados: {processed}/{len(COURSE_URLS)}")
        print(f"❌ Falharam: {failed}")
        print(f"📁 Diretório: {OUTPUT_DIR}")
        print(f"📄 Resumo: courses_summary.json")
        print("="*80 + "\n")
        
        await browser.close()


if __name__ == "__main__":
    print("\n")
    asyncio.run(main())
    print("✅ CONCLUÍDO!\n")
