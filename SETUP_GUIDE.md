# Telegram Gift Card Deal Bot - Setup Guide

## Overview
This bot scrapes gift card deals from CardCash.com and GCX (Raise.com), filters for deals with 15%+ discounts, and posts formatted messages to Telegram channels. It includes duplicate prevention, affiliate link shortening, and premium deal filtering.

## Current Status ✅
- ✅ Web scraping (CardCash.com working, finding ~28 deals)
- ✅ Deal filtering (≥15% discount threshold)
- ✅ Message formatting with emojis and markdown
- ✅ Database integration (Supabase) - code ready
- ✅ Geniuslink integration - code ready
- ✅ Telegram posting - code ready
- ✅ Duplicate prevention - code ready

## Prerequisites

### 1. Supabase Database Setup
1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to SQL Editor and run the schema from `database_setup.sql`
4. Get your project URL and anon key from Settings > API

### 2. Telegram Bot Setup
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Save the bot token
4. Create your public channel and add the bot as admin
5. (Optional) Create a premium channel for deals ≥25% off
6. Get channel IDs using [@userinfobot](https://t.me/userinfobot)

### 3. Geniuslink Setup (Optional but Recommended)
1. Sign up at [geniuslink.com](https://geniuslink.com)
2. Get your API key and secret from the dashboard
3. This enables affiliate link shortening and tracking

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the project root:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=@your_public_channel
TELEGRAM_PREMIUM_CHANNEL_ID=@your_premium_channel  # Optional

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here

# Geniuslink Configuration (Optional)
GENIUSLINK_API_KEY=your_api_key_here
GENIUSLINK_SECRET=your_secret_here
```

### 3. Database Setup
Run the SQL schema in your Supabase project:
```bash
# Copy the contents of database_setup.sql and run in Supabase SQL Editor
```

## Testing

### 1. Test Scraper Only
```bash
python test_scraper.py
```

### 2. Test Bot Integration
```bash
python test_bot_integration.py
```

### 3. Test Complete Integration
```bash
python test_complete_integration.py
```

### 4. Test Single Run (No Posting)
```bash
python main.py --dry-run  # If implemented
```

## Deployment Options

### Option 1: Replit (Recommended for Beginners)
1. Import this project to Replit
2. Set environment variables in Replit Secrets
3. Use Replit's Always On feature for 24/7 operation
4. Set up a cron job or use Replit's scheduler

### Option 2: Railway
1. Connect your GitHub repo to Railway
2. Set environment variables in Railway dashboard
3. Deploy with automatic scaling

### Option 3: Heroku
1. Create a new Heroku app
2. Set config vars for environment variables
3. Use Heroku Scheduler add-on for cron jobs

### Option 4: VPS/Cloud Server
1. Set up a Linux server (Ubuntu/Debian)
2. Install Python 3.8+
3. Set up systemd service for auto-restart
4. Use cron for scheduling

## Scheduling

### Cron Job Example (Every 5 minutes)
```bash
# Edit crontab
crontab -e

# Add this line
*/5 * * * * cd /path/to/telegram-deal-bot && python main.py >> logs/bot.log 2>&1
```

### Systemd Service Example
```ini
# /etc/systemd/system/deal-bot.service
[Unit]
Description=Telegram Gift Card Deal Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram-deal-bot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

## Monitoring and Maintenance

### 1. Check Logs
```bash
# View recent bot executions
tail -f logs/bot.log

# Check database for execution history
# Query bot_executions table in Supabase
```

### 2. Monitor Deal Quality
- Check `merchant_stats` table for popular merchants
- Monitor `posted_deals` table for deal frequency
- Adjust discount thresholds if needed

### 3. Update Scrapers
- Websites may change their HTML structure
- Monitor scraper success rates
- Update CSS selectors in `scraper.py` as needed

## Troubleshooting

### Common Issues

1. **No deals found**
   - Check if websites changed their structure
   - Verify scraper selectors are still valid
   - Check network connectivity

2. **Duplicate deals posting**
   - Verify Supabase connection
   - Check `posted_deals` table
   - Ensure deal hashing is working

3. **Telegram posting fails**
   - Verify bot token and channel IDs
   - Check if bot is admin in channels
   - Verify message formatting (Markdown)

4. **Database errors**
   - Check Supabase credentials
   - Verify database schema is set up
   - Check network connectivity

### Debug Mode
Set logging level to DEBUG in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimization

### 1. Rate Limiting
- Current: 1-second delay between posts
- Adjust in `main.py` if needed

### 2. Database Cleanup
- Old deals are cleaned up automatically
- Adjust retention period in `database.py`

### 3. Scraping Efficiency
- Current: 2-second delay between sites
- Adjust in `scraper.py` if needed

## Security Best Practices

1. **Environment Variables**
   - Never commit `.env` file
   - Use secure credential storage in production

2. **API Keys**
   - Rotate keys regularly
   - Monitor API usage

3. **Database Access**
   - Use Row Level Security in Supabase
   - Limit database permissions

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Test individual components
4. Check if external services (websites) have changed

## License
This project is for educational purposes. Ensure compliance with website terms of service and applicable laws when scraping.
