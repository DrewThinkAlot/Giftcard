#!/usr/bin/env python3
"""
Database Integration Test for Telegram Deal Bot
Tests the full pipeline with the database-driven monitoring and dashboard.
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import GiftCardDealBot
from database_monitor import DatabaseDealMonitor
from database_dashboard import DatabaseTurnoverDashboard
from adaptive_scraper import AdaptiveScraper
from scraper import get_all_deals
from database import DealDatabase
from services import telegram_service, geniuslink_service
# from unified_monitor import UnifiedMonitor  # No longer needed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseIntegrationTest:
    """Test class for database-driven monitoring integration"""
    
    def __init__(self, test_mode=True):
        """Initialize test components"""
        self.test_mode = test_mode
        self.deal_bot = GiftCardDealBot()
        self.db = DealDatabase()
        self.db_monitor = DatabaseDealMonitor()
        self.db_dashboard = DatabaseTurnoverDashboard()
        self.adaptive_scraper = AdaptiveScraper()
    
    def test_monitoring(self, duration_minutes=10, interval_minutes=2):
        """Test the database-driven monitoring functionality"""
        logger.info(f"Testing monitoring for {duration_minutes} minutes with {interval_minutes}-minute intervals")
        
        self.db_monitor.run_monitoring_session(
            duration_minutes=duration_minutes,
            check_interval_minutes=interval_minutes
        )
        
        # Generate reports
        self.db_dashboard.generate_reports()
        
        return True
    
    def test_adaptive_scraping(self, iterations=2, base_interval=2):
        """Test adaptive scraping with the database-driven monitor"""
        logger.info(f"Testing adaptive scraping with {iterations} iterations")
        
        for i in range(iterations):
            logger.info(f"Iteration {i+1}/{iterations}")
            
            # Quick monitoring to get data
            self.db_monitor.quick_analysis(samples=2, interval_minutes=base_interval)
            
            # Wait between iterations
            if i < iterations - 1:
                logger.info(f"Waiting {base_interval} minutes before next iteration...")
                time.sleep(base_interval * 60)
        
        return True
    
    def test_full_pipeline(self, scraping_iterations=1, post_deals=False):
        """Test the full pipeline with adaptive scraping and database-driven monitoring"""
        logger.info("Testing full pipeline integration")
        
        # Step 1: Run monitoring to collect data
        self.test_monitoring(duration_minutes=5, interval_minutes=1)
        
        # Step 2: Run adaptive scraping based on monitoring data
        self.test_adaptive_scraping(iterations=scraping_iterations)
        
        # Step 3: Process and optionally post deals
        if post_deals:
            logger.info("Processing and posting deals")
            self.deal_bot.process_deals()
        else:
            logger.info("Skipping deal posting (test mode)")
            
            # Just fetch and filter deals without posting
            all_deals = self.deal_bot.fetch_all_deals()
            filtered_deals = self.deal_bot.filter_deals(all_deals)
            logger.info(f"Found {len(filtered_deals)} new deals to post (not actually posting)")
        
        return True


def main():
    """Main entry point for the integration test"""
    parser = argparse.ArgumentParser(description='Test database integration')
    
    parser.add_argument('--mode', choices=['monitoring', 'adaptive', 'full'], default='full',
                      help='Test mode: monitoring, adaptive scraping, or full pipeline')
    parser.add_argument('--post', action='store_true',
                      help='Actually post deals to Telegram (use with caution)')
    parser.add_argument('--duration', type=int, default=10,
                      help='Duration in minutes for monitoring test')
    parser.add_argument('--interval', type=int, default=2,
                      help='Check interval in minutes for monitoring test')
    parser.add_argument('--iterations', type=int, default=2,
                      help='Number of iterations for adaptive scraping test')
    
    args = parser.parse_args()
    
    # Run the selected test
    test = DatabaseIntegrationTest(test_mode=not args.post)
    
    if args.mode == 'monitoring':
        test.test_monitoring(duration_minutes=args.duration, interval_minutes=args.interval)
    elif args.mode == 'adaptive':
        test.test_adaptive_scraping(iterations=args.iterations, base_interval=args.interval)
    else:  # full
        test.test_full_pipeline(scraping_iterations=args.iterations, post_deals=args.post)
    
    logger.info("Test run completed successfully")


if __name__ == "__main__":
    main()
