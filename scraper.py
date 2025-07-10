#!/usr/bin/env python3
"""
Web scraping module for Raise.com and CardCash.com gift card deals using Scrapingdog.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urljoin

from config import config

logger = logging.getLogger(__name__)

class BaseScraper:
    """Base class for a web scraper using the Scrapingdog API."""
    def __init__(self, start_url: str):
        self.start_url = start_url
        self.api_key = config.scrapingdog_api_key

    def scrape(self) -> List[Dict]:
        """Main scraping method to be called."""
        if not self.api_key:
            logger.error("Scrapingdog API key is not set. Cannot perform scraping.")
            return []

        try:
            logger.info(f"Fetching {self.start_url} via Scrapingdog for {self.__class__.__name__}")
            api_url = f"https://api.scrapingdog.com/scrape?api_key={self.api_key}&url={self.start_url}&dynamic=true"
            response = requests.get(api_url, timeout=90) # Increased timeout for dynamic rendering
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            deals = self.parse_deals(soup)
            logger.info(f"Found {len(deals)} deals from {self.__class__.__name__}.")
            return deals
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred during scraping {self.__class__.__name__}: {e}")
            return []

    def parse_deals(self, soup: BeautifulSoup) -> List[Dict]:
        """Parses deals from a given BeautifulSoup object. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method.")

class RaiseScraper(BaseScraper):
    """Scraper for GCX (Raise.com marketplace)."""
    def __init__(self):
        super().__init__("https://gcx.raise.com/buy-gift-cards")

    def parse_deals(self, soup: BeautifulSoup) -> List[Dict]:
        deals = []
        
        # GCX is a React app, so we need to look for various possible selectors
        # Try multiple selector patterns for deal cards
        possible_selectors = [
            'a[href*="gift-card"]',  # Links containing gift-card
            'div[class*="card"]',    # Divs with card in class name
            'div[data-testid*="card"]', # React test IDs
            '[class*="product"]',    # Product containers
            '[class*="deal"]',       # Deal containers
        ]
        
        cards = []
        for selector in possible_selectors:
            found_cards = soup.select(selector)
            if found_cards:
                logger.info(f"Found {len(found_cards)} potential cards with selector: {selector}")
                cards.extend(found_cards[:20])  # Limit to avoid duplicates
        
        # Remove duplicates
        cards = list(set(cards))
        logger.info(f"Processing {len(cards)} unique card elements from GCX")
        
        for card in cards:
            try:
                deal = self._extract_gcx_deal(card)
                if deal:
                    deals.append(deal)
            except Exception as e:
                logger.debug(f"Could not parse a deal card on GCX: {e}")
                continue
                
        return deals
    
    def _extract_gcx_deal(self, element) -> Dict:
        """Extract deal information from a GCX card element"""
        try:
            # Get all text content for analysis
            element_text = element.get_text(strip=True)
            if not element_text or len(element_text) < 10:
                return None
            
            # Look for merchant name - try various approaches
            merchant = "Unknown"
            
            # Try to find merchant in alt text of images
            img_elem = element.find('img')
            if img_elem and img_elem.get('alt'):
                merchant = img_elem['alt'].strip()
            
            # Try to find merchant in text content
            if merchant == "Unknown":
                # Look for text that might be a merchant name
                text_elements = element.find_all(['span', 'div', 'h1', 'h2', 'h3', 'h4'])
                for elem in text_elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 2 and len(text) < 50:
                        # Skip if it's clearly a price or percentage
                        if not any(char in text for char in ['$', '%', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
                            merchant = text
                            break
            
            # Extract prices using regex
            import re
            prices = re.findall(r'\$(\d+(?:\.\d{2})?)', element_text)
            percentages = re.findall(r'(\d+(?:\.\d+)?)%', element_text)
            
            if not prices and not percentages:
                return None
            
            # Determine face value and price
            face_value = 100.0  # Default assumption
            price = face_value
            discount_percent = 0
            
            if len(prices) >= 2:
                # Multiple prices found - assume first is sale price, second is face value
                price = float(prices[0])
                face_value = float(prices[1])
            elif len(prices) == 1 and percentages:
                # One price and percentage - calculate the other
                price_val = float(prices[0])
                discount_pct = float(percentages[0])
                
                if 'off' in element_text.lower() or 'save' in element_text.lower():
                    # Price is likely face value, calculate sale price
                    face_value = price_val
                    price = face_value * (1 - discount_pct / 100)
                else:
                    # Price is likely sale price, calculate face value
                    price = price_val
                    face_value = price / (1 - discount_pct / 100)
            elif percentages:
                # Only percentage, use default face value
                discount_pct = float(percentages[0])
                price = face_value * (1 - discount_pct / 100)
            
            if face_value > price > 0:
                discount_percent = ((face_value - price) / face_value) * 100
                
                # Find URL
                url = ''
                if element.name == 'a' and element.get('href'):
                    url = urljoin(self.start_url, element['href'])
                else:
                    link_elem = element.find('a', href=True)
                    if link_elem:
                        url = urljoin(self.start_url, link_elem['href'])
                
                return {
                    'source': 'GCX',
                    'merchant': merchant,
                    'face_value': face_value,
                    'price': price,
                    'discount_percent': discount_percent,
                    'url': url
                }
        
        except Exception as e:
            logger.debug(f"Error extracting GCX deal: {e}")
        
        return None

class CardCashScraper(BaseScraper):
    """Scraper for CardCash.com."""
    def __init__(self):
        super().__init__("https://www.cardcash.com/buy-gift-cards/")

    def parse_deals(self, soup: BeautifulSoup) -> List[Dict]:
        deals = []
        
        # CardCash is also a React app, try multiple selector patterns
        possible_selectors = [
            'a[href*="gift-card"]',     # Links containing gift-card
            'a[href*="discount"]',      # Links containing discount
            'div[class*="card"]',       # Divs with card in class name
            '[class*="discount"]',      # Elements with discount in class
            '[class*="product"]',       # Product containers
            '[class*="item"]',          # Item containers
        ]
        
        cards = []
        for selector in possible_selectors:
            found_cards = soup.select(selector)
            if found_cards:
                logger.info(f"Found {len(found_cards)} potential cards with selector: {selector}")
                cards.extend(found_cards[:20])  # Limit to avoid duplicates
        
        # Remove duplicates
        cards = list(set(cards))
        logger.info(f"Processing {len(cards)} unique card elements from CardCash")
        
        for card in cards:
            try:
                deal = self._extract_cardcash_deal(card)
                if deal:
                    deals.append(deal)
            except Exception as e:
                logger.debug(f"Could not parse a deal card on CardCash: {e}")
                continue
                
        return deals
    
    def _extract_cardcash_deal(self, element) -> Dict:
        """Extract deal information from a CardCash card element"""
        try:
            # Get all text content for analysis
            element_text = element.get_text(strip=True)
            if not element_text or len(element_text) < 5:
                return None
            
            # Look for merchant name
            merchant = "Unknown"
            
            # Try to find merchant in alt text of images
            img_elem = element.find('img')
            if img_elem and img_elem.get('alt'):
                alt_text = img_elem['alt'].strip()
                if alt_text and 'logo' not in alt_text.lower():
                    merchant = alt_text
            
            # Try to find merchant in text content or URL
            if merchant == "Unknown":
                # Look in the URL for merchant name
                if element.name == 'a' and element.get('href'):
                    href = element['href']
                    # Extract merchant from URL patterns like /buy-gift-cards/discount-walmart-cards/
                    import re
                    url_match = re.search(r'/discount-([^-/]+)-cards?/', href)
                    if url_match:
                        merchant = url_match.group(1).title()
                
                # Look for text that might be a merchant name
                if merchant == "Unknown":
                    text_elements = element.find_all(['span', 'div', 'h1', 'h2', 'h3', 'h4', 'p'])
                    for elem in text_elements:
                        text = elem.get_text(strip=True)
                        if text and len(text) > 2 and len(text) < 30:
                            # Skip if it's clearly a price or percentage
                            if not any(char in text for char in ['$', '%']) and not text.replace('.', '').isdigit():
                                merchant = text
                                break
            
            # Extract discount percentage using regex
            import re
            percentages = re.findall(r'(\d+(?:\.\d+)?)%', element_text)
            prices = re.findall(r'\$(\d+(?:\.\d{2})?)', element_text)
            
            if not percentages and not prices:
                return None
            
            # Calculate deal values
            face_value = 100.0  # Default assumption for CardCash
            discount_percent = 0
            
            if percentages:
                # Take the highest discount percentage found
                discount_percent = max(float(p) for p in percentages)
                price = face_value * (1 - discount_percent / 100)
            elif prices:
                # If we have prices but no percentages, estimate
                price_val = float(prices[0])
                if price_val < face_value:
                    price = price_val
                    discount_percent = ((face_value - price) / face_value) * 100
                else:
                    # Price might be face value
                    face_value = price_val
                    price = face_value * 0.95  # Assume 5% discount
                    discount_percent = 5.0
            else:
                return None
            
            # Skip deals with very low discounts (likely not real deals)
            if discount_percent < 1:
                return None
            
            # Find URL
            url = ''
            if element.name == 'a' and element.get('href'):
                url = urljoin(self.start_url, element['href'])
            else:
                link_elem = element.find('a', href=True)
                if link_elem:
                    url = urljoin(self.start_url, link_elem['href'])
            
            return {
                'source': 'CardCash',
                'merchant': merchant,
                'face_value': face_value,
                'price': price,
                'discount_percent': discount_percent,
                'url': url
            }
        
        except Exception as e:
            logger.debug(f"Error extracting CardCash deal: {e}")
        
        return None

def get_all_deals(scrapers: List[str] = ['raise', 'cardcash']) -> List[Dict]:
    """Get deals from all specified sources."""
    all_deals = []
    scraper_map = {
        'raise': RaiseScraper,
        'cardcash': CardCashScraper
    }

    for scraper_name in scrapers:
        if scraper_name in scraper_map:
            scraper_instance = scraper_map[scraper_name]()
            all_deals.extend(scraper_instance.scrape())
        else:
            logger.warning(f"Unknown scraper specified: {scraper_name}")

    logger.info(f"Total deals found from all sources: {len(all_deals)}")
    return all_deals

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    # Test with all scrapers
    deals = get_all_deals()
    print(f"\nFound {len(deals)} total deals.")
    for deal in deals[:10]: # Print first 10 deals
        print(f"- [{deal['source']}] {deal['merchant']}: ${deal['price']:.2f} for ${deal['face_value']:.2f} gift card ({deal['discount_percent']:.2f}% off)")
