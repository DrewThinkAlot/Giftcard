-- Supabase database schema for the Telegram Gift Card Deal Bot
-- Run this SQL in your Supabase SQL editor to set up the required tables

-- Table to track posted deals and prevent duplicates
CREATE TABLE IF NOT EXISTS posted_deals (
    id SERIAL PRIMARY KEY,
    deal_hash VARCHAR(32) UNIQUE NOT NULL,
    merchant VARCHAR(255) NOT NULL,
    face_value DECIMAL(10,2) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) NOT NULL,
    url TEXT,
    source VARCHAR(50) NOT NULL, -- 'raise' or 'cardcash'
    posted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_posted_deals_hash ON posted_deals(deal_hash);
CREATE INDEX IF NOT EXISTS idx_posted_deals_posted_at ON posted_deals(posted_at);
CREATE INDEX IF NOT EXISTS idx_posted_deals_source ON posted_deals(source);
CREATE INDEX IF NOT EXISTS idx_posted_deals_discount ON posted_deals(discount_percent);

-- Optional: Table to track bot execution logs
CREATE TABLE IF NOT EXISTS bot_executions (
    id SERIAL PRIMARY KEY,
    execution_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deals_found INTEGER DEFAULT 0,
    deals_posted INTEGER DEFAULT 0,
    premium_deals_posted INTEGER DEFAULT 0,
    errors TEXT,
    status VARCHAR(20) DEFAULT 'success' -- 'success', 'error', 'partial'
);

-- Optional: Table to track popular merchants for analytics
CREATE TABLE IF NOT EXISTS merchant_stats (
    id SERIAL PRIMARY KEY,
    merchant VARCHAR(255) UNIQUE NOT NULL,
    total_deals INTEGER DEFAULT 0,
    avg_discount DECIMAL(5,2) DEFAULT 0,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to update merchant stats (optional)
CREATE OR REPLACE FUNCTION update_merchant_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO merchant_stats (merchant, total_deals, avg_discount, last_seen)
    VALUES (NEW.merchant, 1, NEW.discount_percent, NOW())
    ON CONFLICT (merchant) 
    DO UPDATE SET 
        total_deals = merchant_stats.total_deals + 1,
        avg_discount = (merchant_stats.avg_discount * merchant_stats.total_deals + NEW.discount_percent) / (merchant_stats.total_deals + 1),
        last_seen = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update merchant stats when deals are posted
-- Drop the trigger if it exists (Postgres 11+ syntax)
DROP TRIGGER IF EXISTS trigger_update_merchant_stats ON posted_deals;

-- Now create the trigger
CREATE TRIGGER trigger_update_merchant_stats
    AFTER INSERT ON posted_deals
    FOR EACH ROW
    EXECUTE FUNCTION update_merchant_stats();

-- Clean up old deals (optional - run periodically)
-- DELETE FROM posted_deals WHERE posted_at < NOW() - INTERVAL '30 days';
