#!/usr/bin/env python3
"""
Test script to validate the web scraping functionality
This helps debug and refine the scraping logic before full deployment
"""

import logging
from scraper import GiftCardScraper
import json

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_scraper():
    """Test the gift card scraper with detailed output"""
    print("🔍 Testing Gift Card Scraper...")
    print("=" * 50)
    
    scraper = GiftCardScraper()
    
    # Test Raise.com scraping
    print("\n📊 Testing Raise.com scraping...")
    raise_deals = scraper.scrape_raise_deals()
    print(f"Found {len(raise_deals)} deals from Raise.com")
    
    if raise_deals:
        print("\nSample Raise.com deals:")
        for i, deal in enumerate(raise_deals[:3]):
            print(f"{i+1}. {deal['merchant']}: ${deal['price']:.2f} (was ${deal['face_value']:.2f}) - {deal['discount_percent']:.1f}% off")
            print(f"   URL: {deal['url']}")
    
    # Test CardCash.com scraping
    print("\n💳 Testing CardCash.com scraping...")
    cardcash_deals = scraper.scrape_cardcash_deals()
    print(f"Found {len(cardcash_deals)} deals from CardCash.com")
    
    if cardcash_deals:
        print("\nSample CardCash.com deals:")
        for i, deal in enumerate(cardcash_deals[:3]):
            print(f"{i+1}. {deal['merchant']}: ${deal['price']:.2f} (was ${deal['face_value']:.2f}) - {deal['discount_percent']:.1f}% off")
            print(f"   URL: {deal['url']}")
    
    # Combined results
    all_deals = raise_deals + cardcash_deals
    print(f"\n📈 Total deals found: {len(all_deals)}")
    
    # Filter for high-discount deals
    high_discount_deals = [deal for deal in all_deals if deal.get('discount_percent', 0) >= 15]
    premium_deals = [deal for deal in all_deals if deal.get('discount_percent', 0) >= 25]
    
    print(f"🎯 Deals with 15%+ discount: {len(high_discount_deals)}")
    print(f"⭐ Premium deals with 25%+ discount: {len(premium_deals)}")
    
    if high_discount_deals:
        print("\n🔥 Best deals (15%+ off):")
        sorted_deals = sorted(high_discount_deals, key=lambda x: x.get('discount_percent', 0), reverse=True)
        for i, deal in enumerate(sorted_deals[:5]):
            print(f"{i+1}. {deal['merchant']}: {deal['discount_percent']:.1f}% off (${deal['price']:.2f})")
    
    # Save results to file for inspection
    if all_deals:
        with open('/Users/admin/CascadeProjects/telegram-deal-bot/test_results.json', 'w') as f:
            json.dump(all_deals, f, indent=2, default=str)
        print(f"\n💾 Full results saved to test_results.json")
    
    return all_deals

if __name__ == "__main__":
    deals = test_scraper()
    print(f"\n✅ Test completed. Found {len(deals)} total deals.")
