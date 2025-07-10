#!/usr/bin/env python3
"""
Flask web server for Replit deployment
Provides an endpoint that can be pinged by external cron services to trigger the bot
"""

import os
from flask import Flask, jsonify
from main import GiftCardDealBot
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Telegram Gift Card Deal Bot is running',
        'endpoints': {
            '/': 'Health check',
            '/trigger': 'Trigger bot execution',
            '/health': 'Detailed health check'
        }
    })

@app.route('/health')
def health():
    """Detailed health check with configuration status"""
    config_status = {
        'telegram_bot_token': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
        'telegram_channel_id': bool(os.getenv('TELEGRAM_CHANNEL_ID')),
        'geniuslink_api_key': bool(os.getenv('GENIUSLINK_API_KEY')),
        'supabase_url': bool(os.getenv('SUPABASE_URL')),
        'supabase_key': bool(os.getenv('SUPABASE_ANON_KEY'))
    }
    
    all_configured = all(config_status.values())
    
    return jsonify({
        'status': 'healthy' if all_configured else 'partially_configured',
        'configuration': config_status,
        'ready_to_run': all_configured
    })

@app.route('/trigger')
def trigger_bot():
    """Trigger the bot to check for deals and post to Telegram"""
    try:
        logger.info("Bot execution triggered via web endpoint")
        bot = GiftCardDealBot()
        bot.process_deals()
        
        return jsonify({
            'status': 'success',
            'message': 'Bot execution completed successfully'
        })
    
    except Exception as e:
        logger.error(f"Error during bot execution: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Bot execution failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
