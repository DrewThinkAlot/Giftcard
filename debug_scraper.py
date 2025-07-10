#!/usr/bin/env python3
"""
Debug script to inspect the actual HTML structure of the websites
This helps us understand what data is available for scraping
"""

import requests
from bs4 import BeautifulSoup
import json
import re

def debug_website(url, name):
    """Debug a website's HTML structure"""
    print(f"\n🔍 Debugging {name} ({url})")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"📄 Page Title: {soup.title.string if soup.title else 'No title'}")
        print(f"📊 Page Size: {len(response.content)} bytes")
        
        # Look for JSON data in script tags (common for modern sites)
        script_tags = soup.find_all('script')
        json_data_found = False
        
        for i, script in enumerate(script_tags):
            if script.string:
                script_content = script.string.strip()
                # Look for JSON-like structures
                if any(keyword in script_content for keyword in ['gift', 'card', 'price', 'discount', 'deal']):
                    print(f"\n🎯 Potential data in script tag {i}:")
                    # Try to extract JSON objects
                    json_matches = re.findall(r'\{[^{}]*(?:"(?:gift|card|price|discount|deal|merchant|brand)")[^{}]*\}', script_content, re.IGNORECASE)
                    for j, match in enumerate(json_matches[:3]):  # Show first 3 matches
                        print(f"  JSON {j+1}: {match[:200]}...")
                        json_data_found = True
        
        if not json_data_found:
            print("❌ No obvious JSON data found in script tags")
        
        # Look for data attributes
        elements_with_data = soup.find_all(attrs={"data-price": True}) + \
                           soup.find_all(attrs={"data-discount": True}) + \
                           soup.find_all(attrs={"data-value": True})
        
        if elements_with_data:
            print(f"\n📋 Found {len(elements_with_data)} elements with data attributes:")
            for elem in elements_with_data[:5]:
                print(f"  - {elem.name}: {dict(elem.attrs)}")
        
        # Look for price patterns in visible text
        all_text = soup.get_text()
        price_matches = re.findall(r'\$\d+(?:\.\d{2})?', all_text)
        percent_matches = re.findall(r'\d+%', all_text)
        
        print(f"\n💰 Found {len(price_matches)} price patterns: {price_matches[:10]}")
        print(f"📈 Found {len(percent_matches)} percentage patterns: {percent_matches[:10]}")
        
        # Look for common class patterns
        common_classes = {}
        for elem in soup.find_all(class_=True):
            for class_name in elem.get('class', []):
                if any(keyword in class_name.lower() for keyword in ['card', 'gift', 'deal', 'product', 'item']):
                    common_classes[class_name] = common_classes.get(class_name, 0) + 1
        
        if common_classes:
            print(f"\n🏷️  Common relevant classes:")
            for class_name, count in sorted(common_classes.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {class_name}: {count} occurrences")
        
        # Save a sample of the HTML for manual inspection
        filename = f"/Users/admin/CascadeProjects/telegram-deal-bot/debug_{name.lower().replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"\n💾 Saved HTML sample to: {filename}")
        
    except Exception as e:
        print(f"❌ Error debugging {name}: {e}")

def main():
    """Debug both websites"""
    print("🔍 Website Structure Debug Tool")
    print("This will help us understand how to extract gift card deals")
    
    # Debug GCX (Raise)
    debug_website("https://gcx.raise.com/buy-gift-cards", "GCX Raise")
    
    # Debug CardCash
    debug_website("https://www.cardcash.com/buy-gift-cards", "CardCash")
    
    print("\n✅ Debug complete! Check the saved HTML files for manual inspection.")

if __name__ == "__main__":
    main()
