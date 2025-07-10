# Telegram Gift Card Deal Bot - Scheduling Guide

## Overview
This guide covers different methods to automatically schedule your Telegram gift card deal bot to run at regular intervals.

## Option 1: Cron Job (Recommended for macOS/Linux)

### Setup Cron Job
1. Open terminal and edit your crontab:
   ```bash
   crontab -e
   ```

2. Add one of these scheduling options:

   **Every 30 minutes:**
   ```bash
   */30 * * * * /Users/admin/CascadeProjects/telegram-deal-bot/run_bot.sh
   ```

   **Every hour at minute 0:**
   ```bash
   0 * * * * /Users/admin/CascadeProjects/telegram-deal-bot/run_bot.sh
   ```

   **Every 2 hours:**
   ```bash
   0 */2 * * * /Users/admin/CascadeProjects/telegram-deal-bot/run_bot.sh
   ```

   **Every 4 hours:**
   ```bash
   0 */4 * * * /Users/admin/CascadeProjects/telegram-deal-bot/run_bot.sh
   ```

   **Daily at 9 AM:**
   ```bash
   0 9 * * * /Users/admin/CascadeProjects/telegram-deal-bot/run_bot.sh
   ```

### Verify Cron Job
```bash
# List current cron jobs
crontab -l

# Check cron service status (macOS)
sudo launchctl list | grep cron
```

## Option 2: macOS LaunchAgent (Alternative for macOS)

Create a LaunchAgent plist file for more reliable scheduling on macOS:

1. Create the plist file:
   ```bash
   nano ~/Library/LaunchAgents/com.telegram.dealbot.plist
   ```

2. Add this content (adjust timing as needed):
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.telegram.dealbot</string>
       <key>ProgramArguments</key>
       <array>
           <string>/Users/admin/CascadeProjects/telegram-deal-bot/run_bot.sh</string>
       </array>
       <key>StartInterval</key>
       <integer>3600</integer> <!-- Run every hour (3600 seconds) -->
       <key>RunAtLoad</key>
       <true/>
       <key>StandardOutPath</key>
       <string>/Users/admin/CascadeProjects/telegram-deal-bot/logs/launchd.log</string>
       <key>StandardErrorPath</key>
       <string>/Users/admin/CascadeProjects/telegram-deal-bot/logs/launchd_error.log</string>
   </dict>
   </plist>
   ```

3. Load the LaunchAgent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.telegram.dealbot.plist
   launchctl start com.telegram.dealbot
   ```

## Option 3: Python Scheduler (Built-in Solution)

Create a scheduler script that runs continuously:

```python
# scheduler.py
import schedule
import time
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bot():
    """Run the bot and log the execution"""
    try:
        logger.info(f"Starting bot execution at {datetime.now()}")
        result = subprocess.run(['python3', 'main.py'], 
                              capture_output=True, text=True, cwd='/Users/admin/CascadeProjects/telegram-deal-bot')
        
        if result.returncode == 0:
            logger.info("Bot execution completed successfully")
        else:
            logger.error(f"Bot execution failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Error running bot: {e}")

# Schedule options (choose one):
schedule.every(30).minutes.do(run_bot)  # Every 30 minutes
# schedule.every().hour.do(run_bot)     # Every hour
# schedule.every(2).hours.do(run_bot)   # Every 2 hours
# schedule.every().day.at("09:00").do(run_bot)  # Daily at 9 AM

if __name__ == "__main__":
    logger.info("Bot scheduler started")
    run_bot()  # Run once immediately
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
```

## Option 4: Cloud Deployment

### GitHub Actions (Free tier available)
Create `.github/workflows/bot-scheduler.yml`:

```yaml
name: Telegram Deal Bot
on:
  schedule:
    - cron: '0 */2 * * *'  # Every 2 hours
  workflow_dispatch:  # Manual trigger

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run bot
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHANNEL_ID: ${{ secrets.TELEGRAM_CHANNEL_ID }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          SCRAPINGDOG_API_KEY: ${{ secrets.SCRAPINGDOG_API_KEY }}
        run: python main.py
```

## Recommended Scheduling Frequency

Based on gift card deal patterns:

- **High Activity**: Every 30 minutes (for maximum deal coverage)
- **Balanced**: Every 1-2 hours (good balance of coverage vs. API usage)
- **Conservative**: Every 4-6 hours (minimal API usage)
- **Daily**: Once per day (very light usage)

## Monitoring & Maintenance

### Log Monitoring
- Check logs regularly: `tail -f logs/bot_*.log`
- Set up log rotation to prevent disk space issues
- Monitor for API rate limits or errors

### Health Checks
Create a simple health check script:

```bash
#!/bin/bash
# health_check.sh
LOG_FILE="logs/bot_$(date +%Y%m%d).log"
if [ -f "$LOG_FILE" ]; then
    LAST_RUN=$(tail -n 50 "$LOG_FILE" | grep "Deal processing completed" | tail -n 1)
    if [ -n "$LAST_RUN" ]; then
        echo "✅ Bot is running normally"
        echo "Last successful run: $LAST_RUN"
    else
        echo "⚠️  No recent successful runs found"
    fi
else
    echo "❌ No log file found for today"
fi
```

## Troubleshooting

### Common Issues:
1. **Permission denied**: Ensure `run_bot.sh` is executable (`chmod +x run_bot.sh`)
2. **Path issues**: Use absolute paths in cron jobs
3. **Environment variables**: Make sure `.env` file is accessible
4. **API limits**: Monitor Scrapingdog API usage and adjust frequency

### Debug Commands:
```bash
# Test the runner script manually
./run_bot.sh

# Check cron logs (macOS)
log show --predicate 'process == "cron"' --last 1h

# Check if cron job is running
ps aux | grep cron
```

Choose the method that best fits your environment and monitoring preferences!
