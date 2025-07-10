#!/usr/bin/env python3
"""
Test script to verify Telegram bot integration
Run this after setting up your Telegram bot credentials
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import GiftCardDealBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_telegram_connection():
    """Test Telegram bot connection and message sending"""
    print("📱 Testing Telegram Bot Connection...")
    print("=" * 50)
    
    # Check if credentials are available
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
    premium_channel_id = os.getenv('TELEGRAM_PREMIUM_CHANNEL_ID')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Please set up your .env file with Telegram credentials")
        return False
    
    if not channel_id:
        print("❌ TELEGRAM_CHANNEL_ID not found in environment variables")
        print("Please set up your .env file with channel ID")
        return False
    
    print(f"✅ Bot token found: {bot_token[:10]}...")
    print(f"✅ Channel ID found: {channel_id}")
    if premium_channel_id:
        print(f"✅ Premium channel ID found: {premium_channel_id}")
    
    # Initialize bot
    bot = GiftCardDealBot()
    
    # Create test deal
    test_deal = {
        'merchant': 'Test Store',
        'face_value': 100.0,
        'price': 85.0,
        'discount_percent': 15.0,
        'source': 'test',
        'url': 'https://example.com/test-deal'
    }
    
    # Test regular message
    print("\n📤 Testing regular message...")
    regular_message = bot.format_deal_message(test_deal, is_premium=False)
    print("Message to be sent:")
    print("-" * 30)
    print(regular_message)
    print("-" * 30)
    
    # Ask for confirmation before sending
    response = input("\nSend this test message to your channel? (y/n): ").lower().strip()
    if response == 'y':
        success = bot.send_telegram_message(regular_message)
        if success:
            print("✅ Regular message sent successfully!")
        else:
            print("❌ Failed to send regular message")
            return False
    else:
        print("⏭️  Skipping regular message test")
    
    # Test premium message if premium channel is configured
    if premium_channel_id:
        print("\n📤 Testing premium message...")
        premium_message = bot.format_deal_message(test_deal, is_premium=True)
        print("Premium message to be sent:")
        print("-" * 30)
        print(premium_message)
        print("-" * 30)
        
        response = input("\nSend this test message to your premium channel? (y/n): ").lower().strip()
        if response == 'y':
            success = bot.send_telegram_message(premium_message, premium_channel_id)
            if success:
                print("✅ Premium message sent successfully!")
            else:
                print("❌ Failed to send premium message")
                return False
        else:
            print("⏭️  Skipping premium message test")
    
    print("\n🎉 Telegram integration test completed!")
    return True

def main():
    """Main test function"""
    print("🚀 Telegram Bot Integration Test")
    print("This will test your Telegram bot setup and send test messages")
    print("Make sure you have set up your .env file with Telegram credentials\n")
    
    try:
        success = test_telegram_connection()
        
        if success:
            print("\n✅ All tests passed! Your Telegram bot is ready.")
            print("\nNext steps:")
            print("1. Set up Supabase database for duplicate prevention")
            print("2. Configure Geniuslink for affiliate link shortening")
            print("3. Deploy the bot to run every 5 minutes")
        else:
            print("\n❌ Some tests failed. Please check your configuration.")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    main()
