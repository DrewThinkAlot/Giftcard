#!/usr/bin/env python3
"""
Database-Driven Deal Turnover Monitor
Tracks how often deals appear and disappear on CardCash and GCX
using Supabase database for storage instead of JSON files.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
from collections import defaultdict
import hashlib
import os
from dotenv import load_dotenv
from supabase import create_client, Client

from scraper import get_all_deals

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseDealMonitor:
    def __init__(self):
        """Initialize the database-driven deal monitor."""
        # No need to load any JSON files - data is in the database
        pass
    
    def create_deal_hash(self, deal: Dict) -> str:
        """Create a unique hash for a deal"""
        # Use merchant, face_value, price, and source to create unique identifier
        deal_string = f"{deal.get('source', '')}-{deal.get('merchant', '')}-{deal.get('face_value', 0)}-{deal.get('price', 0)}"
        return hashlib.md5(deal_string.encode()).hexdigest()[:12]
    
    def run_monitoring_session(self, duration_minutes: int = 60, check_interval_minutes: int = 10):
        """Run a monitoring session to track deal changes using database storage"""
        logger.info(f"Starting {duration_minutes}-minute monitoring session with {check_interval_minutes}-minute intervals")
        
        session_id = datetime.now().isoformat()
        
        # Create session record in database
        session_data = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "duration_minutes": duration_minutes,
            "check_interval_minutes": check_interval_minutes,
        }
        supabase.table("monitoring_sessions").upsert(session_data).execute()
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        check_count = 0
        
        while datetime.now() < end_time:
            check_count += 1
            logger.info(f"Taking snapshot {check_count}...")
            
            # Get current deals
            current_deals = get_all_deals(['raise', 'cardcash'])
            
            # Create snapshot record
            snapshot_data = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "check_number": check_count,
            }
            
            # Insert snapshot and get its ID
            snapshot_response = supabase.table("snapshots").insert(snapshot_data).execute()
            if not snapshot_response.data:
                logger.error("Failed to create snapshot record")
                continue
                
            snapshot_id = snapshot_response.data[0]['id']
            
            # Process each deal
            gcx_count = 0
            cardcash_count = 0
            
            for deal in current_deals:
                deal_hash = self.create_deal_hash(deal)
                
                # Update deal record or create if it doesn't exist
                deal_data = {
                    "hash": deal_hash,
                    "merchant": deal.get('merchant', 'Unknown'),
                    "face_value": deal.get('face_value', 0),
                    "price": deal.get('price', 0),
                    "discount_percent": deal.get('discount_percent', 0),
                    "url": deal.get('url', ''),
                    "source": deal.get('source', '')
                }
                
                # Check if deal exists in database
                deal_response = supabase.table("deals").select("*").eq("hash", deal_hash).execute()
                
                if not deal_response.data:
                    # New deal - create record with first_seen
                    deal_data["first_seen"] = datetime.now().isoformat()
                    deal_data["last_seen"] = datetime.now().isoformat()
                    deal_data["appearances"] = 1
                    supabase.table("deals").insert(deal_data).execute()
                else:
                    # Update existing deal's last_seen time and increment appearances
                    supabase.table("deals").update({
                        "last_seen": datetime.now().isoformat(),
                        "appearances": deal_response.data[0]['appearances'] + 1
                    }).eq("hash", deal_hash).execute()
                
                # Link deal to snapshot
                supabase.table("snapshot_deals").upsert({
                    "snapshot_id": snapshot_id,
                    "deal_hash": deal_hash
                }).execute()
                
                # Count by source
                if deal.get('source') == 'raise':
                    gcx_count += 1
                elif deal.get('source') == 'cardcash':
                    cardcash_count += 1
            
            logger.info(f"Snapshot {check_count} complete: {gcx_count} GCX deals, {cardcash_count} CardCash deals")
            
            # Sleep until next check
            if datetime.now() < end_time:
                sleep_time = check_interval_minutes * 60
                logger.info(f"Sleeping for {check_interval_minutes} minutes...")
                time.sleep(sleep_time)
    
    def analyze_session(self, session_id: str):
        """Analyze a monitoring session for deal turnover patterns using database data"""
        logger.info(f"Analyzing session {session_id}...")
        
        # Get session details
        session_response = supabase.table("monitoring_sessions").select("*").eq("session_id", session_id).execute()
        if not session_response.data:
            logger.error(f"Session {session_id} not found")
            return None
        
        session = session_response.data[0]
        
        # Get all snapshots for this session
        snapshots_response = supabase.table("snapshots").select("*").eq("session_id", session_id).order("check_number").execute()
        if not snapshots_response.data:
            logger.error(f"No snapshots found for session {session_id}")
            return None
        
        snapshots = snapshots_response.data
        
        # Track deals by source
        gcx_deals_timeline = {}
        cardcash_deals_timeline = {}
        
        for snapshot in snapshots:
            snapshot_id = snapshot['id']
            
            # Get deals in this snapshot
            deals_response = supabase.from_("snapshot_deals").select(
                "deals(*)"
            ).eq("snapshot_id", snapshot_id).execute()
            
            if not deals_response.data:
                continue
            
            # Record presence in timeline
            for item in deals_response.data:
                deal = item['deals']
                if not deal:
                    continue
                
                deal_hash = deal['hash']
                source = deal['source']
                check_num = snapshot['check_number']
                
                if source == 'raise':
                    if deal_hash not in gcx_deals_timeline:
                        gcx_deals_timeline[deal_hash] = []
                    gcx_deals_timeline[deal_hash].append(check_num)
                elif source == 'cardcash':
                    if deal_hash not in cardcash_deals_timeline:
                        cardcash_deals_timeline[deal_hash] = []
                    cardcash_deals_timeline[deal_hash].append(check_num)
        
        # Calculate statistics
        num_snapshots = len(snapshots)
        interval_minutes = session['check_interval_minutes']
        
        gcx_stats = self._calculate_turnover_stats(gcx_deals_timeline, num_snapshots, interval_minutes, 'raise')
        cardcash_stats = self._calculate_turnover_stats(cardcash_deals_timeline, num_snapshots, interval_minutes, 'cardcash')
        
        # Generate recommendations
        recommendations = self.recommend_scraping_frequency(gcx_stats, cardcash_stats)
        
        return {
            "session_id": session_id,
            "gcx_stats": gcx_stats,
            "cardcash_stats": cardcash_stats,
            "recommendations": recommendations
        }
    
    @staticmethod
    def _calculate_turnover_stats(deal_timeline: Dict, num_snapshots: int, interval_minutes: float, source_name: str):
        """Calculate turnover statistics for a given deal timeline."""
        total_deals = len(deal_timeline)
        if total_deals == 0:
            return {"total_deals_seen": 0}
        
        # Calculate statistics
        deal_lifespans = []
        disappeared_deals = 0
        
        for deal_hash, appearances in deal_timeline.items():
            # Sort appearance check numbers
            appearances.sort()
            
            # Calculate lifespan in check intervals
            if len(appearances) < 2:
                continue
                
            first_seen = appearances[0]
            last_seen = appearances[-1]
            
            # If the deal wasn't seen in the last snapshot, it disappeared
            if last_seen < num_snapshots:
                disappeared_deals += 1
            
            # Calculate lifespan in check intervals
            lifespan_checks = last_seen - first_seen + 1
            
            # Convert to minutes
            lifespan_minutes = lifespan_checks * interval_minutes
            deal_lifespans.append(lifespan_minutes)
        
        # Calculate average lifespan
        if deal_lifespans:
            avg_lifetime_minutes = sum(deal_lifespans) / len(deal_lifespans)
        else:
            avg_lifetime_minutes = 0
        
        # Calculate turnover rate
        if total_deals > 0:
            turnover_rate = disappeared_deals / total_deals
        else:
            turnover_rate = 0
            
        logger.info(f"{source_name} Stats: {total_deals} deals, {disappeared_deals} disappeared, "
                   f"{avg_lifetime_minutes:.1f} min avg lifetime, {turnover_rate:.2f} turnover rate")
        
        return {
            "total_deals_seen": total_deals,
            "disappeared_deals": disappeared_deals,
            "turnover_rate": turnover_rate,
            "avg_lifetime_minutes": avg_lifetime_minutes
        }
    
    def recommend_scraping_frequency(self, gcx_stats: Dict, cardcash_stats: Dict):
        """Provide scraping frequency recommendations based on turnover analysis"""
        logger.info("\n" + "="*50)
        logger.info("SCRAPING FREQUENCY RECOMMENDATIONS")
        logger.info("="*50)
        
        def get_recommendation(stats: Dict, source_name: str):
            avg_lifetime = stats.get("avg_lifetime_minutes", 0)
            turnover_rate = stats.get("turnover_rate", 0)
            
            if avg_lifetime == 0:
                return f"{source_name}: No data available"
            
            # Recommendation logic
            if avg_lifetime < 30:
                freq = "Every 10-15 minutes"
                reason = "Very high turnover - deals disappear quickly"
            elif avg_lifetime < 60:
                freq = "Every 20-30 minutes"
                reason = "High turnover - frequent checking needed"
            elif avg_lifetime < 120:
                freq = "Every 30-60 minutes"
                reason = "Moderate turnover - hourly checking sufficient"
            elif avg_lifetime < 240:
                freq = "Every 1-2 hours"
                reason = "Low turnover - less frequent checking okay"
            else:
                freq = "Every 2-4 hours"
                reason = "Very low turnover - deals stay available longer"
            
            return f"{source_name}: {freq} ({reason})"
        
        gcx_rec = get_recommendation(gcx_stats, "GCX")
        cardcash_rec = get_recommendation(cardcash_stats, "CardCash")
        
        logger.info(gcx_rec)
        logger.info(cardcash_rec)
        
        # Overall recommendation
        min_lifetime = min(
            gcx_stats.get("avg_lifetime_minutes", float('inf')),
            cardcash_stats.get("avg_lifetime_minutes", float('inf'))
        )
        
        if min_lifetime < 60:
            overall_rec = "Every 30 minutes"
        elif min_lifetime < 120:
            overall_rec = "Every 1 hour"
        else:
            overall_rec = "Every 2 hours"
        
        logger.info(f"\nOVERALL RECOMMENDATION: {overall_rec}")
        logger.info("="*50)
        
        # Return structured recommendation data
        return {
            "minutes": self._extract_minutes_from_recommendation(overall_rec),
            "recommendation": overall_rec,
            "confidence": "high" if min_lifetime != float('inf') else "low",
            "reasoning": f"Based on minimum average lifetime of {min_lifetime:.1f} minutes",
            "gcx_recommendation": gcx_rec,
            "cardcash_recommendation": cardcash_rec
        }
    
    def _extract_minutes_from_recommendation(self, recommendation: str) -> int:
        """Extract numeric minutes from recommendation string"""
        if "30 minutes" in recommendation:
            return 30
        elif "1 hour" in recommendation:
            return 60
        elif "2 hours" in recommendation:
            return 120
        else:
            return 60  # Default fallback
    
    def quick_analysis(self, samples: int = 3, interval_minutes: int = 30):
        """Run a quick analysis with fewer samples"""
        logger.info(f"Running quick analysis: {samples} samples, {interval_minutes} minutes apart")
        self.run_monitoring_session(
            duration_minutes=samples * interval_minutes,
            check_interval_minutes=interval_minutes
        )


def main():
    """Main function to run deal monitoring"""
    monitor = DatabaseDealMonitor()
    
    # Quick analysis (3 samples, 30 minutes apart = 1 hour total)
    logger.info("Starting quick deal turnover analysis...")
    monitor.quick_analysis(samples=3, interval_minutes=30)
    
    # For more comprehensive analysis, uncomment:
    # monitor.run_monitoring_session(duration_minutes=240, check_interval_minutes=30)  # 4 hours, every 30 min


if __name__ == "__main__":
    main()
