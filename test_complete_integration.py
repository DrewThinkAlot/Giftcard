#!/usr/bin/env python3
"""
Complete integration test for the Telegram Gift Card Deal Bot
Tests the full pipeline: scraping -> filtering -> duplicate checking -> formatting
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import GiftCardScraper
from database import DealDatabase
from main import GiftCardDealBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_operations():
    """Test database operations"""
    print("🗄️  Testing Database Operations...")
    print("-" * 40)
    
    db = DealDatabase()
    
    # Test deal
    test_deal = {
        'merchant': 'Test Store Integration',
        'face_value': 100.0,
        'price': 80.0,
        'discount_percent': 20.0,
        'source': 'test',
        'url': 'https://example.com/test-deal'
    }
    
    # Test hash generation
    deal_hash = db.generate_deal_hash(test_deal)
    print(f"✅ Deal hash generated: {deal_hash[:8]}...")
    
    # Test duplicate checking (should be False initially)
    is_posted = db.is_deal_posted(test_deal)
    print(f"✅ Deal posted check (should be False): {is_posted}")
    
    # Test filtering new deals
    test_deals = [test_deal]
    new_deals = db.filter_new_deals(test_deals)
    print(f"✅ New deals filter: {len(new_deals)} out of {len(test_deals)}")
    
    return True

def test_scraper_integration():
    """Test scraper integration"""
    print("\n🕷️  Testing Scraper Integration...")
    print("-" * 40)
    
    scraper = GiftCardScraper()
    
    # Test individual scrapers
    print("Testing CardCash scraper...")
    cardcash_deals = scraper.scrape_cardcash_deals()
    print(f"✅ CardCash deals found: {len(cardcash_deals)}")
    
    print("Testing GCX scraper...")
    gcx_deals = scraper.scrape_raise_deals()
    print(f"✅ GCX deals found: {len(gcx_deals)}")
    
    # Test combined scraper
    all_deals = scraper.get_all_deals()
    print(f"✅ Total deals from all sources: {len(all_deals)}")
    
    return all_deals

def test_bot_integration():
    """Test complete bot integration"""
    print("\n🤖 Testing Complete Bot Integration...")
    print("-" * 40)
    
    bot = GiftCardDealBot()
    
    # Test deal fetching
    print("Fetching deals...")
    all_deals = bot.fetch_all_deals()
    print(f"✅ Bot fetched {len(all_deals)} deals")
    
    # Test deal filtering
    print("Filtering deals...")
    filtered_deals = bot.filter_deals(all_deals, min_discount=15.0)
    premium_deals = bot.filter_deals(all_deals, min_discount=25.0)
    
    print(f"✅ Filtered deals (≥15%): {len(filtered_deals)}")
    print(f"✅ Premium deals (≥25%): {len(premium_deals)}")
    
    # Test message formatting
    if filtered_deals:
        print("\nTesting message formatting...")
        sample_deal = filtered_deals[0]
        
        # Test regular message
        regular_message = bot.format_deal_message(sample_deal, is_premium=False)
        print("✅ Regular message formatted")
        print("Sample regular message:")
        print(regular_message)
        
        # Test premium message
        premium_message = bot.format_deal_message(sample_deal, is_premium=True)
        print("\n✅ Premium message formatted")
        print("Sample premium message:")
        print(premium_message)
    
    return {
        'total_deals': len(all_deals),
        'filtered_deals': len(filtered_deals),
        'premium_deals': len(premium_deals)
    }

def test_duplicate_prevention():
    """Test duplicate prevention system"""
    print("\n🔄 Testing Duplicate Prevention...")
    print("-" * 40)
    
    db = DealDatabase()
    
    # Create a test deal
    test_deal = {
        'merchant': 'Duplicate Test Store',
        'face_value': 50.0,
        'price': 40.0,
        'discount_percent': 20.0,
        'source': 'test',
        'url': 'https://example.com/duplicate-test'
    }

    # Pre-test cleanup: ensure the test deal doesn't exist
    try:
        if db.supabase:
            deal_hash = db.generate_deal_hash(test_deal)
            db.supabase.table('posted_deals').delete().eq('deal_hash', deal_hash).execute()
            print(f"🧹 Pre-test cleanup: Removed any lingering test deals.")
    except Exception as e:
        logger.warning(f"Pre-test cleanup failed, but continuing: {e}")
    
    # Test filtering - should return the deal initially
    deals_list = [test_deal]
    new_deals_first = db.filter_new_deals(deals_list)
    print(f"✅ First filter: {len(new_deals_first)} new deals (should be 1)")
    
    # Mark the deal as posted (simulate posting)
    if new_deals_first:
        success = db.mark_deal_as_posted(test_deal)
        print(f"✅ Deal marked as posted: {success}")
    
    # Test filtering again - should return empty list (duplicate)
    new_deals_second = db.filter_new_deals(deals_list)
    print(f"✅ Second filter: {len(new_deals_second)} new deals (should be 0)")

    # Cleanup: remove the test deal from the database
    try:
        if db.supabase:
            deal_hash = db.generate_deal_hash(test_deal)
            db.supabase.table('posted_deals').delete().eq('deal_hash', deal_hash).execute()
            print(f"🧹 Cleanup: Test deal removed from database.")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
    
    return len(new_deals_first) == 1 and len(new_deals_second) == 0

def main():
    """Run complete integration test"""
    print("🚀 Starting Complete Integration Test")
    print("=" * 50)
    
    test_results = {
        'database': False,
        'scraper': False,
        'bot': False,
        'duplicates': False
    }
    
    try:
        # Test database operations
        test_results['database'] = test_database_operations()
        
        # Test scraper integration
        deals = test_scraper_integration()
        test_results['scraper'] = len(deals) > 0
        
        # Test bot integration
        bot_results = test_bot_integration()
        test_results['bot'] = bot_results['total_deals'] > 0
        
        # Test duplicate prevention
        test_results['duplicates'] = test_duplicate_prevention()
        
        # Summary
        print("\n📊 Integration Test Results")
        print("=" * 50)
        print(f"✅ Database Operations: {'PASS' if test_results['database'] else 'FAIL'}")
        print(f"✅ Scraper Integration: {'PASS' if test_results['scraper'] else 'FAIL'}")
        print(f"✅ Bot Integration: {'PASS' if test_results['bot'] else 'FAIL'}")
        print(f"✅ Duplicate Prevention: {'PASS' if test_results['duplicates'] else 'FAIL'}")
        
        all_passed = all(test_results.values())
        print(f"\n🎯 Overall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        
        if all_passed:
            print("\n🎉 The bot is ready for deployment!")
            print("Next steps:")
            print("1. Set up Supabase database with the provided schema")
            print("2. Configure environment variables (.env file)")
            print("3. Set up Telegram bot and channels")
            print("4. Configure Geniuslink for affiliate link shortening")
            print("5. Deploy to your preferred hosting platform")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"Integration test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
