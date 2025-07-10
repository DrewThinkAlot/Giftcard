#!/usr/bin/env python3
"""
Database-Driven Turnover Dashboard
Generates reports and dashboards for deal turnover statistics
using Supabase database instead of JSON files.
"""

import os
import json
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

from database_monitor import DatabaseDealMonitor

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


class DatabaseTurnoverDashboard:
    """Database-driven dashboard for analyzing deal turnover patterns"""
    
    def __init__(self):
        """Initialize the turnover dashboard."""
        self.monitor = DatabaseDealMonitor()
        self.reports_dir = "reports"
        self.frequency_adjustments_file = "frequency_adjustments.json"
        
        # Ensure directories exist
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Load historical data and frequency adjustments
        self.historical_data = self._load_historical_data()
        self.frequency_adjustments = self._load_frequency_adjustments()
    
    def _load_frequency_adjustments(self):
        """Load frequency adjustment settings from JSON file"""
        try:
            with open(self.frequency_adjustments_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create default frequency adjustments
            default_adjustments = {
                "source_adjustments": {
                    "raise": 1.0,  # No adjustment
                    "cardcash": 1.0  # No adjustment
                },
                "last_updated": datetime.now().isoformat()
            }
            with open(self.frequency_adjustments_file, 'w') as f:
                json.dump(default_adjustments, f, indent=2)
            return default_adjustments
    
    def _save_frequency_adjustments(self):
        """Save frequency adjustments to file"""
        self.frequency_adjustments["last_updated"] = datetime.now().isoformat()
        with open(self.frequency_adjustments_file, 'w') as f:
            json.dump(self.frequency_adjustments, f, indent=2)
    
    def _load_historical_data(self):
        """Load historical data from database"""
        # Query the database for historical data
        # Get the last 30 days of session data
        cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        sessions_response = supabase.table("monitoring_sessions").select("*").gte("start_time", cutoff_date).execute()
        
        if not sessions_response.data:
            logger.info("No historical data found in database")
            return {
                "gcx": {"lifetimes": [], "turnover_rates": []},
                "cardcash": {"lifetimes": [], "turnover_rates": []}
            }
        
        # Process session data
        historical_data = {
            "gcx": {"lifetimes": [], "turnover_rates": []},
            "cardcash": {"lifetimes": [], "turnover_rates": []}
        }
        
        for session in sessions_response.data:
            session_id = session["session_id"]
            
            # For each session, analyze results
            analysis_result = self.monitor.analyze_session(session_id)
            
            if analysis_result:
                gcx_stats = analysis_result.get("gcx_stats", {})
                cardcash_stats = analysis_result.get("cardcash_stats", {})
                
                if gcx_stats.get("avg_lifetime_minutes"):
                    historical_data["gcx"]["lifetimes"].append(gcx_stats["avg_lifetime_minutes"])
                    historical_data["gcx"]["turnover_rates"].append(gcx_stats["turnover_rate"])
                
                if cardcash_stats.get("avg_lifetime_minutes"):
                    historical_data["cardcash"]["lifetimes"].append(cardcash_stats["avg_lifetime_minutes"])
                    historical_data["cardcash"]["turnover_rates"].append(cardcash_stats["turnover_rate"])
        
        logger.info(f"Loaded historical data: {len(historical_data['gcx']['lifetimes'])} GCX records, "
                    f"{len(historical_data['cardcash']['lifetimes'])} CardCash records")
        
        return historical_data
    
    def run_analysis(self, duration_minutes=60, check_interval_minutes=10):
        """Run a new analysis session"""
        logger.info(f"Running {duration_minutes}-minute analysis with {check_interval_minutes}-minute intervals")
        
        # Run monitoring session
        self.monitor.run_monitoring_session(
            duration_minutes=duration_minutes,
            check_interval_minutes=check_interval_minutes
        )
        
        # Reload historical data to include the new session
        self.historical_data = self._load_historical_data()
        
        # Generate reports
        self.generate_reports()
    
    def generate_reports(self):
        """Generate reports and visualizations"""
        logger.info("Generating reports...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create dataframes for analysis
        gcx_df = pd.DataFrame({
            'Lifetime (min)': self.historical_data['gcx']['lifetimes'],
            'Turnover Rate': self.historical_data['gcx']['turnover_rates']
        })
        
        cardcash_df = pd.DataFrame({
            'Lifetime (min)': self.historical_data['cardcash']['lifetimes'],
            'Turnover Rate': self.historical_data['cardcash']['turnover_rates']
        })
        
        # Generate lifetime histogram
        self._generate_lifetime_histogram(gcx_df, cardcash_df, timestamp)
        
        # Generate turnover rate trends
        self._generate_turnover_trend(gcx_df, cardcash_df, timestamp)
        
        # Generate recommendation summary
        self._generate_recommendation_summary(timestamp)
    
    def _generate_lifetime_histogram(self, gcx_df, cardcash_df, timestamp):
        """Generate histogram of deal lifetimes"""
        plt.figure(figsize=(10, 6))
        
        if not gcx_df.empty and not cardcash_df.empty:
            plt.hist([gcx_df['Lifetime (min)'], cardcash_df['Lifetime (min)']], 
                    bins=20, alpha=0.7, label=['GCX', 'CardCash'])
            plt.xlabel('Deal Lifetime (minutes)')
            plt.ylabel('Frequency')
            plt.title('Distribution of Deal Lifetimes')
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Save plot
            output_path = os.path.join(self.reports_dir, f"lifetime_distribution_{timestamp}.png")
            plt.savefig(output_path)
            plt.close()
            logger.info(f"Saved lifetime histogram to {output_path}")
    
    def _generate_turnover_trend(self, gcx_df, cardcash_df, timestamp):
        """Generate trend chart of turnover rates"""
        plt.figure(figsize=(10, 6))
        
        if not gcx_df.empty:
            plt.plot(range(len(gcx_df)), gcx_df['Turnover Rate'], 'b-', label='GCX')
        
        if not cardcash_df.empty:
            plt.plot(range(len(cardcash_df)), cardcash_df['Turnover Rate'], 'r-', label='CardCash')
        
        plt.xlabel('Analysis Session')
        plt.ylabel('Turnover Rate')
        plt.title('Deal Turnover Rate Trends')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Save plot
        output_path = os.path.join(self.reports_dir, f"turnover_trend_{timestamp}.png")
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved turnover trend to {output_path}")
    
    def _generate_recommendation_summary(self, timestamp):
        """Generate a summary of scraping recommendations"""
        # Calculate average metrics
        gcx_avg_lifetime = sum(self.historical_data['gcx']['lifetimes']) / len(self.historical_data['gcx']['lifetimes']) if self.historical_data['gcx']['lifetimes'] else 0
        cardcash_avg_lifetime = sum(self.historical_data['cardcash']['lifetimes']) / len(self.historical_data['cardcash']['lifetimes']) if self.historical_data['cardcash']['lifetimes'] else 0
        
        gcx_avg_turnover = sum(self.historical_data['gcx']['turnover_rates']) / len(self.historical_data['gcx']['turnover_rates']) if self.historical_data['gcx']['turnover_rates'] else 0
        cardcash_avg_turnover = sum(self.historical_data['cardcash']['turnover_rates']) / len(self.historical_data['cardcash']['turnover_rates']) if self.historical_data['cardcash']['turnover_rates'] else 0
        
        # Create recommendation
        recommendations = self.monitor.recommend_scraping_frequency(
            {"avg_lifetime_minutes": gcx_avg_lifetime, "turnover_rate": gcx_avg_turnover},
            {"avg_lifetime_minutes": cardcash_avg_lifetime, "turnover_rate": cardcash_avg_turnover}
        )
        
        # Write summary to file
        summary = f"""
        # Deal Turnover Analysis Summary
        
        ## Analysis Time
        Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        ## Historical Data
        - GCX Records: {len(self.historical_data['gcx']['lifetimes'])}
        - CardCash Records: {len(self.historical_data['cardcash']['lifetimes'])}
        
        ## Average Metrics
        
        ### GCX
        - Average Deal Lifetime: {gcx_avg_lifetime:.1f} minutes
        - Average Turnover Rate: {gcx_avg_turnover:.2f}
        
        ### CardCash
        - Average Deal Lifetime: {cardcash_avg_lifetime:.1f} minutes
        - Average Turnover Rate: {cardcash_avg_turnover:.2f}
        
        ## Recommendations
        
        {recommendations['gcx_recommendation']}
        {recommendations['cardcash_recommendation']}
        
        ### Overall Recommendation
        {recommendations['recommendation']} ({recommendations['reasoning']})
        
        ## Confidence
        Confidence Level: {recommendations['confidence']}
        """
        
        # Save summary
        output_path = os.path.join(self.reports_dir, f"analysis_summary_{timestamp}.md")
        with open(output_path, 'w') as f:
            f.write(summary)
        
        logger.info(f"Saved analysis summary to {output_path}")
        
        # Return the minutes value for scheduling
        return recommendations['minutes']
    
    def adjust_scraping_frequency(self, source: str, factor: float):
        """Adjust scraping frequency for a specific source"""
        if source not in ['raise', 'cardcash']:
            logger.error(f"Invalid source: {source}. Must be 'raise' or 'cardcash'.")
            return
        
        self.frequency_adjustments['source_adjustments'][source] = factor
        self._save_frequency_adjustments()
        logger.info(f"Adjusted {source} frequency by factor {factor}")
    
    def get_adjusted_frequency(self, base_minutes: int, source: str) -> int:
        """Get adjusted frequency for a source based on base recommendation"""
        if source not in self.frequency_adjustments['source_adjustments']:
            return base_minutes
            
        adjustment = self.frequency_adjustments['source_adjustments'][source]
        return max(10, int(base_minutes * adjustment))


def main():
    """Main function to run dashboard"""
    dashboard = DatabaseTurnoverDashboard()
    
    # Run a quick analysis
    logger.info("Running turnover analysis...")
    dashboard.run_analysis(duration_minutes=90, check_interval_minutes=30)
    
    # Example of adjusting frequency for a specific source
    # dashboard.adjust_scraping_frequency('raise', 0.8)  # Increase frequency (0.8 of base minutes = 20% faster)
    # dashboard.adjust_scraping_frequency('cardcash', 1.2)  # Decrease frequency (1.2 of base minutes = 20% slower)


if __name__ == "__main__":
    main()
