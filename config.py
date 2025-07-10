#!/usr/bin/env python3
"""
Configuration loader for the Telegram Gift Card Deal Bot.
Loads environment variables from a .env file and provides them as a dataclass.
"""

import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class Config:
    """A dataclass to hold all configuration variables from environment variables."""
    telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_channel_id: str = os.getenv('TELEGRAM_CHANNEL_ID')
    telegram_premium_channel_id: str = os.getenv('TELEGRAM_PREMIUM_CHANNEL_ID')
    geniuslink_api_key: str = os.getenv('GENIUSLINK_API_KEY')
    geniuslink_secret: str = os.getenv('GENIUSLINK_SECRET')
    supabase_url: str = os.getenv('SUPABASE_URL')
    supabase_key: str = os.getenv('SUPABASE_ANON_KEY')
    scrapingdog_api_key: str = os.getenv('SCRAPINGDOG_API_KEY')

    def __post_init__(self):
        """Validate that essential variables are set."""
        if not self.telegram_bot_token:
            logger.error("TELEGRAM_BOT_TOKEN is not set.")
            raise ValueError("TELEGRAM_BOT_TOKEN is not set.")
        if not self.telegram_channel_id:
            logger.error("TELEGRAM_CHANNEL_ID is not set.")
            raise ValueError("TELEGRAM_CHANNEL_ID is not set.")
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials are not fully set. Database features will be limited.")
        if not self.scrapingdog_api_key:
            logger.warning("SCRAPINGDOG_API_KEY is not set. Scraping will not work.")

# Create a single instance of the config to be imported by other modules
config = Config()
