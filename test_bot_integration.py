#!/usr/bin/env python3
"""
Test script to verify bot integration with scraper
Tests deal fetching, filtering, and message formatting
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_deal_message(deal: dict, is_premium: bool = False) -> str:
    """Format a deal into a Telegram message"""
    emoji = "🔥" if is_premium else "💳"
    
    message = f"{emoji} **{deal['merchant']} Gift Card Deal**\n\n"
    message += f"💰 **Price:** ${deal['price']:.2f}\n"
    message += f"💵 **Face Value:** ${deal['face_value']:.2f}\n"
    message += f"📈 **Discount:** {deal['discount_percent']:.1f}% OFF\n"
    message += f"💸 **You Save:** ${deal['face_value'] - deal['price']:.2f}\n\n"
    
    if deal.get('url'):
        message += f"🔗 [Get This Deal]({deal['url']})\n\n"
    
    message += f"📍 Source: {deal['source'].upper()}\n"
    message += f"⏰ Found: {datetime.now().strftime('%I:%M %p')}"
    
    return message

def test_bot_integration():
    """Test the bot integration with scraper"""
    print("🤖 Testing Bot Integration with Scraper")
    print("=" * 50)
    
    try:
        # Initialize scraper
        scraper = GiftCardScraper()
        
        # Fetch all deals
        print("📡 Fetching deals from all sources...")
        all_deals = scraper.get_all_deals()
        
        print(f"✅ Found {len(all_deals)} total deals")
        
        # Filter deals by discount threshold
        regular_deals = [deal for deal in all_deals if deal['discount_percent'] >= 15.0]
        premium_deals = [deal for deal in all_deals if deal['discount_percent'] >= 25.0]
        
        print(f"🎯 Regular deals (≥15% off): {len(regular_deals)}")
        print(f"⭐ Premium deals (≥25% off): {len(premium_deals)}")
        
        # Show sample formatted messages
        if regular_deals:
            print("\n📝 Sample Regular Deal Message:")
            print("-" * 40)
            sample_deal = regular_deals[0]
            formatted_message = format_deal_message(sample_deal, is_premium=False)
            print(formatted_message)
        
        if premium_deals:
            print("\n🔥 Sample Premium Deal Message:")
            print("-" * 40)
            sample_premium = premium_deals[0]
            formatted_message = format_deal_message(sample_premium, is_premium=True)
            print(formatted_message)
        
        # Test deal uniqueness (simulate duplicate detection)
        print(f"\n🔍 Testing Deal Uniqueness...")
        unique_deals = {}
        duplicates = 0
        
        for deal in all_deals:
            # Create a unique hash for each deal
            deal_key = f"{deal['merchant']}_{deal['discount_percent']}_{deal['source']}"
            deal_hash = hashlib.md5(deal_key.encode()).hexdigest()
            
            if deal_hash in unique_deals:
                duplicates += 1
            else:
                unique_deals[deal_hash] = deal
        
        print(f"✅ Unique deals: {len(unique_deals)}")
        print(f"🔄 Duplicates found: {duplicates}")
        
        # Summary
        print(f"\n📊 Integration Test Summary:")
        print(f"   • Total deals scraped: {len(all_deals)}")
        print(f"   • Regular deals (≥15%): {len(regular_deals)}")
        print(f"   • Premium deals (≥25%): {len(premium_deals)}")
        print(f"   • Unique deals: {len(unique_deals)}")
        print(f"   • Ready for Telegram posting: ✅")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False

if __name__ == "__main__":
    import hashlib
    success = test_bot_integration()
    if success:
        print("\n🎉 Bot integration test completed successfully!")
    else:
        print("\n❌ Bot integration test failed!")
        sys.exit(1)
