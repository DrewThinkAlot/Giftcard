# Differentiated Scheduling Setup

Based on the turnover analysis, we're using different scraping frequencies for optimal deal capture:

- **GCX (Raise)**: Every 30 minutes (high turnover: 4.5 deals change per 15 min)
- **CardCash**: Every hour (stable: 0% turnover observed)

## Cron Job Setup

Add these lines to your crontab (`crontab -e`):

```bash
# GCX scraper - every 30 minutes
*/30 * * * * cd /Users/admin/CascadeProjects/telegram-deal-bot && python main_gcx.py >> logs/gcx.log 2>&1

# CardCash scraper - every hour
0 * * * * cd /Users/admin/CascadeProjects/telegram-deal-bot && python main_cardcash.py >> logs/cardcash.log 2>&1
```

## Create Log Directory

```bash
mkdir -p /Users/admin/CascadeProjects/telegram-deal-bot/logs
```

## Alternative: Combined Approach

If you prefer to keep using the original `main.py` but with different frequencies, you can modify the scraper selection:

### Option 1: Time-based scraping in main.py

```python
from datetime import datetime

def should_scrape_cardcash():
    """Only scrape CardCash on the hour (when minutes = 0)"""
    return datetime.now().minute == 0

# In main.py, modify the scraper selection:
scrapers_to_run = ['raise']  # Always run GCX
if should_scrape_cardcash():
    scrapers_to_run.append('cardcash')
```

### Option 2: Separate cron jobs with the original main.py

```bash
# GCX only - every 30 minutes
*/30 * * * * cd /path/to/bot && python -c "
from main import GiftCardDealBot
from scraper import RaiseScraper
bot = GiftCardDealBot()
bot.scraper = RaiseScraper()
bot.process_deals()
" >> logs/gcx.log 2>&1

# CardCash only - every hour  
0 * * * * cd /path/to/bot && python -c "
from main import GiftCardDealBot
from scraper import CardCashScraper
bot = GiftCardDealBot()
bot.scraper = CardCashScraper()
bot.process_deals()
" >> logs/cardcash.log 2>&1
```

## Recommended Approach

I recommend using the **separate script approach** (`main_gcx.py` and `main_cardcash.py`) because:

1. **Clear separation**: Each script has a single responsibility
2. **Independent logging**: Easier to debug issues with specific scrapers
3. **Flexible scheduling**: Can easily adjust timing for each scraper
4. **Better monitoring**: Can track performance of each scraper separately

## Monitoring

Check your logs regularly:

```bash
# View recent GCX activity
tail -f logs/gcx.log

# View recent CardCash activity  
tail -f logs/cardcash.log

# Check for errors
grep -i error logs/*.log
```

## Expected Behavior

- **GCX runs**: :00, :30 every hour (e.g., 1:00, 1:30, 2:00, 2:30...)
- **CardCash runs**: :00 every hour (e.g., 1:00, 2:00, 3:00...)
- **Overlap**: Both run together at the top of each hour

This setup maximizes deal capture while respecting each site's update patterns and your API limits.
