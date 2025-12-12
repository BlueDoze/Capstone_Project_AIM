"""
Multi-Course D2L Announcements Scraper
Extracts announcements from multiple D2L courses in a single run
Courses: 2001539, 2001540, 2001541, 2001542, 2001538, 2014765
"""

import asyncio
import os
import sys
import json
import random
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

def load_course_ids_from_file():
    """Load course IDs from data/courses.txt"""
    courses_file = project_root / 'data' / 'courses.txt'
    if courses_file.exists():
        with open(courses_file, 'r') as f:
            content = f.read().strip()
            # Parse comma-separated course IDs
            course_ids = [cid.strip() for cid in content.split(',') if cid.strip()]
            return course_ids
    return []

# Course IDs to scrape - load from file or use defaults
COURSE_IDS = load_course_ids_from_file() or [
    "2001539",
    "2001540",
    "2001541",
    "2001542",
    "2001538",
    "2014765",
]


async def wait_for_2fa_approval(page, timeout=300000):
    """Wait for 2FA approval"""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " 🔐 TWO-FACTOR AUTHENTICATION REQUIRED ".center(78) + "║")
    print("╚" + "="*78 + "╝")
    print()

    verification_code = None
    try:
        await asyncio.sleep(random.uniform(1.0, 2.0))

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
            print("║" + f"  🔢 VERIFICATION CODE: {verification_code}  ".center(78) + "║")
            print("╚" + "="*78 + "╝")
            print()

            try:
                code_input_selectors = [
                    'input[name="otc"]',
                    'input[type="tel"]',
                    '#idTxtBx_SAOTCC_OTC'
                ]

                for selector in code_input_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                        await page.fill(selector, verification_code)
                        print(f"✅ Code {verification_code} entered!")
                        await asyncio.sleep(random.uniform(0.5, 1.0))

                        verify_button = await page.query_selector('input[type="submit"]')
                        if verify_button:
                            await verify_button.click()
                            print(f"✅ Code submitted!")
                        break
                    except:
                        continue

            except Exception as e:
                print(f"📱 Please enter code manually: {verification_code}")
        else:
            print("📱 Please approve on Microsoft Authenticator app")

    except:
        print("📱 Please approve on Microsoft Authenticator app")

    print("⏳ Waiting for approval...\n")

    elapsed = 0
    dots = 0

    while elapsed < timeout:
        current_url = page.url

        if "login.microsoftonline.com" not in current_url and "fanshaweonline.ca" in current_url:
            print("\n✅ AUTHENTICATION APPROVED!\n")
            return True

        await asyncio.sleep(2)
        elapsed += 2000

        dots = (dots + 1) % 4
        loading = "." * dots + " " * (3 - dots)
        print(f"\r   Waiting{loading} ({elapsed // 1000}s)", end="", flush=True)

    print("\n\n❌ TIMEOUT: Approval not detected")
    return False


async def perform_login(page, username, password):
    """Perform D2L login"""
    print("\n[LOGIN] Starting login...")
    login_url = "https://www.fanshaweonline.ca/d2l/login"
    await page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(random.uniform(2.0, 3.5))

    print("  → Entering email...")
    await page.wait_for_selector("input#i0116", timeout=10000)
    await page.fill("input#i0116", username)
    await asyncio.sleep(random.uniform(0.8, 1.5))
    await page.click("input#idSIButton9")

    await page.wait_for_load_state("domcontentloaded", timeout=20000)
    await asyncio.sleep(random.uniform(1.5, 2.5))

    print("  → Entering password...")
    await page.wait_for_selector("input#i0118", timeout=10000)
    await page.fill("input#i0118", password)
    await asyncio.sleep(random.uniform(0.8, 1.5))
    await page.click("input#idSIButton9")

    await asyncio.sleep(3)

    print("  → Checking for 2FA...")
    await asyncio.sleep(2)
    current_url = page.url

    if "login.microsoftonline.com" in current_url or "Stay signed in" in await page.content():
        try:
            stay_button = await page.query_selector("input#idSIButton9")
            if stay_button:
                button_value = await stay_button.get_attribute("value")
                if button_value and ("Yes" in button_value or "No" in button_value):
                    print("  → Clicking 'Yes' on Stay signed in...")
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    await stay_button.click()
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                    await asyncio.sleep(random.uniform(1.5, 2.5))
        except:
            pass

        current_url = page.url
        if "login.microsoftonline.com" in current_url:
            success = await wait_for_2fa_approval(page, timeout=300000)
            if not success:
                raise Exception("2FA approval failed")

    await asyncio.sleep(2)
    print(f"\n✓ Login completed!\n")
    return True


async def scrape_course_announcements(page, course_id, news_url):
    """Extract announcements from a specific course"""
    all_announcements = []
    
    try:
        print(f"→ Accessing announcements page for course {course_id}...")
        await page.goto(news_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(random.uniform(2.0, 3.5))
        print("✓ Page loaded!\n")

        print("→ Extracting announcements list...")
        announcements_list = await page.evaluate("""
            () => {
                const announcements = [];
                const links = document.querySelectorAll('a.d2l-link-inline');

                links.forEach((link, idx) => {
                    const title = link.textContent.trim();
                    const url = link.href;

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

        print(f"✓ Found {len(announcements_list)} announcements!\n")

        if len(announcements_list) == 0:
            print("⚠️ No announcements found for this course.\n")
            return []

        print(f"Extracting content from {len(announcements_list)} announcements...")

        for idx, announcement in enumerate(announcements_list, 1):
            try:
                progress = int((idx / len(announcements_list)) * 40)
                bar = "█" * progress + "░" * (40 - progress)
                percentage = int((idx / len(announcements_list)) * 100)

                print(f"\n[{idx}/{len(announcements_list)}] {bar} {percentage}%")
                print(f"📄 {announcement['title'][:60]}")

                await page.goto(announcement['url'], wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(1.0, 2.0))

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

                        const main = document.querySelector('[role="main"]');
                        if (main) {
                            return main.innerText.trim();
                        }

                        return '';
                    }
                """)

                content = content.strip() if content else ""
                content = '\n'.join(line.strip() for line in content.split('\n') if line.strip())

                result = {
                    "index": idx,
                    "title": announcement['title'],
                    "date": announcement['date'],
                    "url": announcement['url'],
                    "content": content,
                    "content_length": len(content)
                }
                all_announcements.append(result)

                print(f"   ✅ OK ({len(content)} chars)")

                await page.go_back()
                await asyncio.sleep(random.uniform(0.8, 1.5))

            except Exception as e:
                print(f"   ❌ Error: {str(e)[:80]}")
                result = {
                    "index": idx,
                    "title": announcement['title'],
                    "date": announcement['date'],
                    "url": announcement['url'],
                    "content": f"ERROR: {str(e)}",
                    "error": True
                }
                all_announcements.append(result)

                try:
                    await page.goto(news_url, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                except:
                    pass

        return all_announcements

    except Exception as e:
        print(f"\n✗ ERROR processing course {course_id}: {str(e)}\n")
        return []


async def extract_multi_course_announcements(course_ids=None):
    """Extract announcements from multiple courses"""
    
    if course_ids is None:
        course_ids = COURSE_IDS

    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("Configure D2L_USERNAME and D2L_PASSWORD in .env")

    async with async_playwright() as p:
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

        await context.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font", "media"] else route.continue_())

        page = await context.new_page()

        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        results = {}

        try:
            print("\n")
            print("╔" + "="*78 + "╗")
            print("║" + " "*78 + "║")
            print("║" + "  D2L MULTI-COURSE ANNOUNCEMENTS EXTRACTOR".center(78) + "║")
            print("║" + f"  Total courses: {len(course_ids)}".center(78) + "║")
            print("║" + " "*78 + "║")
            print("╚" + "="*78 + "╝")
            print("\n")

            # Login once for all courses
            await perform_login(page, username, password)

            # Extract announcements from each course
            for idx, course_id in enumerate(course_ids, 1):
                print(f"\n{'#'*80}")
                print(f"# COURSE {idx}/{len(course_ids)}: {course_id}")
                print(f"{'#'*80}\n")
                
                news_url = f"https://www.fanshaweonline.ca/d2l/lms/news/main.d2l?ou={course_id}"
                
                announcements = await scrape_course_announcements(page, course_id, news_url)
                
                course_data = {
                    "course_id": course_id,
                    "course_url": news_url,
                    "total_announcements": len(announcements),
                    "successful": sum(1 for a in announcements if 'error' not in a),
                    "failed": sum(1 for a in announcements if 'error' in a),
                    "extracted_at": datetime.now().isoformat(),
                    "announcements": announcements
                }
                
                results[course_id] = course_data

                # Save individual course file
                output_dir = project_root / 'src' / 'data' / 'announcements'
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f'course_{course_id}_announcements.json'
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(course_data, f, indent=2, ensure_ascii=False)

                print(f"\n✓ Saved: {output_path}")
                print(f"✓ Total: {course_data['total_announcements']} announcements")
                print(f"✓ Success: {course_data['successful']}")
                print(f"✓ Failed: {course_data['failed']}")

                # Pause between courses
                if idx < len(course_ids):
                    await asyncio.sleep(random.uniform(2.0, 4.0))

            # Save summary file
            summary = {
                "extracted_at": datetime.now().isoformat(),
                "total_courses": len(course_ids),
                "courses_processed": len(results),
                "course_ids": course_ids,
                "summary": {
                    course_id: {
                        "total": data['total_announcements'],
                        "successful": data['successful'],
                        "failed": data['failed']
                    }
                    for course_id, data in results.items()
                }
            }

            summary_path = output_dir / 'all_courses_summary.json'
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            print(f"\n{'='*80}")
            print("SUMMARY")
            print(f"{'='*80}")
            print(f"✓ Summary saved: {summary_path}")
            print(f"✓ Total courses processed: {len(results)}")
            
            total_announcements = sum(c['total_announcements'] for c in results.values())
            total_successful = sum(c['successful'] for c in results.values())
            total_failed = sum(c['failed'] for c in results.values())
            
            print(f"✓ Total announcements: {total_announcements}")
            print(f"✓ Successful: {total_successful}")
            print(f"✓ Failed: {total_failed}")

            return summary

        except Exception as e:
            print(f"\n✗ FATAL ERROR: {str(e)}")
            raise

        finally:
            await browser.close()


if __name__ == "__main__":
    import sys
    
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  D2L MULTI-COURSE ANNOUNCEMENTS EXTRACTOR".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print("\n")

    # Allow passing course IDs as arguments
    if len(sys.argv) > 1:
        course_ids = sys.argv[1:]
        print(f"Processing custom courses: {', '.join(course_ids)}")
    else:
        course_ids = COURSE_IDS
        print(f"Processing default courses: {', '.join(course_ids)}")

    result = asyncio.run(extract_multi_course_announcements(course_ids))

    print("\n" + "="*80)
    print("COMPLETED SUCCESSFULLY!")
    print("="*80)
    print(f"Courses processed: {result['courses_processed']}/{result['total_courses']}")
    print("="*80 + "\n")
    # Aggregate all announcements into one file
    try:
        from .aggregate_announcements import aggregate_announcements
    except ImportError:
        # For direct script execution, fallback to relative import
        import importlib.util, os
        script_path = os.path.join(os.path.dirname(__file__), 'aggregate_announcements.py')
        spec = importlib.util.spec_from_file_location("aggregate_announcements", script_path)
        agg_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agg_mod)
        agg_mod.aggregate_announcements()
    else:
        aggregate_announcements()
    print("All course announcements aggregated into all_courses_announcements.json.")
