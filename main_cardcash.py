#!/usr/bin/env python3
"""
CardCash-only scraper for the Telegram Gift Card Deal Bot
Runs every hour since CardCash deals are more stable
"""

import logging
from datetime import datetime
from scraper import CardCashScraper
from database import DealDatabase
from services import telegram_service, geniuslink_service
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_cardcash_deals():
    """Process deals from CardCash only"""
    logger.info("Starting CardCash deal processing...")
    
    db = DealDatabase()
    scraper = CardCashScraper()
    
    deals_posted = 0
    premium_deals_posted = 0
    errors = []
    
    try:
        # Fetch deals from CardCash only
        all_deals = scraper.scrape()
        logger.info(f"Found {len(all_deals)} CardCash deals")
        
        # Filter deals by discount threshold
        regular_deals = []
        premium_deals = []
        
        for deal in all_deals:
            discount = deal.get('discount_percent', 0)
            if discount >= 15.0:
                regular_deals.append(deal)
            if discount >= 25.0:
                premium_deals.append(deal)
        
        # Remove duplicates using database
        new_regular_deals = db.filter_new_deals(regular_deals)
        new_premium_deals = db.filter_new_deals(premium_deals)
        
        logger.info(f"Found {len(new_regular_deals)} new regular deals, {len(new_premium_deals)} new premium deals")
        
        # Process regular deals
        for deal in new_regular_deals:
            try:
                message = format_deal_message(deal)
                if telegram_service.send_message(message, config.telegram_channel_id):
                    if db.mark_deal_as_posted(deal):
                        deals_posted += 1
                        logger.info(f"Posted CardCash deal: {deal.get('merchant', 'Unknown')}")
            except Exception as e:
                error_msg = f"Error posting CardCash deal {deal.get('merchant', 'Unknown')}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Process premium deals (if premium channel is configured)
        if config.telegram_premium_channel_id:
            for deal in new_premium_deals:
                try:
                    message = format_deal_message(deal, is_premium=True)
                    if telegram_service.send_message(message, config.telegram_premium_channel_id):
                        if db.mark_deal_as_posted(deal):
                            premium_deals_posted += 1
                            logger.info(f"Posted CardCash premium deal: {deal.get('merchant', 'Unknown')}")
                except Exception as e:
                    error_msg = f"Error posting CardCash premium deal {deal.get('merchant', 'Unknown')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        # Log execution statistics
        status = 'success' if not errors else ('partial' if deals_posted > 0 else 'error')
        error_summary = '; '.join(errors[:3]) if errors else None
        
        db.log_bot_execution(
            deals_found=len(all_deals),
            deals_posted=deals_posted,
            premium_deals_posted=premium_deals_posted,
            errors=error_summary,
            status=status
        )
        
        logger.info(f"CardCash processing completed: {deals_posted} regular, {premium_deals_posted} premium deals posted")
        
    except Exception as e:
        error_msg = f"Critical error in CardCash processing: {e}"
        logger.error(error_msg)
        db.log_bot_execution(
            deals_found=0,
            deals_posted=0,
            premium_deals_posted=0,
            errors=error_msg,
            status='error'
        )

def format_deal_message(deal: dict, is_premium: bool = False) -> str:
    """Format deal into Telegram message with markdown and emojis"""
    merchant = deal.get('merchant', 'Unknown')
    face_value = deal.get('face_value', 0)
    price = deal.get('price', 0)
    discount_percent = deal.get('discount_percent', 0)
    original_url = deal.get('url', '')

    # Shorten the URL using the Geniuslink service
    short_url = geniuslink_service.shorten_url(original_url) or original_url

    # Message formatting
    premium_header = "🌟 **PREMIUM DEAL** 🌟\n\n" if is_premium else ""
    message = (
        f"{premium_header}🎯 **{merchant} Gift Card**\n"
        f"💳 **Face Value:** ${face_value:.2f}\n"
        f"💸 **Price:** ${price:.2f} *({discount_percent:.1f}% OFF)*\n"
        f"🔗 [**Buy Now**]({short_url})\n"
        f"📍 *Source: CardCash*"
    )

    return message

if __name__ == "__main__":
    process_cardcash_deals()
