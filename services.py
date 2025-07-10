#!/usr/bin/env python3
"""
External service integrations for the Telegram Gift Card Deal Bot.
Handles interactions with Telegram and Geniuslink APIs.
"""

import os
import logging
import requests
from typing import Optional

from config import config

logger = logging.getLogger(__name__)

class TelegramService:
    """A service for sending messages to Telegram channels."""
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_message(self, message: str, channel_id: str) -> bool:
        """Sends a message to a specified Telegram channel."""
        if not self.bot_token or not channel_id:
            logger.error("Telegram bot token or channel ID is not configured.")
            return False
        
        payload = {
            'chat_id': channel_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Message sent to Telegram channel: {channel_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

class GeniuslinkService:
    """A service for shortening URLs using the Geniuslink API."""
    def __init__(self, api_key: str, api_secret: str, group_id: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = "https://api.geni.us/v3/shorturls"
        self.group_id = group_id or "1"  # Default group ID if none provided

    def shorten_url(self, url: str) -> Optional[str]:
        """Shortens a URL using the Geniuslink API."""
        if not self.api_key or not self.api_secret:
            logger.warning("Geniuslink credentials not found. Returning original URL.")
            return url

        headers = {
            'X-Api-Key': self.api_key,
            'X-Api-Secret': self.api_secret,
            'Content-Type': 'application/json'
        }
        # Add group ID to payload for v3 API requirement
        payload = {
            'Url': url,
            'GroupId': self.group_id,
            'DomainId': getattr(config, 'geniuslink_domain_id', '1'),  # Default domain ID
            'AutoTagAllLinks': True
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 201:
                short_url = response.json().get('ShortUrl')
                logger.info(f"Successfully shortened URL: {url} -> {short_url}")
                return short_url
            else:
                logger.warning(f"Geniuslink API returned status {response.status_code}: {response.text}")
                return url
        except requests.exceptions.RequestException as e:
            logger.error(f"Error shortening link with Geniuslink: {e}")
            return url

# Instantiate services with config
# Instantiate services with config values, provide fallbacks for testing
telegram_token = getattr(config, 'telegram_bot_token', None) or os.environ.get('TELEGRAM_BOT_TOKEN', '')
geniuslink_key = getattr(config, 'geniuslink_api_key', None) or os.environ.get('GENIUSLINK_API_KEY', '')
geniuslink_secret = getattr(config, 'geniuslink_secret', None) or os.environ.get('GENIUSLINK_SECRET', '')
geniuslink_group = getattr(config, 'geniuslink_group_id', None) or os.environ.get('GENIUSLINK_GROUP_ID', '1')

telegram_service = TelegramService(telegram_token)
geniuslink_service = GeniuslinkService(geniuslink_key, geniuslink_secret, geniuslink_group)
