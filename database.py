#!/usr/bin/env python3
"""
Database operations for the Telegram Gift Card Deal Bot
Handles Supabase integration for duplicate checking and deal storage
"""

import os
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set
from supabase import create_client, Client

from config import config

logger = logging.getLogger(__name__)

class DealDatabase:
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = config.supabase_url
        self.supabase_key = config.supabase_key
        
        if self.supabase_url and self.supabase_key:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized successfully")
        else:
            logger.warning("Supabase credentials not found. Database operations will be disabled.")
            self.supabase = None
    
    def generate_deal_hash(self, deal: Dict) -> str:
        """Generate a unique hash for a deal to prevent duplicates"""
        # Create a unique identifier based on merchant, discount, and source
        deal_key = f"{deal['merchant']}_{deal['discount_percent']:.1f}_{deal['source']}_{deal.get('face_value', 0)}"
        return hashlib.md5(deal_key.encode()).hexdigest()
    
    def is_deal_posted(self, deal: Dict) -> bool:
        """Check if a deal has already been posted"""
        if not self.supabase:
            logger.warning("Supabase not available, skipping duplicate check")
            return False
        
        try:
            deal_hash = self.generate_deal_hash(deal)
            
            response = self.supabase.table('posted_deals').select('id').eq('deal_hash', deal_hash).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking if deal is posted: {e}")
            return False
    
    def get_posted_deal_hashes(self, hours_back: int = 24) -> Set[str]:
        """Get all deal hashes posted in the last N hours"""
        if not self.supabase:
            return set()
        
        try:
            # Calculate timestamp for N hours ago
            from datetime import timedelta
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            response = self.supabase.table('posted_deals').select('deal_hash').gte('posted_at', cutoff_time.isoformat()).execute()
            
            return {row['deal_hash'] for row in response.data}
            
        except Exception as e:
            logger.error(f"Error getting posted deal hashes: {e}")
            return set()
    
    def mark_deal_as_posted(self, deal: Dict) -> bool:
        """Mark a deal as posted to prevent duplicates"""
        if not self.supabase:
            logger.warning("Supabase not available, skipping deal storage")
            return False
        
        try:
            deal_hash = self.generate_deal_hash(deal)
            
            deal_record = {
                'deal_hash': deal_hash,
                'merchant': deal['merchant'],
                'face_value': float(deal['face_value']),
                'price': float(deal['price']),
                'discount_percent': float(deal['discount_percent']),
                'url': deal.get('url', ''),
                'source': deal['source'],
                'posted_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table('posted_deals').insert(deal_record).execute()
            
            if response.data:
                logger.info(f"Deal marked as posted: {deal['merchant']} ({deal['discount_percent']:.1f}% off)")
                return True
            else:
                logger.error("Failed to mark deal as posted - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error marking deal as posted: {e}")
            return False
    
    def filter_new_deals(self, deals: List[Dict]) -> List[Dict]:
        """Filter out deals that have already been posted"""
        if not self.supabase:
            logger.warning("Supabase not available, returning all deals")
            return deals
        
        try:
            # Get all posted deal hashes from the last 24 hours
            posted_hashes = self.get_posted_deal_hashes(hours_back=24)
            
            new_deals = []
            for deal in deals:
                deal_hash = self.generate_deal_hash(deal)
                if deal_hash not in posted_hashes:
                    new_deals.append(deal)
                else:
                    logger.debug(f"Skipping duplicate deal: {deal['merchant']} ({deal['discount_percent']:.1f}% off)")
            
            logger.info(f"Filtered {len(deals)} deals down to {len(new_deals)} new deals")
            return new_deals
            
        except Exception as e:
            logger.error(f"Error filtering new deals: {e}")
            return deals  # Return all deals if filtering fails
    
    def log_bot_execution(self, deals_found: int, deals_posted: int, premium_deals_posted: int = 0, errors: str = None, status: str = 'success') -> bool:
        """Log bot execution statistics"""
        if not self.supabase:
            return False
        
        try:
            execution_record = {
                'execution_time': datetime.now(timezone.utc).isoformat(),
                'deals_found': deals_found,
                'deals_posted': deals_posted,
                'premium_deals_posted': premium_deals_posted,
                'errors': errors,
                'status': status
            }
            
            response = self.supabase.table('bot_executions').insert(execution_record).execute()
            
            if response.data:
                logger.info(f"Bot execution logged: {deals_found} found, {deals_posted} posted")
                return True
            else:
                logger.error("Failed to log bot execution")
                return False
                
        except Exception as e:
            logger.error(f"Error logging bot execution: {e}")
            return False
    
    def update_merchant_stats(self, deal: Dict) -> bool:
        """Update merchant statistics (optional analytics)"""
        if not self.supabase:
            return False
        
        try:
            merchant = deal['merchant']
            discount = float(deal['discount_percent'])
            
            # Check if merchant exists
            response = self.supabase.table('merchant_stats').select('*').eq('merchant', merchant).execute()
            
            if response.data:
                # Update existing merchant
                existing = response.data[0]
                new_total = existing['total_deals'] + 1
                new_avg = ((existing['avg_discount'] * existing['total_deals']) + discount) / new_total
                
                update_data = {
                    'total_deals': new_total,
                    'avg_discount': round(new_avg, 2),
                    'last_seen': datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase.table('merchant_stats').update(update_data).eq('merchant', merchant).execute()
            else:
                # Create new merchant record
                new_record = {
                    'merchant': merchant,
                    'total_deals': 1,
                    'avg_discount': discount,
                    'last_seen': datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase.table('merchant_stats').insert(new_record).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating merchant stats: {e}")
            return False
    
    def get_recent_deals(self, hours_back: int = 24, min_discount: float = 15.0) -> List[Dict]:
        """Get recent deals from the database"""
        if not self.supabase:
            return []
        
        try:
            from datetime import timedelta
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            response = self.supabase.table('posted_deals').select('*').gte('posted_at', cutoff_time.isoformat()).gte('discount_percent', min_discount).order('posted_at', desc=True).execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting recent deals: {e}")
            return []
    
    def cleanup_old_deals(self, days_old: int = 7) -> bool:
        """Clean up old deals from the database to prevent it from growing too large"""
        if not self.supabase:
            return False
        
        try:
            from datetime import timedelta
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            response = self.supabase.table('posted_deals').delete().lt('posted_at', cutoff_time.isoformat()).execute()
            
            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Cleaned up {deleted_count} old deals (older than {days_old} days)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up old deals: {e}")
            return False

if __name__ == "__main__":
    # Test the database operations
    logging.basicConfig(level=logging.INFO)
    
    db = DealDatabase()
    
    # Test deal
    test_deal = {
        'merchant': 'Test Store',
        'face_value': 100.0,
        'price': 85.0,
        'discount_percent': 15.0,
        'source': 'test',
        'url': 'https://example.com'
    }
    
    print(f"Deal hash: {db.generate_deal_hash(test_deal)}")
    print(f"Is posted: {db.is_deal_posted(test_deal)}")
