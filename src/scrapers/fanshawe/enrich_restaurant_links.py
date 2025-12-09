"""
Script to enrich restaurant data by accessing links and gathering detailed information.
Fetches content from restaurant FSU pages and compiles into comprehensive report.
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


async def fetch_and_parse_restaurant_page(page, url: str) -> Dict:
    """
    Fetch a restaurant page and extract detailed information.

    Args:
        page: Playwright page object
        url: URL to fetch

    Returns:
        Dictionary with extracted information
    """
    info = {
        "url": url,
        "accessible": False,
        "hours": None,
        "menu_items": [],
        "location": None,
        "description": None,
        "phone": None,
        "email": None,
        "payment_methods": [],
        "dietary_options": [],
        "special_features": [],
        "raw_content_preview": ""
    }

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        info["accessible"] = True

        # Extract all text content
        text_content = await page.inner_text("body")
        info["raw_content_preview"] = text_content[:500] if text_content else ""

        # Try to extract hours using JavaScript
        hours_data = await page.evaluate("""
            () => {
                const hourPatterns = [
                    document.querySelector('[class*="hour"]'),
                    document.querySelector('[class*="time"]'),
                    document.querySelector('[class*="open"]'),
                    document.querySelector('[id*="hours"]'),
                    document.querySelector('[id*="time"]')
                ];

                const found = [];
                for (let elem of hourPatterns) {
                    if (elem) {
                        found.push(elem.innerText);
                    }
                }

                return found.length > 0 ? found : null;
            }
        """)

        if hours_data:
            info["hours"] = hours_data

        # Extract phone numbers
        phone_match = re.findall(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text_content or "")
        if phone_match:
            info["phone"] = phone_match[0]

        # Extract email addresses
        email_match = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_content or "")
        if email_match:
            info["email"] = email_match[0]

        # Look for menu items (common keywords)
        menu_keywords = ['menu', 'items', 'food', 'drink', 'beverage', 'sandwich', 'salad', 'coffee', 'juice']
        text_lower = (text_content or "").lower()

        for keyword in menu_keywords:
            if keyword in text_lower:
                # Find surrounding context
                idx = text_lower.find(keyword)
                context = text_content[max(0, idx-50):min(len(text_content), idx+200)]
                if context not in info["menu_items"]:
                    info["menu_items"].append(context.strip())

        # Look for dietary options
        dietary_keywords = ['vegan', 'vegetarian', 'gluten', 'dairy', 'nut', 'halal', 'kosher', 'allergen']
        for keyword in dietary_keywords:
            if keyword in text_lower:
                info["dietary_options"].append(keyword.capitalize())

        # Remove duplicates
        info["dietary_options"] = list(set(info["dietary_options"]))
        info["menu_items"] = info["menu_items"][:5]  # Limit to first 5

    except Exception as e:
        info["error"] = str(e)

    return info


async def enrich_restaurants_from_file(input_file: Path, output_file: Optional[Path] = None) -> Dict:
    """
    Load restaurant data from JSON file and enrich restaurants with links.

    Args:
        input_file: Path to input restaurants JSON file
        output_file: Path to save enriched data (default: timestamped in same directory)

    Returns:
        Dictionary with enriched restaurant data
    """

    # Load input file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    restaurants = data.get('restaurants', [])
    metadata = data.get('metadata', {})

    # Determine output file
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = input_file.parent
        output_file = output_dir / f'detailed_restaurant_info_{timestamp}.json'
    else:
        output_file = Path(output_file)

    # Filter restaurants with links
    restaurants_with_links = [r for r in restaurants if r.get('link')]

    print(f"\n{'='*80}")
    print("ENRICHING RESTAURANT DATA FROM LINKS")
    print(f"{'='*80}")
    print(f"\nInput file: {input_file}")
    print(f"Total restaurants: {len(restaurants)}")
    print(f"Restaurants with links: {len(restaurants_with_links)}")
    print(f"\nOutput will be saved to: {output_file}\n")

    # Launch browser
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
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

        enriched_restaurants = []

        try:
            # Process each restaurant with a link
            for idx, restaurant in enumerate(restaurants_with_links, 1):
                rest_id = restaurant.get('id', 'unknown')
                rest_name = restaurant.get('name', 'Unknown')
                rest_link = restaurant.get('link')

                print(f"[{idx}/{len(restaurants_with_links)}] Processing: {rest_name}")
                print(f"  → URL: {rest_link}")

                # Fetch and parse page
                detailed_info = await fetch_and_parse_restaurant_page(page, rest_link)

                # Combine with original data
                enriched = {
                    "id": rest_id,
                    "name": rest_name,
                    "original_link": rest_link,
                    "source": restaurant.get('source', 'fanshawe_scraper'),
                    "data_source": restaurant.get('data_source', 'web_scraper'),
                    "original_data": {
                        "location": restaurant.get('location'),
                        "description": restaurant.get('description'),
                        "building": restaurant.get('building'),
                        "floor": restaurant.get('floor'),
                        "hours": restaurant.get('hours'),
                        "cuisine_type": restaurant.get('cuisine_type'),
                        "menu_highlights": restaurant.get('menu_highlights', [])
                    },
                    "detailed_info": detailed_info
                }

                enriched_restaurants.append(enriched)

                # Status indicators
                if detailed_info["accessible"]:
                    print(f"  ✓ Page accessible")
                    if detailed_info.get("phone"):
                        print(f"    Phone: {detailed_info['phone']}")
                    if detailed_info.get("email"):
                        print(f"    Email: {detailed_info['email']}")
                    if detailed_info.get("dietary_options"):
                        print(f"    Dietary options: {', '.join(detailed_info['dietary_options'])}")
                else:
                    print(f"  ⚠ Page not accessible: {detailed_info.get('error', 'Unknown error')}")

                print()

                # Rate limiting
                await asyncio.sleep(1)

        finally:
            await browser.close()

    # Prepare output
    output_data = {
        "metadata": {
            "source": "restaurant_link_enrichment",
            "generated_at": datetime.now().isoformat(),
            "source_file": str(input_file),
            "total_restaurants_processed": len(restaurants_with_links),
            "successful_enrichments": sum(1 for r in enriched_restaurants if r["detailed_info"]["accessible"]),
            "original_metadata": metadata
        },
        "restaurants": enriched_restaurants
    }

    # Save output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print("ENRICHMENT COMPLETE")
    print(f"{'='*80}")
    print(f"Output file: {output_file}")
    print(f"Restaurants with links accessed: {len(enriched_restaurants)}")
    print(f"Successfully accessible: {output_data['metadata']['successful_enrichments']}")
    print(f"{'='*80}\n")

    return output_data


async def main():
    parser = argparse.ArgumentParser(
        description='Enrich restaurant data by accessing and parsing FSU restaurant pages'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=False,
        help='Input restaurants JSON file (default: most recent in data/fanshawe_restaurants/)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: timestamped in same directory as input)'
    )

    args = parser.parse_args()

    # Determine input file
    if args.input:
        input_file = Path(args.input)
    else:
        # Find most recent file in fanshawe_restaurants directory
        fanshawe_dir = Path('data/fanshawe_restaurants')
        restaurant_files = sorted(
            fanshawe_dir.glob('restaurants_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not restaurant_files:
            print("Error: No restaurant files found in data/fanshawe_restaurants/")
            return

        input_file = restaurant_files[0]
        print(f"Using most recent file: {input_file}")

    # Run enrichment
    await enrich_restaurants_from_file(input_file, Path(args.output) if args.output else None)


if __name__ == "__main__":
    asyncio.run(main())
