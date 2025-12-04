#!/usr/bin/env python3
"""
Script de debug para inspecionar a página de login do D2L
Salva screenshot e HTML da página para análise
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


async def inspect_login_page():
    """Inspeciona a estrutura da página de login"""
    base_url = "https://www.fanshaweonline.ca"
    login_url = f"{base_url}/d2l/login"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Modo visível
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        print(f"[Debug] Navegando para: {login_url}")
        await page.goto(login_url, wait_until="networkidle", timeout=30000)

        print(f"[Debug] URL atual: {page.url}")

        # Aguardar um pouco para carregar completamente
        await asyncio.sleep(3)

        # Salvar screenshot
        screenshot_path = "login_page_debug.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"[Debug] Screenshot salvo: {screenshot_path}")

        # Salvar HTML completo
        html_content = await page.content()
        html_path = "login_page_debug.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[Debug] HTML salvo: {html_path}")

        # Tentar encontrar todos os campos de input
        print("\n[Debug] Procurando campos de input...")
        inputs = await page.query_selector_all("input")
        print(f"[Debug] Total de campos input encontrados: {len(inputs)}")

        for idx, input_elem in enumerate(inputs):
            input_type = await input_elem.get_attribute("type") or "text"
            input_name = await input_elem.get_attribute("name") or "N/A"
            input_id = await input_elem.get_attribute("id") or "N/A"
            input_placeholder = await input_elem.get_attribute("placeholder") or "N/A"

            print(f"\n  Input #{idx + 1}:")
            print(f"    Type: {input_type}")
            print(f"    Name: {input_name}")
            print(f"    ID: {input_id}")
            print(f"    Placeholder: {input_placeholder}")

        # Procurar botões
        print("\n[Debug] Procurando botões...")
        buttons = await page.query_selector_all("button, input[type='submit']")
        print(f"[Debug] Total de botões encontrados: {len(buttons)}")

        for idx, button in enumerate(buttons):
            button_type = await button.get_attribute("type") or "button"
            button_text = await button.text_content() or "N/A"
            button_id = await button.get_attribute("id") or "N/A"

            print(f"\n  Botão #{idx + 1}:")
            print(f"    Type: {button_type}")
            print(f"    Text: {button_text.strip()}")
            print(f"    ID: {button_id}")

        print("\n[Debug] Aguardando 10 segundos para você inspecionar a página...")
        print("[Debug] Pressione Ctrl+C para encerrar")

        try:
            await asyncio.sleep(10)
        except KeyboardInterrupt:
            pass

        await browser.close()

        print("\n[Debug] Análise completa!")
        print(f"[Debug] Verifique os arquivos:")
        print(f"  - {screenshot_path}")
        print(f"  - {html_path}")


if __name__ == "__main__":
    asyncio.run(inspect_login_page())
