#!/bin/bash

# Telegram Gift Card Deal Bot Runner Script
# This script ensures the bot runs in the correct environment

# Change to the bot directory
cd /Users/admin/CascadeProjects/telegram-deal-bot

# Activate virtual environment if you're using one
# source venv/bin/activate

# Set environment variables (if not using .env file)
# export TELEGRAM_BOT_TOKEN="your_token_here"

# Run the bot with logging
python3 main.py >> logs/bot_$(date +%Y%m%d).log 2>&1

# Optional: Clean up old log files (keep last 30 days)
find logs/ -name "bot_*.log" -mtime +30 -delete 2>/dev/null || true
