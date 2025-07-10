#!/usr/bin/env python3
"""
Adaptive Scraper for Telegram Deal Bot
Automatically adjusts scraping frequency based on deal turnover analysis.
"""

import os
import time
import json
import logging
import threading
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from deal_monitor import DealMonitor
from main import GiftCardDealBot
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.join('logs', 'adaptive_scraper.log'),
    filemode='a'
)
logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

class AdaptiveScraper:
    """
    Adaptive scraper that automatically adjusts scraping frequency
    based on real-time deal turnover analysis.
    """
    
    def __init__(self, initial_frequency_minutes: int = 60):
        """Initialize the adaptive scraper."""
        self.bot = GiftCardDealBot()
        self.monitor = DealMonitor()
        self.current_frequency = initial_frequency_minutes
        self.min_frequency = 10  # Minimum 10 minutes between scrapes
        self.max_frequency = 240  # Maximum 4 hours between scrapes
        self.adjustment_threshold = 5  # Number of scrapes before first adjustment
        self.scrape_count = 0
        self.scrape_history = []
        self.running = False
        self.last_adjustment_time = None
        self.adjustment_log_file = "frequency_adjustments.json"
        self._load_adjustment_history()

    def _load_adjustment_history(self):
        """Load previous frequency adjustment history."""
        try:
            if os.path.exists(self.adjustment_log_file):
                with open(self.adjustment_log_file, 'r') as f:
                    self.adjustment_history = json.load(f)
            else:
                self.adjustment_history = {
                    "adjustments": [],
                    "stats": {
                        "total_adjustments": 0,
                        "increases": 0,
                        "decreases": 0,
                        "last_updated": datetime.now().isoformat()
                    }
                }
        except Exception as e:
            logger.error(f"Error loading adjustment history: {e}")
            self.adjustment_history = {
                "adjustments": [],
                "stats": {
                    "total_adjustments": 0,
                    "increases": 0,
                    "decreases": 0,
                    "last_updated": datetime.now().isoformat()
                }
            }

    def _save_adjustment_history(self):
        """Save frequency adjustment history to file."""
        try:
            with open(self.adjustment_log_file, 'w') as f:
                self.adjustment_history["stats"]["last_updated"] = datetime.now().isoformat()
                json.dump(self.adjustment_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving adjustment history: {e}")

    def set_frequency_bounds(self, min_minutes: int = 10, max_minutes: int = 240):
        """Set the minimum and maximum scraping frequency bounds."""
        self.min_frequency = max(5, min_minutes)  # Absolute minimum of 5 minutes
        self.max_frequency = min(360, max_minutes)  # Absolute maximum of 6 hours
        logger.info(f"Frequency bounds set: min={self.min_frequency}m, max={self.max_frequency}m")

    def adjust_frequency(self, turnover_data: Dict = None):
        """
        Adjust scraping frequency based on deal turnover data.
        If no turnover data is provided, run a quick analysis.
        """
        # Don't adjust until we have enough data points
        if self.scrape_count < self.adjustment_threshold:
            logger.info(f"Not enough scrapes ({self.scrape_count}/{self.adjustment_threshold}) for adjustment yet.")
            return
            
        # Get turnover data if not provided
        if not turnover_data:
            try:
                # Run a quick analysis (3 checks, 10 minutes apart)
                logger.info("Running quick turnover analysis for frequency adjustment...")
                session_data = self.monitor.run_monitoring_session(
                    duration_minutes=30, 
                    check_interval_minutes=10
                )
                turnover_data = self.monitor.analyze_session(session_data)
            except Exception as e:
                logger.error(f"Error running turnover analysis: {e}")
                return

        # Extract metrics from turnover data
        try:
            gcx_stats = turnover_data.get('gcx_stats', {})
            cardcash_stats = turnover_data.get('cardcash_stats', {})
            
            # Calculate weighted turnover rate and lifetime across both platforms
            gcx_turnover = gcx_stats.get('turnover_rate', 0) 
            cardcash_turnover = cardcash_stats.get('turnover_rate', 0)
            avg_turnover = (gcx_turnover + cardcash_turnover) / 2
            
            gcx_lifetime = gcx_stats.get('avg_lifetime_minutes', 120)
            cardcash_lifetime = cardcash_stats.get('avg_lifetime_minutes', 120)
            avg_lifetime = (gcx_lifetime + cardcash_lifetime) / 2
            
            # Apply frequency adjustments based on metrics
            old_frequency = self.current_frequency
            
            # High turnover → more frequent scraping
            # Long lifetime → less frequent scraping
            if avg_turnover > 50:  # Very high turnover (>50% changing)
                self.current_frequency = max(self.min_frequency, min(15, self.current_frequency - 15))
                confidence = "high"
                reason = "very high turnover rate"
            elif avg_turnover > 30:  # High turnover
                self.current_frequency = max(self.min_frequency, min(30, self.current_frequency - 10))
                confidence = "high"
                reason = "high turnover rate"
            elif avg_turnover < 5 and avg_lifetime > 180:  # Very low turnover and long lifetimes
                self.current_frequency = min(self.max_frequency, max(120, self.current_frequency + 20))
                confidence = "high"
                reason = "very low turnover and long deal lifetime"
            elif avg_turnover < 10:  # Low turnover
                self.current_frequency = min(self.max_frequency, self.current_frequency + 10)
                confidence = "medium"
                reason = "low turnover rate"
            elif avg_lifetime < 30:  # Very short-lived deals
                self.current_frequency = max(self.min_frequency, self.current_frequency - 10)
                confidence = "high" 
                reason = "very short deal lifetime"
            else:  # No significant change needed
                confidence = "low"
                reason = "metrics within normal range"
                
            # Ensure frequency stays within bounds
            self.current_frequency = max(self.min_frequency, min(self.max_frequency, self.current_frequency))
            
            # Log the adjustment
            if old_frequency != self.current_frequency:
                logger.info(f"Adjusted frequency: {old_frequency}m → {self.current_frequency}m ({reason})")
                self._log_adjustment(old_frequency, self.current_frequency, reason, confidence, turnover_data)
            else:
                logger.info(f"Frequency unchanged at {self.current_frequency}m ({reason})")
                
            self.last_adjustment_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error during frequency adjustment: {e}")

    def _log_adjustment(self, old_freq: int, new_freq: int, reason: str, confidence: str, metrics: Dict):
        """Log frequency adjustment details."""
        adjustment = {
            "timestamp": datetime.now().isoformat(),
            "old_frequency": old_freq,
            "new_frequency": new_freq,
            "reason": reason,
            "confidence": confidence,
            "metrics": {
                "gcx_turnover": metrics.get("gcx_stats", {}).get("turnover_rate", 0),
                "cardcash_turnover": metrics.get("cardcash_stats", {}).get("turnover_rate", 0),
                "avg_lifetime_minutes": (
                    metrics.get("gcx_stats", {}).get("avg_lifetime_minutes", 0) +
                    metrics.get("cardcash_stats", {}).get("avg_lifetime_minutes", 0)
                ) / 2,
                "scrape_count": self.scrape_count
            }
        }
        
        # Update statistics
        self.adjustment_history["adjustments"].append(adjustment)
        self.adjustment_history["stats"]["total_adjustments"] += 1
        
        if new_freq < old_freq:
            self.adjustment_history["stats"]["increases"] += 1
        else:
            self.adjustment_history["stats"]["decreases"] += 1
            
        self._save_adjustment_history()

    def _scraping_thread(self):
        """Background thread that handles periodic scraping."""
        while self.running:
            try:
                start_time = datetime.now()
                logger.info(f"Starting scheduled scrape (frequency: {self.current_frequency}m)")
                
                # Run the main bot scraping process
                self.bot.process_deals()
                
                # Update scrape statistics
                self.scrape_count += 1
                self.scrape_history.append({
                    "timestamp": start_time.isoformat(),
                    "duration_seconds": (datetime.now() - start_time).total_seconds(),
                    "frequency_minutes": self.current_frequency
                })
                
                # Periodically adjust frequency (every 4 scrapes after threshold)
                if (self.scrape_count >= self.adjustment_threshold and
                        self.scrape_count % 4 == 0):
                    self.adjust_frequency()
                
                # Wait until next scheduled scrape
                elapsed_seconds = (datetime.now() - start_time).total_seconds()
                wait_seconds = max(0, (self.current_frequency * 60) - elapsed_seconds)
                
                logger.info(f"Scrape completed. Next scrape in {wait_seconds/60:.1f} minutes")
                
                # Check periodically if we should stop
                wait_interval = 30  # Check every 30 seconds if we should stop
                for _ in range(int(wait_seconds / wait_interval) + 1):
                    if not self.running:
                        break
                    time.sleep(min(wait_interval, wait_seconds))
                    wait_seconds -= wait_interval
                    
            except Exception as e:
                logger.error(f"Error in scraping thread: {e}")
                time.sleep(60)  # Wait a minute before retrying on error

    def _monitoring_thread(self):
        """Background thread that performs periodic turnover monitoring."""
        # Wait for initial scrapes to complete
        time.sleep(self.current_frequency * 60 * 2)
        
        while self.running:
            try:
                # Run monitoring session every 6 hours
                if (not self.last_adjustment_time or 
                    (datetime.now() - self.last_adjustment_time).total_seconds() / 3600 >= 6):
                    
                    logger.info("Running comprehensive monitoring session...")
                    session_data = self.monitor.run_monitoring_session(
                        duration_minutes=60,
                        check_interval_minutes=15
                    )
                    turnover_data = self.monitor.analyze_session(session_data)
                    self.adjust_frequency(turnover_data)
                
                # Sleep for 3 hours before checking again
                for _ in range(36):  # Check every 5 minutes for 3 hours
                    if not self.running:
                        break
                    time.sleep(300)  # 5 minutes
                    
            except Exception as e:
                logger.error(f"Error in monitoring thread: {e}")
                time.sleep(1800)  # Wait 30 minutes before retrying on error

    def start_adaptive_scraping(self):
        """Start the adaptive scraping process."""
        if self.running:
            logger.warning("Adaptive scraper is already running")
            return
            
        self.running = True
        logger.info(f"Starting adaptive scraper with initial frequency: {self.current_frequency}m")
        
        # Create and start threads
        self.scrape_thread = threading.Thread(target=self._scraping_thread)
        self.scrape_thread.daemon = True
        self.scrape_thread.start()
        
        self.monitor_thread = threading.Thread(target=self._monitoring_thread)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Adaptive scraper started successfully")

    def stop_adaptive_scraping(self):
        """Stop the adaptive scraping process."""
        logger.info("Stopping adaptive scraper...")
        self.running = False
        
        # Wait for threads to terminate
        if hasattr(self, 'scrape_thread') and self.scrape_thread.is_alive():
            self.scrape_thread.join(timeout=60)
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=60)
            
        logger.info("Adaptive scraper stopped")
        
    def get_status(self) -> Dict:
        """Get the current status of the adaptive scraper."""
        return {
            "running": self.running,
            "current_frequency_minutes": self.current_frequency,
            "scrape_count": self.scrape_count,
            "last_adjustment": self.last_adjustment_time.isoformat() if self.last_adjustment_time else None,
            "min_frequency": self.min_frequency,
            "max_frequency": self.max_frequency,
            "adjustment_threshold": self.adjustment_threshold,
            "latest_scrapes": self.scrape_history[-5:] if self.scrape_history else []
        }

def main():
    """Main entry point for the adaptive scraper."""
    parser = argparse.ArgumentParser(description="Adaptive Scraper for Telegram Deal Bot")
    parser.add_argument("--min", type=int, default=10, help="Minimum scraping frequency in minutes (default: 10)")
    parser.add_argument("--max", type=int, default=240, help="Maximum scraping frequency in minutes (default: 240)")
    parser.add_argument("--initial", type=int, default=60, help="Initial scraping frequency in minutes (default: 60)")
    parser.add_argument("--threshold", type=int, default=5, help="Adjustment threshold - scrapes before first adjustment (default: 5)")
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    try:
        # Create and configure adaptive scraper
        scraper = AdaptiveScraper(initial_frequency_minutes=args.initial)
        scraper.set_frequency_bounds(min_minutes=args.min, max_minutes=args.max)
        scraper.adjustment_threshold = args.threshold
        
        # Start adaptive scraping
        scraper.start_adaptive_scraping()
        
        # Keep main thread alive for keyboard interrupt
        print("\nAdaptive scraper running. Press Ctrl+C to stop...\n")
        while True:
            time.sleep(60)
            status = scraper.get_status()
            print(f"\nStatus: Frequency={status['current_frequency_minutes']}m, Scrapes={status['scrape_count']}")
            
    except KeyboardInterrupt:
        print("\nStopping adaptive scraper...")
        if 'scraper' in locals():
            scraper.stop_adaptive_scraping()
        print("Stopped.")
    except Exception as e:
        logger.critical(f"Critical error in adaptive scraper: {e}")
        if 'scraper' in locals():
            scraper.stop_adaptive_scraping()

if __name__ == "__main__":
    main()
