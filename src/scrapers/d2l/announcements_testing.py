"""
Testing pipeline for D2L course announcements extraction.
Follows the restaurant scraper architecture for consistency.
Targets: https://www.fanshaweonline.ca/d2l/home/2001539
Extracts announcements from D2L course page with full content details.
"""

import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import re
import os
import random
from dotenv import load_dotenv

load_dotenv()


async def wait_for_2fa_approval(page, timeout=300000):
    """
    Wait for 2FA approval with automatic code detection and filling.

    Args:
        page: Playwright page object
        timeout: Timeout in milliseconds (default 5 minutes)

    Returns:
        bool: True if 2FA approved, False if timeout
    """
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " 🔐 TWO-FACTOR AUTHENTICATION REQUIRED ".center(78) + "║")
    print("╚" + "="*78 + "╝")
    print()

    try:
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Attempt to detect and extract verification code
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
            print("║" + f"  🔢 VERIFICATION CODE DETECTED: {verification_code}  ".center(78) + "║")
            print("╚" + "="*78 + "╝")
            print()

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
                        print(f"✅ Code input field found: {selector}")
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                        await page.fill(selector, verification_code)
                        print(f"✅ Code {verification_code} automatically filled!")
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
                                    print(f"✅ Verification button found, clicking...")
                                    await asyncio.sleep(random.uniform(0.5, 1.0))
                                    await verify_button.click()
                                    print(f"✅ Code submitted automatically!")
                                    code_filled = True
                                    break
                            except:
                                continue

                        if code_filled:
                            break

                    except:
                        continue

                if not code_filled:
                    print("⚠️  Could not automatically fill code.")
                    print(f"📱 Please manually enter: {verification_code}")

            except Exception as e:
                print(f"⚠️  Error auto-filling code: {str(e)[:100]}")
                print(f"📱 Please use Microsoft Authenticator app:")
                print(f"   - Enter code: {verification_code}")
                print(f"   - Or tap 'Approve'")

            print()
        else:
            print("📱 ACTION REQUIRED:")
            print("   1. Open Microsoft Authenticator app on your phone")
            print("   2. Look for approval notification")
            print("   3. Tap 'Approve' or enter code if prompted")
            print()

    except Exception as e:
        print("📱 ACTION REQUIRED:")
        print("   1. Open Microsoft Authenticator app on your phone")
        print("   2. Look for approval notification")
        print("   3. Tap 'Approve'")
        print()

    print("⏳ Waiting for approval...\n")

    start_url = page.url
    elapsed = 0
    dots = 0
    last_code_check = 0

    while elapsed < timeout:
        current_url = page.url

        if "login.microsoftonline.com" not in current_url and "fanshaweonline.ca" in current_url:
            print("\n✅ AUTHENTICATION APPROVED SUCCESSFULLY!\n")
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
                    print(f"\n   🔄 Code updated: {new_code}")
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
            print(f"\r   Waiting{loading_animation} ({elapsed_sec}s)", end="", flush=True)

        if elapsed % 30000 == 0 and elapsed > 0:
            code_reminder = f" - Code: {verification_code}" if verification_code else ""
            print(f"\n   💡 Reminder: Check phone{code_reminder} - {elapsed_sec}s elapsed")

    print("\n\n❌ TIMEOUT: Approval not detected after 5 minutes")
    print("   Please try again.\n")
    return False


async def try_login_if_needed(page):
    """
    Check if login is needed and perform authentication if required.
    Uses multiple selector strategies for robustness.

    Args:
        page: Playwright page object

    Returns:
        bool: True if logged in or already logged in, False otherwise
    """
    current_url = page.url

    # Check if already authenticated
    if "login" not in current_url.lower() and "microsoft" not in current_url.lower():
        return True

    print("\n[AUTH] Login required. Starting authentication...")

    username = os.getenv("D2L_USERNAME")
    password = os.getenv("D2L_PASSWORD")

    if not username or not password:
        raise ValueError("D2L_USERNAME and D2L_PASSWORD required in .env")

    # ============== EMAIL/USERNAME FIELD ==============
    print("  → Filling email...")

    # Wait for the page to fully load
    try:
        await page.wait_for_load_state("networkidle", timeout=20000)
    except:
        await asyncio.sleep(2)

    email_selectors = [
        "input#i0116",           # Microsoft Office 365 email
        "input[type='email']",   # Generic email type
        "input[name='loginfmt']", # Microsoft login format name
        "input[name='email']",   # Generic email name
        "input[placeholder*='email' i]", # Placeholder containing "email"
        "input[name='username']" # Generic username
    ]

    email_filled = False
    for selector in email_selectors:
        try:
            print(f"    Trying selector: {selector}")
            await page.wait_for_selector(selector, timeout=15000)
            print(f"    ✓ Found with selector: {selector}")
            await asyncio.sleep(random.uniform(0.5, 1.0))
            await page.fill(selector, username)
            print(f"    ✓ Email filled")
            await asyncio.sleep(random.uniform(0.8, 1.5))
            email_filled = True
            break
        except Exception as e:
            print(f"    ✗ Failed: {str(e)[:50]}")
            continue

    if not email_filled:
        # Save debug HTML for troubleshooting
        page_html = await page.content()
        debug_path = "/tmp/login_page_email_debug.html"
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(page_html)
        raise Exception(f"Could not find email input field after trying {len(email_selectors)} selectors. "
                       f"Debug HTML saved to {debug_path}")

    # ============== SUBMIT BUTTON AFTER EMAIL ==============
    print("  → Clicking submit button for email...")
    submit_buttons = [
        "input#idSIButton9",           # Microsoft submit button
        "button[type='submit']",       # Generic submit button
        "input[type='submit']",        # Input submit
        "input[value*='Next']",        # Button with "Next" text
        "button[value*='Next']"
    ]

    email_submitted = False
    for selector in submit_buttons:
        try:
            button = await page.query_selector(selector)
            if button:
                print(f"    ✓ Found submit button: {selector}")
                await asyncio.sleep(random.uniform(0.5, 1.0))
                await button.click()
                print(f"    ✓ Email submitted")
                await asyncio.sleep(2)
                email_submitted = True
                break
        except Exception as e:
            print(f"    ✗ Failed: {str(e)[:50]}")
            continue

    if not email_submitted:
        raise Exception(f"Could not click submit button after entering email")

    # Wait for page to load after email submission
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=15000)
    except:
        await asyncio.sleep(3)

    await asyncio.sleep(random.uniform(1.5, 2.5))

    # ============== PASSWORD FIELD ==============
    print("  → Filling password...")
    password_selectors = [
        "input#i0118",           # Microsoft Office 365 password
        "input[type='password']", # Generic password type
        "input[name='passwd']",   # Microsoft password name
        "input[name='password']", # Generic password name
        "input[aria-label*='password' i]" # Aria label with password
    ]

    password_filled = False
    for selector in password_selectors:
        try:
            print(f"    Trying selector: {selector}")
            await page.wait_for_selector(selector, timeout=15000)
            print(f"    ✓ Found with selector: {selector}")
            await asyncio.sleep(random.uniform(0.5, 1.0))
            await page.fill(selector, password)
            print(f"    ✓ Password filled")
            await asyncio.sleep(random.uniform(0.8, 1.5))
            password_filled = True
            break
        except Exception as e:
            print(f"    ✗ Failed: {str(e)[:50]}")
            continue

    if not password_filled:
        # Save debug HTML for troubleshooting
        page_html = await page.content()
        debug_path = "/tmp/login_page_password_debug.html"
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(page_html)
        raise Exception(f"Could not find password input field after trying {len(password_selectors)} selectors. "
                       f"Debug HTML saved to {debug_path}")

    # ============== SUBMIT BUTTON AFTER PASSWORD ==============
    print("  → Clicking submit button for password...")
    for selector in submit_buttons:
        try:
            button = await page.query_selector(selector)
            if button:
                print(f"    ✓ Found submit button: {selector}")
                await asyncio.sleep(random.uniform(0.5, 1.0))
                await button.click()
                print(f"    ✓ Password submitted")
                await asyncio.sleep(3)
                break
        except Exception as e:
            print(f"    ✗ Failed: {str(e)[:50]}")
            continue

    # Wait for page load
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=15000)
    except:
        await asyncio.sleep(3)

    current_url = page.url

    # ============== HANDLE "STAY SIGNED IN" PROMPT ==============
    if "login.microsoftonline.com" in current_url or "Stay signed in" in await page.content():
        try:
            stay_button = await page.query_selector("input#idSIButton9")
            if stay_button:
                button_value = await stay_button.get_attribute("value")
                if button_value and ("Yes" in button_value or "No" in button_value):
                    print("  → Clicking 'Yes' on Stay signed in...")
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    await stay_button.click()
                    await asyncio.sleep(2)
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=15000)
                    except:
                        await asyncio.sleep(2)
                    await asyncio.sleep(random.uniform(1.5, 2.5))
        except Exception as e:
            print(f"  ⚠ Could not handle 'Stay signed in': {str(e)[:50]}")

    current_url = page.url

    # ============== HANDLE 2FA IF NEEDED ==============
    if "login.microsoftonline.com" in current_url:
        print("  → 2FA authentication required...")
        success = await wait_for_2fa_approval(page, timeout=300000)
        if not success:
            raise Exception("2FA approval failed or timed out")

    print("✓ Login completed!\n")
    return True


async def fetch_announcement_details(page, announcement_url: str) -> Dict:
    """
    Fetch and parse an individual announcement page.

    Args:
        page: Playwright page object
        announcement_url: URL of the announcement

    Returns:
        Dictionary with announcement details
    """
    info = {
        "url": announcement_url,
        "accessible": False,
        "title": None,
        "date": None,
        "author": None,
        "content": None,
        "content_length": 0,
        "has_attachments": False,
        "raw_content_preview": ""
    }

    try:
        await page.goto(announcement_url, wait_until="domcontentloaded", timeout=30000)
        info["accessible"] = True

        # Extract announcement title
        title = await page.evaluate("""
            () => {
                const titleSelectors = [
                    'h1',
                    'h2',
                    '[role="heading"]',
                    '.d2l-page-title',
                    '.d2l-heading-standard'
                ];

                for (const selector of titleSelectors) {
                    const elem = document.querySelector(selector);
                    if (elem) {
                        return elem.innerText.trim();
                    }
                }
                return null;
            }
        """)

        info["title"] = title

        # Extract announcement content (HTML block)
        content = await page.evaluate("""
            () => {
                // Try to find d2l-html-block with html attribute
                const htmlBlock = document.querySelector('d2l-html-block');
                if (htmlBlock) {
                    const htmlAttr = htmlBlock.getAttribute('html');
                    if (htmlAttr) {
                        const temp = document.createElement('div');
                        temp.innerHTML = htmlAttr;
                        return temp.innerText.trim();
                    }
                }

                // Fallback: try to get main content area
                const mainContent = document.querySelector('[role="main"]');
                if (mainContent) {
                    return mainContent.innerText.trim();
                }

                // Final fallback: get body text
                return document.body.innerText.trim();
            }
        """)

        if content:
            info["content"] = content
            info["content_length"] = len(content)
            info["raw_content_preview"] = content[:300] if len(content) > 300 else content

        # Try to extract date and author
        metadata = await page.evaluate("""
            () => {
                const metaInfo = {};

                // Look for date patterns
                const dateSelectors = [
                    '[data-date]',
                    '.d2l-date',
                    '.d2l-published-date',
                    'time'
                ];

                for (const selector of dateSelectors) {
                    const elem = document.querySelector(selector);
                    if (elem) {
                        const dateAttr = elem.getAttribute('data-date') ||
                                        elem.getAttribute('datetime') ||
                                        elem.innerText;
                        if (dateAttr) {
                            metaInfo.date = dateAttr.trim();
                            break;
                        }
                    }
                }

                // Look for author
                const authorSelectors = [
                    '[data-author]',
                    '.d2l-author',
                    '.d2l-published-by'
                ];

                for (const selector of authorSelectors) {
                    const elem = document.querySelector(selector);
                    if (elem) {
                        const authorAttr = elem.getAttribute('data-author') || elem.innerText;
                        if (authorAttr) {
                            metaInfo.author = authorAttr.trim();
                            break;
                        }
                    }
                }

                return metaInfo;
            }
        """)

        if metadata.get("date"):
            info["date"] = metadata["date"]
        if metadata.get("author"):
            info["author"] = metadata["author"]

        # Check for attachments
        has_attachments = await page.evaluate("""
            () => {
                const attachmentSelectors = [
                    '.d2l-file-attachment',
                    '[role="link"][href*="download"]',
                    '.d2l-attachment'
                ];

                for (const selector of attachmentSelectors) {
                    if (document.querySelector(selector)) {
                        return true;
                    }
                }
                return false;
            }
        """)

        info["has_attachments"] = has_attachments

    except Exception as e:
        info["error"] = str(e)

    return info


async def extract_announcements_from_home_page(page) -> List[Dict]:
    """
    Extract announcements list from D2L course home page.

    Args:
        page: Playwright page object

    Returns:
        List of announcement dictionaries with title, date, and url
    """
    announcements = []

    try:
        # Extract announcements from the page
        announcements_data = await page.evaluate("""
            () => {
                const announcements = [];

                // Strategy 1: Look for announcement links in tables
                const tableLinks = document.querySelectorAll('a.d2l-link-inline');
                tableLinks.forEach(link => {
                    const title = link.textContent.trim();
                    const url = link.href;

                    if (title && url && (url.includes('/d2l/le/news/') || url.includes('/d2l/lms/news/'))) {
                        // Try to get date from nearby cells
                        const row = link.closest('tr');
                        let date = '';
                        if (row) {
                            const cells = row.querySelectorAll('td, th');
                            if (cells.length >= 2) {
                                date = cells[cells.length - 1].textContent.trim();
                            }
                        }

                        announcements.push({
                            title: title,
                            date: date || null,
                            url: url
                        });
                    }
                });

                // Strategy 2: Look for announcement section with main content
                if (announcements.length === 0) {
                    // Look for section containing "Announcements" header
                    const announcementsSections = document.querySelectorAll('[role="main"] h2, [role="main"] h3, main h2, main h3');

                    announcementsSections.forEach(heading => {
                        if (heading.textContent.toLowerCase().includes('announcement')) {
                            // Find parent container
                            let container = heading.closest('section') || heading.closest('div[role="region"]') || heading.parentElement;
                            if (container) {
                                const links = container.querySelectorAll('a');
                                links.forEach(link => {
                                    const title = link.textContent.trim();
                                    const url = link.href;

                                    if (title && url && url.length > 10 &&
                                        (url.includes('/d2l/') || url.includes('fanshaweonline'))) {
                                        // Check if not a navigation link
                                        if (!title.toLowerCase().includes('back') &&
                                            !title.toLowerCase().includes('menu') &&
                                            !url.includes('javascript')) {

                                            // Try to find date near this link
                                            const dateElem = link.closest('div, li, article')?.querySelector('time, [class*="date"], [class*="posted"]');
                                            const date = dateElem ? dateElem.textContent.trim() : null;

                                            announcements.push({
                                                title: title,
                                                date: date,
                                                url: url
                                            });
                                        }
                                    }
                                });
                            }
                        }
                    });
                }

                // Strategy 3: Look for announcement cards (general fallback)
                if (announcements.length === 0) {
                    const cards = document.querySelectorAll('[data-type="announcement"], .d2l-announcement-card, article, .d2l-newsitem');
                    cards.forEach(card => {
                        const linkElem = card.querySelector('a:not([class*="close"])');
                        if (linkElem) {
                            const title = linkElem.textContent.trim();
                            const url = linkElem.href;

                            if (title && url && (url.includes('/d2l/') || url.includes('fanshaweonline'))) {
                                announcements.push({
                                    title: title,
                                    date: null,
                                    url: url
                                });
                            }
                        }
                    });
                }

                return announcements;
            }
        """)

        announcements = announcements_data

    except Exception as e:
        print(f"  ⚠ Error extracting announcements from home page: {str(e)[:100]}")

    return announcements


async def extract_d2l_announcements_testing(course_id: str = "2001539",
                                           output_file: Optional[Path] = None,
                                           debug: bool = False) -> Dict:
    """
    Main D2L announcements extraction pipeline.

    Args:
        course_id: D2L course ID (default: 2001539 - INFO-6153)
        output_file: Path to save output JSON (default: timestamped in data/course_2001539/)
        debug: Enable debug output

    Returns:
        Dictionary with extracted announcements data
    """

    # Determine output file
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path('data/course_2001539')
        output_file = output_dir / f'announcements_testing_{timestamp}.json'
    else:
        output_file = Path(output_file)

    print(f"\n{'='*80}")
    print("D2L ANNOUNCEMENTS TESTING PIPELINE")
    print(f"{'='*80}")
    print(f"\nCourse ID: {course_id}")
    print(f"Target URL: https://www.fanshaweonline.ca/d2l/home/{course_id}")
    print(f"Output file: {output_file}\n")

    # Launch browser
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
        )

        # Block unnecessary resources
        await context.route("**/*", lambda route: route.abort()
            if route.request.resource_type in ["image", "font", "media", "stylesheet"]
            else route.continue_())

        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        extracted_data = {
            "metadata": {
                "source": "d2l_announcements_testing",
                "generated_at": datetime.now().isoformat(),
                "course_id": course_id,
                "home_url": f"https://www.fanshaweonline.ca/d2l/home/{course_id}",
                "total_announcements_found": 0,
                "total_detailed": 0,
                "successful_details": 0,
                "failed_details": 0
            },
            "announcements_list": [],
            "announcements_detailed": []
        }

        try:
            # Step 1: Go to announcements page directly
            print("[1/4] Accessing D2L course announcements page...")
            # Try announcements page directly first (most reliable)
            announcements_url = f"https://www.fanshaweonline.ca/d2l/lms/news/main.d2l?ou={course_id}"
            await page.goto(announcements_url, wait_until="domcontentloaded", timeout=30000)

            # Check if login is needed
            current_url = page.url
            if "login" in current_url.lower() or "saml" in current_url.lower():
                print("[AUTH] Authentication required, logging in...")
                await try_login_if_needed(page)
                # Wait for redirect and 2FA if needed
                await asyncio.sleep(5)
                # Try announcements page again after login
                await page.goto(announcements_url, wait_until="domcontentloaded", timeout=30000)

            # Fallback to home page if announcements page doesn't work
            current_url = page.url
            if "login" in current_url.lower():
                print("[AUTH] Still on login - trying home page...")
                home_url = f"https://www.fanshaweonline.ca/d2l/home/{course_id}"
                await page.goto(home_url, wait_until="domcontentloaded", timeout=30000)

            await asyncio.sleep(random.uniform(1.5, 2.5))
            print("✓ Home page loaded!\n")

            # Step 2: Extract announcements from home page
            print("[2/4] Extracting announcements from home page...")

            # Also try to extract ALL links for fallback
            all_links_data = await page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href*="/d2l/"]').forEach(link => {
                        links.push({
                            text: link.textContent.trim(),
                            href: link.href,
                            parent: link.parentElement?.tagName
                        });
                    });
                    return links;
                }
            """)

            announcements_list = await extract_announcements_from_home_page(page)

            # If no announcements found, try extracting from all links that look like announcements
            if len(announcements_list) == 0 and all_links_data:
                print("  → Trying alternative extraction from all page links...")
                for link_data in all_links_data:
                    text = link_data['text']
                    href = link_data['href']

                    # Filter out navigation and other non-announcement links
                    if (text and href and
                        len(text) > 5 and
                        not any(x in text.lower() for x in ['home', 'menu', 'back', 'log out', 'help', 'profile', 'settings', 'announcements', 'communications', 'evaluations']) and
                        not any(x in href for x in ['profile', 'settings', 'help', 'menu', 'communicate'])):

                        # Check if it might be an announcement
                        if '/d2l/' in href:
                            announcements_list.append({
                                'title': text,
                                'date': None,
                                'url': href
                            })

            extracted_data["metadata"]["total_announcements_found"] = len(announcements_list)

            if announcements_list:
                print(f"✓ Found {len(announcements_list)} announcements!\n")
                extracted_data["announcements_list"] = announcements_list
            else:
                print("⚠ No announcements found on home page.\n")

            # Step 3: Extract details from each announcement
            if announcements_list:
                print(f"[3/4] Extracting details from {min(len(announcements_list), 10)} announcements...")
                announcements_to_detail = announcements_list[:10]  # Limit to first 10

                for idx, announcement in enumerate(announcements_to_detail, 1):
                    try:
                        print(f"\n[{idx}/{len(announcements_to_detail)}] {announcement['title'][:70]}")
                        print(f"  → URL: {announcement['url'][:60]}...")

                        # Fetch details
                        details = await fetch_announcement_details(page, announcement['url'])

                        # Combine with list data
                        combined = {
                            "index": idx,
                            "title": announcement['title'],
                            "date": announcement.get('date'),
                            "url": announcement['url'],
                            "details": details
                        }

                        extracted_data["announcements_detailed"].append(combined)

                        if details["accessible"]:
                            print(f"  ✓ Accessible - {details['content_length']} chars")
                            extracted_data["metadata"]["successful_details"] += 1
                        else:
                            print(f"  ⚠ Not accessible: {details.get('error', 'Unknown error')}")
                            extracted_data["metadata"]["failed_details"] += 1

                        await asyncio.sleep(random.uniform(1.0, 2.0))

                    except Exception as e:
                        print(f"  ❌ Error: {str(e)[:100]}")
                        extracted_data["metadata"]["failed_details"] += 1
                        extracted_data["announcements_detailed"].append({
                            "index": idx,
                            "title": announcement['title'],
                            "url": announcement['url'],
                            "error": str(e)
                        })

                extracted_data["metadata"]["total_detailed"] = len(extracted_data["announcements_detailed"])
                print(f"\n✓ Details extraction complete!\n")

            # Step 4: Save results
            print(f"[4/4] Saving results...")
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)

            print(f"\n{'='*80}")
            print("EXTRACTION COMPLETE")
            print(f"{'='*80}")
            print(f"Output file: {output_file}")
            print(f"Announcements found: {extracted_data['metadata']['total_announcements_found']}")
            print(f"Details extracted: {extracted_data['metadata']['total_detailed']}")
            print(f"Successful: {extracted_data['metadata']['successful_details']}")
            print(f"Failed: {extracted_data['metadata']['failed_details']}")
            print(f"{'='*80}\n")

            return extracted_data

        except Exception as e:
            print(f"\n✗ FATAL ERROR: {str(e)}")

            # Save partial results
            if extracted_data["announcements_list"] or extracted_data["announcements_detailed"]:
                extracted_data["metadata"]["error"] = str(e)
                extracted_data["metadata"]["partial"] = True

                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(extracted_data, f, indent=2, ensure_ascii=False)

                print(f"✓ Partial results saved to: {output_file}")

            raise

        finally:
            await browser.close()


async def main():
    parser = argparse.ArgumentParser(
        description='D2L announcements testing pipeline - extract course announcements with details'
    )
    parser.add_argument(
        '--course-id',
        type=str,
        default='2001539',
        help='D2L course ID (default: 2001539 - INFO-6153)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: timestamped in data/course_2001539/)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    args = parser.parse_args()

    # Run extraction
    await extract_d2l_announcements_testing(
        course_id=args.course_id,
        output_file=Path(args.output) if args.output else None,
        debug=args.debug
    )


if __name__ == "__main__":
    asyncio.run(main())
