#!/usr/bin/env python3
"""
Telegram Gift Card Deal Bot
Scrapes deals from Raise.com and CardCash.com, filters for 15%+ discounts,
and posts formatted messages to Telegram channels.
"""

import os
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

from config import config
from scraper import get_all_deals
from database import DealDatabase
from services import telegram_service, geniuslink_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GiftCardDealBot:
    def __init__(self):
        """Initializes the bot and database."""
        # Initialize database
        self.db = DealDatabase()

    def fetch_all_deals(self) -> List[Dict]:
        """Fetch gift card deals from all sources using the scraper"""
        try:
            deals = get_all_deals(['raise', 'cardcash'])
            logger.info(f"Fetched {len(deals)} total deals from all sources")
            return deals
        except Exception as e:
            logger.error(f"Error fetching deals: {e}")
            return []

    def filter_deals(self, deals: List[Dict], min_discount: float = 15.0) -> List[Dict]:
        """Filter deals by minimum discount percentage and remove duplicates"""
        # First filter by discount percentage
        filtered_deals = []
        for deal in deals:
            discount_percent = deal.get('discount_percent', 0)
            if discount_percent >= min_discount:
                filtered_deals.append(deal)
        
        # Then filter out duplicates using database
        new_deals = self.db.filter_new_deals(filtered_deals)
        
        logger.info(f"Filtered {len(deals)} deals to {len(filtered_deals)} with ≥{min_discount}% discount, {len(new_deals)} are new")
        return new_deals

    def format_deal_message(self, deal: Dict, is_premium: bool = False) -> str:
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
            f"🔗 [**Buy Now**]({short_url})"
        )

        # Optional: Add expiration time if available in the deal data
        # expiration = deal.get('expires_at')
        # if expiration:
        #     message += f"\n⏰ *Expires: {expiration}*"

        return message

    def process_deals(self):
        """Main function to process and post deals"""
        logger.info("Starting deal processing...")

        deals_posted = 0
        premium_deals_posted = 0
        errors = []

        try:
            # Fetch deals from all sources
            all_deals = self.fetch_all_deals()
            logger.info(f"Found {len(all_deals)} total deals")

            # Filter deals by discount threshold (this also removes duplicates)
            filtered_deals = self.filter_deals(all_deals, min_discount=15.0)
            premium_deals = self.filter_deals(all_deals, min_discount=25.0)

            logger.info(f"Found {len(filtered_deals)} new deals with 15%+ discount")
            logger.info(f"Found {len(premium_deals)} new premium deals with 25%+ discount")

            # Process regular deals
            for deal in filtered_deals:
                try:
                    message = self.format_deal_message(deal)
                    if telegram_service.send_message(message, config.telegram_channel_id):
                        # Mark deal as posted in database
                        if self.db.mark_deal_as_posted(deal):
                            deals_posted += 1
                            logger.info(f"Posted deal: {deal.get('merchant', 'Unknown')}")
                        time.sleep(1)  # Rate limiting
                except Exception as e:
                    error_msg = f"Error posting deal {deal.get('merchant', 'Unknown')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Process premium deals (if premium channel is configured)
            if config.telegram_premium_channel_id:
                for deal in premium_deals:
                    try:
                        message = self.format_deal_message(deal, is_premium=True)

                        if telegram_service.send_message(message, config.telegram_premium_channel_id):
                            # Mark deal as posted in database
                            if self.db.mark_deal_as_posted(deal):
                                premium_deals_posted += 1
                                logger.info(f"Posted premium deal: {deal.get('merchant', 'Unknown')}")
                            time.sleep(1)  # Rate limiting
                    except Exception as e:
                        error_msg = f"Error posting premium deal {deal.get('merchant', 'Unknown')}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)

            # Log execution statistics
            status = 'success' if not errors else ('partial' if deals_posted > 0 else 'error')
            error_summary = '; '.join(errors[:3]) if errors else None  # Limit error message length

            self.db.log_bot_execution(
                deals_found=len(all_deals),
                deals_posted=deals_posted,
                premium_deals_posted=premium_deals_posted,
                errors=error_summary,
                status=status
            )

            logger.info(f"Deal processing completed: {deals_posted} regular, {premium_deals_posted} premium deals posted")

        except Exception as e:
            error_msg = f"Critical error in deal processing: {e}"
            logger.error(error_msg)
            self.db.log_bot_execution(
                deals_found=0,
                deals_posted=0,
                premium_deals_posted=0,
                errors=error_msg,
                status='error'
            )

def main():
    """Main entry point"""
    bot = GiftCardDealBot()
    bot.process_deals()

if __name__ == "__main__":
    main()
