"""
Script para extrair informações de restaurantes do site Fanshawe.
Endpoint: https://www.fanshawec.ca/students/life/campus-services/food
"""

import asyncio
import os
import json
import random
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()

MAX_RESTAURANTS_LIMIT = 100


async def extract_restaurant_data(page):
    """
    Extract restaurant information using JavaScript evaluation with multiple strategies.

    Returns:
        dict: Contains 'restaurants' list and 'extraction_method' string
    """

    restaurants_data = await page.evaluate(f"""
        () => {{
            const MAX_RESTAURANTS = {MAX_RESTAURANTS_LIMIT};
            const restaurants = [];
            let extractionMethod = null;

            // Strategy 1: H2 and H3 tags with sibling content (primary)
            try {{
                const headings = document.querySelectorAll('h2, h3');
                if (headings.length > 0) {{
                    extractionMethod = 'heading_parsing';
                    const seen = new Set();

                    headings.forEach((heading, idx) => {{
                        if (restaurants.length >= MAX_RESTAURANTS) return;

                        const name = heading.textContent.trim();
                        if (!name || name.length < 2 || seen.has(name.toLowerCase())) return;

                        // Skip section headers
                        if (name.toLowerCase().includes('where to eat') ||
                            name.toLowerCase().includes('regional') ||
                            name.toLowerCase().includes('meal plan')) {{
                            return;
                        }}

                        seen.add(name.toLowerCase());

                        // Get description from following siblings (p tags)
                        let description = '';
                        let nextElement = heading.nextElementSibling;
                        let iterations = 0;

                        while (nextElement && iterations < 5) {{
                            if (nextElement.tagName === 'P') {{
                                const pText = nextElement.textContent.trim();
                                if (pText && pText.length > 5) {{
                                    description += pText + ' ';
                                }}
                            }} else if (nextElement.tagName.match(/H[2-4]/)) {{
                                break; // Stop at next heading
                            }}
                            nextElement = nextElement.nextElementSibling;
                            iterations++;
                        }}

                        // Look for links in the next 3 siblings
                        let link = '';
                        let sibling = heading.nextElementSibling;
                        for (let i = 0; i < 5 && sibling; i++) {{
                            const links = sibling.querySelectorAll('a[href*="fsu.ca"], a[href*="fanshawe"], a[href*=".ca"]');
                            if (links.length > 0) {{
                                link = links[0].href;
                                break;
                            }}
                            sibling = sibling.nextElementSibling;
                        }}

                        // Try to extract location from description
                        let location = '';
                        const locationPatterns = [
                            /(?:Building|Bldg)\\s+([A-Z])/i,
                            /([A-Z]-[A-Z]-[A-Z])/,
                            /(?:located in|at|in)\\s+([^,;.]+)/i
                        ];

                        for (const pattern of locationPatterns) {{
                            const match = description.match(pattern);
                            if (match) {{
                                location = match[1];
                                break;
                            }}
                        }}

                        restaurants.push({{
                            name: name,
                            description: description.trim(),
                            location: location,
                            link: link
                        }});
                    }});
                }}
            }} catch (e) {{
                console.log('Strategy 1 failed:', e);
            }}

            // Strategy 2: Keyword search for known restaurant names
            if (restaurants.length < 5) {{
                try {{
                    extractionMethod = 'keyword_search';
                    const knownNames = [
                        'Tim Hortons', 'Starbucks', 'Subway', 'Oasis', 'Booster Juice',
                        'Pizza Pizza', 'Harveys', 'The Chef\\'s Table', 'The Spoke',
                        'The Market', 'Food Court', 'Cafeteria'
                    ];

                    const pageText = document.body.innerText;
                    const seen = new Set();

                    knownNames.forEach((name) => {{
                        if (restaurants.length >= MAX_RESTAURANTS) return;
                        if (seen.has(name.toLowerCase())) return;

                        // Find position of name in page
                        const nameIndex = pageText.indexOf(name);
                        if (nameIndex !== -1) {{
                            seen.add(name.toLowerCase());
                            // Extract surrounding text as description
                            const startIdx = Math.max(0, nameIndex + name.length);
                            const description = pageText.substring(startIdx, startIdx + 300).trim();

                            restaurants.push({{
                                name: name,
                                description: description.split('\\n')[0],
                                location: '',
                                link: ''
                            }});
                        }}
                    }});
                }} catch (e) {{
                    console.log('Strategy 2 failed:', e);
                }}
            }}

            // Strategy 3: Look for divs with specific patterns
            if (restaurants.length === 0) {{
                try {{
                    extractionMethod = 'div_parsing';
                    const contentDivs = document.querySelectorAll('div[class*="content"], div[class*="item"], div[class*="card"]');

                    contentDivs.forEach((div, idx) => {{
                        if (idx >= MAX_RESTAURANTS) return;

                        const heading = div.querySelector('h2, h3, h4, strong');
                        if (heading) {{
                            const name = heading.textContent.trim();
                            const description = div.textContent.trim().substring(0, 300);

                            if (name && name.length > 2) {{
                                restaurants.push({{
                                    name: name,
                                    description: description,
                                    location: '',
                                    link: ''
                                }});
                            }}
                        }}
                    }});
                }} catch (e) {{
                    console.log('Strategy 3 failed:', e);
                }}
            }}

            // Remove duplicates by name
            const uniqueRestaurants = [];
            const seenNames = new Set();

            restaurants.forEach(rest => {{
                const nameLower = rest.name.toLowerCase();
                if (!seenNames.has(nameLower)) {{
                    seenNames.add(nameLower);
                    uniqueRestaurants.push(rest);
                }}
            }});

            return {{
                restaurants: uniqueRestaurants.slice(0, MAX_RESTAURANTS),
                extractionMethod: extractionMethod,
                totalFound: restaurants.length
            }};
        }}
    """)

    return restaurants_data


def fuzzy_match(str1, str2, threshold=0.85):
    """Check if two strings match with fuzzy matching."""
    ratio = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    return ratio >= threshold


def normalize_restaurant_data(raw_restaurants):
    """
    Transform scraped raw restaurant data to standard schema format.

    Args:
        raw_restaurants: List of raw restaurant dictionaries

    Returns:
        List of normalized restaurant dictionaries
    """
    normalized = []

    for idx, restaurant in enumerate(raw_restaurants, start=1):
        normalized_entry = {
            "id": f"fanshawe_rest_{idx:03d}",
            "name": restaurant.get('name', '').strip(),
            "location": restaurant.get('location', '').strip() or None,
            "description": restaurant.get('description', '').strip()[:300],  # Truncate to 300 chars
            "link": restaurant.get('link', '').strip() or None,
            "source": "fanshawe_scraper",
            "data_source": "web_scraper"
        }
        normalized.append(normalized_entry)

    return normalized


async def merge_with_existing(new_restaurants, existing_file_path):
    """
    Merge newly scraped restaurants with existing campus_restaurants.json.
    Enhances existing entries with links/descriptions if missing.
    Adds new restaurants found on webpage.

    Args:
        new_restaurants: List of newly scraped restaurant dictionaries
        existing_file_path: Path to existing campus_restaurants.json

    Returns:
        dict: Merged data with metadata
    """

    # Load existing data
    with open(existing_file_path, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)

    existing_restaurants = existing_data.get('restaurants', [])
    enhanced_count = 0
    new_count = 0

    # Create backup
    backup_path = Path(str(existing_file_path) + '.backup')
    shutil.copy(existing_file_path, backup_path)
    print(f"  ✓ Backup created: {backup_path}")

    # Track which new restaurants were already in the list
    matched_indices = set()

    # Try to match and enhance existing entries
    for existing_entry in existing_restaurants:
        existing_name = existing_entry.get('name', '').lower()

        for idx, new_restaurant in enumerate(new_restaurants):
            if idx in matched_indices:
                continue

            new_name = new_restaurant.get('name', '').lower()

            # Use fuzzy matching to detect duplicates
            if fuzzy_match(existing_name, new_name, threshold=0.85):
                matched_indices.add(idx)

                # Enhance with link if missing
                if not existing_entry.get('link'):
                    existing_entry['link'] = new_restaurant.get('link')

                # Enhance with description if missing
                if not existing_entry.get('description'):
                    existing_entry['description'] = new_restaurant.get('description')

                enhanced_count += 1
                break

    # Add new restaurants not found in existing data
    new_id_start = len(existing_restaurants) + 1

    for idx, new_restaurant in enumerate(new_restaurants):
        if idx not in matched_indices:
            # This is a new restaurant
            new_entry = {
                "id": f"fanshawe_rest_{new_id_start + new_count:03d}",
                "name": new_restaurant.get('name', ''),
                "location": new_restaurant.get('location'),
                "building": None,
                "floor": None,
                "room": None,
                "hours": None,
                "cuisine_type": None,
                "menu_highlights": [],
                "payment_methods": [],
                "description": new_restaurant.get('description', ''),
                "link": new_restaurant.get('link'),
                "source": "fanshawe_scraper",
                "data_source": "web_scraper"
            }
            existing_restaurants.append(new_entry)
            new_count += 1

    # Update metadata
    if 'metadata' not in existing_data:
        existing_data['metadata'] = {}

    existing_data['metadata'].update({
        "last_updated": datetime.now().isoformat(),
        "sources": ["manual", "web_scraper"],
        "total_restaurants": len(existing_restaurants),
        "enhanced_count": enhanced_count,
        "new_count": new_count
    })

    return {
        "data": existing_data,
        "enhanced_count": enhanced_count,
        "new_count": new_count,
        "backup_path": str(backup_path)
    }


async def extract_fanshawe_restaurants(output_file=None, update_existing=False, debug=False):
    """
    Extract restaurant information from Fanshawe food services page.

    Args:
        output_file: Custom output file path (default: timestamped in data/fanshawe_restaurants/)
        update_existing: If True, merge with data/campus_restaurants.json
        debug: If True, save screenshot for debugging

    Returns:
        dict: Extracted restaurants and metadata
    """

    # Determine output file
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path('data/fanshawe_restaurants')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f'restaurants_{timestamp}.json'
    else:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        # Browser setup
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

        # Block unnecessary resources
        await context.route("**/*", lambda route: route.abort()
            if route.request.resource_type in ["image", "font", "media", "stylesheet"]
            else route.continue_())

        page = await context.new_page()

        # Apply stealth mode
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        restaurants = []

        try:
            print("="*80)
            print("EXTRATOR FANSHAWE - RESTAURANTES")
            print("="*80)

            # Navigate to page
            fanshawe_url = "https://www.fanshawec.ca/students/life/campus-services/food"
            print(f"\n[1/4] Navegando para página...")
            print(f"  → URL: {fanshawe_url}")

            await page.goto(fanshawe_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2.0, 3.5))

            print(f"\n✓ Página carregada! URL: {page.url[:60]}...\n")

            # Wait for content to load
            print("[2/4] Aguardando conteúdo carregar...")
            await asyncio.sleep(random.uniform(2.0, 4.0))

            # Save debug screenshot if requested
            if debug:
                screenshot_path = "debug_fanshawe_restaurants.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"  📸 Screenshot salvo: {screenshot_path}")

            # Extract restaurants
            print("\n[3/4] Extraindo restaurantes...")

            restaurants_data = await extract_restaurant_data(page)
            raw_restaurants = restaurants_data.get('restaurants', [])
            extraction_method = restaurants_data.get('extractionMethod')
            total_found = restaurants_data.get('totalFound', 0)

            print(f"  ✓ Método de extração: {extraction_method or 'unknown'}")
            print(f"  ✓ Restaurantes encontrados: {len(raw_restaurants)}")

            if total_found >= MAX_RESTAURANTS_LIMIT:
                print(f"\n⚠️  AVISO: Limite máximo ({MAX_RESTAURANTS_LIMIT}) atingido!")

            # Normalize data
            print("\n[4/4] Processando e estruturando dados...")
            restaurants = normalize_restaurant_data(raw_restaurants)

            # Handle merge if requested
            if update_existing:
                print("\n[4b/4] Mesclando com campus_restaurants.json...")

                existing_file = Path('data/campus_restaurants.json')
                if existing_file.exists():
                    merge_result = await merge_with_existing(restaurants, existing_file)
                    output_data = merge_result['data']

                    print(f"  ✓ Restaurantes enhançados: {merge_result['enhanced_count']}")
                    print(f"  ✓ Restaurantes novos adicionados: {merge_result['new_count']}")
                    print(f"  ✓ Backup criado: {merge_result['backup_path']}")

                    # Save merged data to campus_restaurants.json
                    output_file = existing_file
                else:
                    print(f"  ⚠️  Arquivo campus_restaurants.json não encontrado!")
                    output_data = {
                        "metadata": {
                            "source": "fanshawe_food_page_scraper",
                            "scraped_at": datetime.now().isoformat(),
                            "total_restaurants": len(restaurants),
                            "source_url": "https://www.fanshawec.ca/students/life/campus-services/food",
                            "extraction_method": extraction_method
                        },
                        "restaurants": restaurants
                    }
            else:
                # Create standalone output
                output_data = {
                    "metadata": {
                        "source": "fanshawe_food_page_scraper",
                        "scraped_at": datetime.now().isoformat(),
                        "total_restaurants": len(restaurants),
                        "source_url": "https://www.fanshawec.ca/students/life/campus-services/food",
                        "extraction_method": extraction_method
                    },
                    "restaurants": restaurants
                }

            # Save output
            print("\n" + "="*80)
            print("SALVANDO RESULTADOS")
            print("="*80)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Arquivo salvo: {output_file}")
            print(f"✓ Total de restaurantes: {len(restaurants)}")
            print(f"✓ Método de extração: {extraction_method or 'unknown'}")

            return output_data

        except Exception as e:
            print(f"\n✗ ERRO FATAL: {str(e)}")

            # Save partial results if any
            if restaurants:
                partial_output = {
                    "metadata": {
                        "source": "fanshawe_food_page_scraper",
                        "scraped_at": datetime.now().isoformat(),
                        "partial": True,
                        "error": str(e),
                        "total_restaurants": len(restaurants)
                    },
                    "restaurants": restaurants
                }

                partial_file = Path('data/fanshawe_restaurants/restaurants_partial.json')
                partial_file.parent.mkdir(parents=True, exist_ok=True)

                with open(partial_file, 'w', encoding='utf-8') as f:
                    json.dump(partial_output, f, indent=2, ensure_ascii=False)

                print(f"✓ Resultados parciais salvos em: {partial_file}")

            raise

        finally:
            await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extrai informações de restaurantes do site Fanshawe'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Arquivo de saída customizado'
    )
    parser.add_argument(
        '--update-existing',
        action='store_true',
        help='Mesclar com data/campus_restaurants.json'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Ativar modo debug (salva screenshots)'
    )

    args = parser.parse_args()

    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  EXTRATOR FANSHAWE - RESTAURANTES".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print()

    result = asyncio.run(extract_fanshawe_restaurants(
        output_file=args.output,
        update_existing=args.update_existing,
        debug=args.debug
    ))

    print("\n" + "="*80)
    print("CONCLUÍDO COM SUCESSO!")
    print("="*80)
    print(f"Total de restaurantes: {result['metadata']['total_restaurants']}")
    print(f"Arquivo: {args.output or 'data/fanshawe_restaurants/restaurants_*.json'}")
    print("="*80 + "\n")
