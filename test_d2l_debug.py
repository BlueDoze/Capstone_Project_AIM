"""Quick debug script to inspect D2L page structure."""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv
import json

load_dotenv()

async def debug_d2l_page():
    """Inspect the D2L page to understand structure."""

    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        print("D2L credentials not found in .env")
        return

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
        )

        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        try:
            # Go to login
            print("Navigating to D2L...")
            await page.goto("https://www.fanshaweonline.ca/d2l/login", wait_until="domcontentloaded", timeout=30000)

            # Check if login page
            current_url = page.url
            print(f"Current URL: {current_url}")

            if "login" in current_url.lower():
                print("\nOn login page - authenticating...")

                # Fill email
                await page.wait_for_selector("input#i0116", timeout=10000)
                await page.fill("input#i0116", username)
                await asyncio.sleep(1)
                await page.click("input#idSIButton9")

                await page.wait_for_load_state("domcontentloaded", timeout=20000)
                await asyncio.sleep(2)

                # Fill password
                await page.wait_for_selector("input#i0118", timeout=10000)
                await page.fill("input#i0118", password)
                await asyncio.sleep(1)
                await page.click("input#idSIButton9")

                await asyncio.sleep(5)
                print(f"After login URL: {page.url}")

            # Navigate to home page
            print("\nNavigating to course home page...")
            home_url = "https://www.fanshaweonline.ca/d2l/home/2001539"
            await page.goto(home_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            print(f"Final URL: {page.url}")

            # Get page content
            page_content = await page.content()

            # Check for announcements in page
            if "Lab activity" in page_content:
                print("✓ Found 'Lab activity' in page content")
            if "Quiz" in page_content:
                print("✓ Found 'Quiz' in page content")
            if "Announcement" in page_content or "announcement" in page_content:
                print("✓ Found 'Announcement' in page content")

            # Try to find all clickable links
            print("\n=== INSPECTING PAGE STRUCTURE ===\n")

            page_info = await page.evaluate("""
                () => {
                    return {
                        title: document.title,
                        url: window.location.href,
                        body_text_length: document.body.innerText.length,
                        all_links_count: document.querySelectorAll('a').length,
                        d2l_links_count: document.querySelectorAll('a[href*="/d2l/"]').length,
                        headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.textContent.trim()).slice(0, 10),
                        links_sample: Array.from(document.querySelectorAll('a')).slice(0, 10).map(a => ({
                            text: a.textContent.trim().slice(0, 50),
                            href: a.href.slice(0, 100)
                        }))
                    };
                }
            """)

            print(f"Page Title: {page_info['title']}")
            print(f"Page URL: {page_info['url']}")
            print(f"Body Text Length: {page_info['body_text_length']}")
            print(f"Total Links: {page_info['all_links_count']}")
            print(f"D2L Links: {page_info['d2l_links_count']}")

            print("\nHeadings found:")
            for heading in page_info['headings']:
                print(f"  - {heading}")

            print("\nSample Links:")
            for link in page_info['links_sample']:
                print(f"  Text: {link['text']}")
                print(f"  URL: {link['href']}")
                print()

            # Try to find announcement-like content
            announcement_content = await page.evaluate("""
                () => {
                    // Look for any div or section with announcement-like content
                    const potentialAnnouncements = [];

                    document.querySelectorAll('[role="main"] *').forEach(el => {
                        const text = el.textContent;
                        if (text && (text.includes('Lab activity') || text.includes('Quiz') || text.includes('Dear students'))) {
                            potentialAnnouncements.push({
                                tag: el.tagName,
                                class: el.className,
                                text: text.slice(0, 100)
                            });
                        }
                    });

                    return potentialAnnouncements;
                }
            """)

            print("\n=== ANNOUNCEMENT-LIKE CONTENT ===\n")
            for item in announcement_content[:5]:
                print(f"Tag: {item['tag']}, Class: {item['class']}")
                print(f"Text: {item['text']}\n")

            # Save full page content for analysis
            with open('/tmp/d2l_page.html', 'w') as f:
                f.write(page_content)
            print("\nFull page saved to /tmp/d2l_page.html")

        except Exception as e:
            print(f"Error: {str(e)}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_d2l_page())
