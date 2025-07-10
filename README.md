# Telegram Gift Card Deal Bot

A Python bot that scrapes gift card deals from Raise.com and CardCash.com, filters for discounts ≥15%, and posts formatted messages to Telegram channels.

## Features

- 🔍 Scrapes deals from Raise.com and CardCash.com
- 📊 Filters deals by discount percentage (≥15% for regular, ≥25% for premium)
- 🚫 Prevents duplicate posts using Supabase database
- 🔗 Shortens affiliate links using Geniuslink
- 📱 Posts formatted messages to Telegram channels
- ⏰ Optional deal expiration time display
- 🌟 Premium channel for high-value deals (25%+ off)
- 📈 Deal monitoring and turnover analysis
- 🗄️ Full database-driven storage for deal tracking and analytics

## Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in your API keys and tokens

3. **Set up Supabase database:**
   - Create a new Supabase project
   - Run the SQL schema (see Database Schema section)
   - Get your project URL and anon key

4. **Create Telegram bot:**
   - Message @BotFather on Telegram
   - Create a new bot and get the token
   - Add the bot to your channel as an admin

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather |
| `TELEGRAM_CHANNEL_ID` | Channel username (e.g., @your_channel) or chat ID |
| `TELEGRAM_PREMIUM_CHANNEL_ID` | Premium channel for 25%+ deals (optional) |
| `GENIUSLINK_API_KEY` | Your Geniuslink API key |
| `GENIUSLINK_SECRET` | Your Geniuslink secret |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anonymous key |

## Database Schema

The bot uses Supabase for deal tracking, monitoring, and analytics. Set up the following tables:

### Basic Deal Tracking
```sql
CREATE TABLE posted_deals (
    id SERIAL PRIMARY KEY,
    deal_hash VARCHAR(32) UNIQUE NOT NULL,
    merchant VARCHAR(255),
    face_value DECIMAL(10,2),
    price DECIMAL(10,2),
    discount_percent DECIMAL(5,2),
    url TEXT,
    posted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_posted_deals_hash ON posted_deals(deal_hash);
CREATE INDEX idx_posted_deals_posted_at ON posted_deals(posted_at);
```

### Deal Monitoring & Analysis (run database_schema.sql)
```sql
-- Deals table for persistent deal storage
CREATE TABLE deals (
    id SERIAL PRIMARY KEY,
    merchant VARCHAR(255) NOT NULL,
    face_value DECIMAL(10,2) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) NOT NULL,
    source VARCHAR(50) NOT NULL,
    url TEXT,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Monitoring sessions
CREATE TABLE monitoring_sessions (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(255),
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_minutes NUMERIC,
    check_interval_minutes NUMERIC,
    notes TEXT
);

-- Snapshots
CREATE TABLE snapshots (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES monitoring_sessions(id),
    timestamp TIMESTAMP WITH TIME ZONE,
    total_deals INTEGER,
    new_deals INTEGER,
    notes TEXT
);

-- Snapshot deals (deals in each snapshot)
CREATE TABLE snapshot_deals (
    id SERIAL PRIMARY KEY,
    snapshot_id INTEGER REFERENCES snapshots(id),
    deal_id INTEGER REFERENCES deals(id),
    UNIQUE(snapshot_id, deal_id)
);
```

## Usage

### Running the Deal Bot
```bash
python main.py
```

### Deal Monitoring & Analysis

#### Database-Driven Monitoring (Recommended)
```bash
# Run a monitoring session
python unified_monitor.py --duration 60 --interval 10

# Generate reports after monitoring
python unified_monitor.py --duration 60 --interval 10 --reports

# Run quick analysis
python unified_monitor.py --quick --interval 5
```

#### Legacy JSON-Based Monitoring
```bash
python unified_monitor.py --legacy --duration 60 --interval 10
```

#### Full Integration Test
```bash
# Test the database-driven monitoring with the main bot
python test_database_integration.py --mode full

# Just test monitoring
python test_database_integration.py --mode monitoring --duration 10 --interval 2
```

### Scheduled Execution (Every 5 minutes)

For Replit deployment:
1. Create a simple Flask web server
2. Use a free cron service like cron-job.org to ping your Replit URL every 5 minutes

## Message Format

The bot posts deals in this format:

```
🎯 Target Gift Card
💳 Face Value: $100.00
💸 Price: $78.00 (22% OFF)
🔗 Buy Now
⏰ Expires: 2024-01-15 (if available)
```

Premium deals include a "🌟 **PREMIUM DEAL** 🌟" header.

## API Integration Status

- [ ] Raise.com API integration (needs investigation)
- [ ] CardCash.com API integration (needs investigation)  
- [ ] Geniuslink API integration (needs implementation)
- [x] Telegram Bot API integration (implemented)
- [x] Supabase database integration (implemented)

## Next Steps

1. Investigate Raise.com and CardCash.com APIs/feeds
2. Implement Geniuslink API integration
3. Set up automated scheduling
4. Test with real data
5. Optimize database queries for improved performance
6. Implement dashboard visualizations for deal analytics

## Deployment

This bot is designed to run on free/low-cost platforms like:
- Replit (recommended for always-on hosting)
- Heroku (free tier)
- Railway
- Render

For Replit deployment, add a simple Flask web server that can be pinged by external cron services.
