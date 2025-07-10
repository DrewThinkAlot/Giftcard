# Deployment Guide

## Quick Start Checklist

### 1. Set Up Supabase Database
1. Go to [supabase.com](https://supabase.com) and create a new project
2. In the SQL Editor, run the contents of `database_setup.sql`
3. Get your project URL and anon key from Settings > API

### 2. Create Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command and follow instructions
3. Save the bot token
4. Add your bot to your channel as an admin with post permissions

### 3. Get Geniuslink API Credentials
1. Sign up at [geniuslink.com](https://geniuslink.com)
2. Get your API key from the dashboard
3. Note: You may need to verify the exact API endpoint format

### 4. Deploy to Replit (Recommended)
1. Create a new Python Repl on [replit.com](https://replit.com)
2. Upload all project files
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables in Replit's Secrets tab:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHANNEL_ID` (e.g., @your_channel or -1001234567890)
   - `TELEGRAM_PREMIUM_CHANNEL_ID` (optional)
   - `GENIUSLINK_API_KEY`
   - `GENIUSLINK_SECRET`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
5. Run `python app.py` to start the web server
6. Your Repl will get a URL like `https://your-repl-name.username.repl.co`

### 5. Set Up Automated Execution
1. Go to [cron-job.org](https://cron-job.org) (free)
2. Create a new cron job
3. Set URL to: `https://your-repl-name.username.repl.co/trigger`
4. Set schedule to run every 5 minutes: `*/5 * * * *`
5. Enable the job

## Testing Before Going Live

### Test the Scraper
```bash
python test_scraper.py
```
This will show you what deals are being found and help debug any scraping issues.

### Test the Bot Manually
```bash
python main.py
```
This runs the bot once to test Telegram posting and database operations.

### Test the Web Server
```bash
python app.py
```
Then visit `http://localhost:5000/health` to check configuration status.

## Monitoring and Maintenance

### Check Bot Status
- Visit `/health` endpoint to see configuration status
- Check Supabase dashboard for posted deals
- Monitor Telegram channel for posts

### Common Issues
1. **No deals found**: The scraping selectors may need updating as websites change
2. **Telegram errors**: Check bot token and channel permissions
3. **Database errors**: Verify Supabase credentials and table setup
4. **Geniuslink errors**: Confirm API credentials and endpoint format

### Updating Scraping Logic
The websites may change their HTML structure. Update the selectors in `scraper.py`:
- Inspect the website's HTML
- Update the CSS selectors in `_extract_raise_deal()` and `_extract_cardcash_deal()`
- Test with `python test_scraper.py`

## Scaling and Optimization

### Performance Tips
- The bot includes rate limiting between requests
- Database indexes are optimized for common queries
- Consider adding caching for frequently accessed data

### Adding More Sources
To add new gift card sites:
1. Add a new scraping method in `scraper.py`
2. Update `get_all_deals()` to include the new source
3. Test thoroughly before deploying

### Premium Features
- The bot supports a premium channel for high-value deals (25%+ off)
- Consider adding email notifications for premium subscribers
- Analytics dashboard using Supabase data
