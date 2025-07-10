#!/usr/bin/env python3
"""
Script to analyze HTML structure from Raise.com and CardCash.com to find correct CSS selectors.
This script uses Scrapingdog to fetch the pages and then analyzes the structure.
"""

import requests
from bs4 import BeautifulSoup
import json
from config import config

def fetch_page_via_scrapingdog(url):
    """Fetch a page using Scrapingdog API"""
    if not config.scrapingdog_api_key:
        print("Error: SCRAPINGDOG_API_KEY is not set in your .env file")
        return None
    
    try:
        api_url = f"https://api.scrapingdog.com/scrape?api_key={config.scrapingdog_api_key}&url={url}&dynamic=true"
        print(f"Fetching {url} via Scrapingdog...")
        response = requests.get(api_url, timeout=90)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def analyze_gcx_structure():
    """Analyze GCX (Raise) page structure"""
    print("\n=== ANALYZING GCX (RAISE) STRUCTURE ===")
    
    html_content = fetch_page_via_scrapingdog("https://gcx.raise.com/buy-gift-cards")
    if not html_content:
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Save HTML for manual inspection
    with open('/tmp/gcx_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("Saved GCX HTML to /tmp/gcx_page.html for manual inspection")
    
    # Look for common patterns that might contain gift card deals
    print("\n--- Looking for potential deal containers ---")
    
    # Check for various card-like elements
    potential_selectors = [
        'div[class*="card"]',
        'div[class*="gift"]',
        'div[class*="deal"]',
        'div[class*="product"]',
        'div[class*="item"]',
        'article',
        '[data-testid*="card"]',
        '[data-testid*="product"]',
        'a[href*="gift-card"]',
        'a[href*="buy"]'
    ]
    
    for selector in potential_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"Found {len(elements)} elements with selector: {selector}")
            # Show first element's structure
            if len(elements) > 0:
                first_elem = elements[0]
                print(f"  Sample element classes: {first_elem.get('class', [])}")
                print(f"  Sample element text (first 100 chars): {first_elem.get_text()[:100]}...")
    
    # Look for price-like patterns
    print("\n--- Looking for price patterns ---")
    price_elements = soup.find_all(text=lambda text: text and '$' in text)
    print(f"Found {len(price_elements)} elements containing '$'")
    
    # Look for percentage patterns
    percent_elements = soup.find_all(text=lambda text: text and '%' in text)
    print(f"Found {len(percent_elements)} elements containing '%'")

def analyze_cardcash_structure():
    """Analyze CardCash page structure"""
    print("\n=== ANALYZING CARDCASH STRUCTURE ===")
    
    html_content = fetch_page_via_scrapingdog("https://www.cardcash.com/buy-gift-cards/")
    if not html_content:
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Save HTML for manual inspection
    with open('/tmp/cardcash_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("Saved CardCash HTML to /tmp/cardcash_page.html for manual inspection")
    
    # Look for common patterns
    print("\n--- Looking for potential deal containers ---")
    
    potential_selectors = [
        'div[class*="card"]',
        'div[class*="gift"]',
        'div[class*="deal"]',
        'div[class*="product"]',
        'div[class*="item"]',
        'article',
        'a[href*="gift-card"]',
        'a[href*="discount"]',
        '[class*="discount"]'
    ]
    
    for selector in potential_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"Found {len(elements)} elements with selector: {selector}")
            if len(elements) > 0:
                first_elem = elements[0]
                print(f"  Sample element classes: {first_elem.get('class', [])}")
                print(f"  Sample element text (first 100 chars): {first_elem.get_text()[:100]}...")
    
    # Look for price and percentage patterns
    print("\n--- Looking for price patterns ---")
    price_elements = soup.find_all(text=lambda text: text and '$' in text)
    print(f"Found {len(price_elements)} elements containing '$'")
    
    percent_elements = soup.find_all(text=lambda text: text and '%' in text)
    print(f"Found {len(percent_elements)} elements containing '%'")

def main():
    """Main function to analyze both sites"""
    print("Gift Card Site Structure Analyzer")
    print("=" * 50)
    
    analyze_gcx_structure()
    analyze_cardcash_structure()
    
    print("\n" + "=" * 50)
    print("Analysis complete!")
    print("Check /tmp/gcx_page.html and /tmp/cardcash_page.html for detailed HTML structure")
    print("Use this information to update the CSS selectors in scraper.py")

if __name__ == '__main__':
    main()
