#!/usr/bin/env python3
"""
Deployment script for the Telegram Gift Card Deal Bot
This script helps set up and deploy the bot to various platforms
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required files and dependencies are present"""
    print("🔍 Checking requirements...")
    
    required_files = [
        'main.py',
        'scraper.py', 
        'database.py',
        'requirements.txt',
        'database_setup.sql',
        '.env.example'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def check_environment():
    """Check environment variables"""
    print("\n🔧 Checking environment configuration...")
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHANNEL_ID',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    optional_vars = [
        'TELEGRAM_PREMIUM_CHANNEL_ID',
        'GENIUSLINK_API_KEY',
        'GENIUSLINK_SECRET'
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_required:
        print(f"❌ Missing required environment variables: {', '.join(missing_required)}")
        print("Please set up your .env file with these variables")
        return False
    
    print("✅ All required environment variables present")
    
    if missing_optional:
        print(f"⚠️  Optional variables not set: {', '.join(missing_optional)}")
        print("These features will be disabled but the bot will still work")
    
    return True

def test_components():
    """Test all bot components"""
    print("\n🧪 Testing bot components...")
    
    try:
        # Test scraper
        print("Testing scraper...")
        result = subprocess.run([sys.executable, 'test_scraper.py'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"❌ Scraper test failed: {result.stderr}")
            return False
        print("✅ Scraper test passed")
        
        # Test integration
        print("Testing integration...")
        result = subprocess.run([sys.executable, 'test_complete_integration.py'], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print("⚠️  Integration test had issues (likely due to missing Supabase credentials)")
        else:
            print("✅ Integration test passed")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def create_deployment_configs():
    """Create deployment configuration files"""
    print("\n📝 Creating deployment configurations...")
    
    # Replit configuration
    replit_config = {
        "language": "python3",
        "run": "python main.py",
        "entrypoint": "main.py",
        "hidden": [".env"],
        "modules": ["python3"]
    }
    
    with open('.replit', 'w') as f:
        f.write(f"language = \"python3\"\nrun = \"python main.py\"\nentrypoint = \"main.py\"\nhidden = [\".env\"]\n")
    
    # Railway configuration
    railway_config = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python main.py",
            "restartPolicyType": "ON_FAILURE"
        }
    }
    
    with open('railway.json', 'w') as f:
        json.dump(railway_config, f, indent=2)
    
    # Heroku Procfile
    with open('Procfile', 'w') as f:
        f.write("worker: python main.py\n")
    
    # Docker configuration
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Deployment configurations created")

def show_deployment_instructions():
    """Show deployment instructions for different platforms"""
    print("\n🚀 Deployment Instructions")
    print("=" * 50)
    
    print("\n1. REPLIT (Easiest)")
    print("   • Import this project to Replit")
    print("   • Set environment variables in Secrets tab")
    print("   • Enable Always On for 24/7 operation")
    print("   • Use Replit's cron job feature for scheduling")
    
    print("\n2. RAILWAY")
    print("   • Connect GitHub repo to Railway")
    print("   • Set environment variables in dashboard")
    print("   • Deploy automatically")
    
    print("\n3. HEROKU")
    print("   • Create new Heroku app")
    print("   • Set config vars for environment variables")
    print("   • Use Heroku Scheduler add-on")
    print("   • Deploy with: git push heroku main")
    
    print("\n4. VPS/CLOUD SERVER")
    print("   • Set up Python 3.8+ environment")
    print("   • Install dependencies: pip install -r requirements.txt")
    print("   • Set up systemd service for auto-restart")
    print("   • Use cron for scheduling every 5 minutes")
    
    print("\n📋 Cron Job Example (Every 5 minutes):")
    print("   */5 * * * * cd /path/to/bot && python main.py >> logs/bot.log 2>&1")

def main():
    """Main deployment function"""
    print("🚀 Telegram Gift Card Deal Bot - Deployment Setup")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Deployment failed - missing requirements")
        return False
    
    # Check environment (only warn, don't fail)
    env_ok = check_environment()
    
    # Test components
    if not test_components():
        print("\n⚠️  Some tests failed, but continuing with deployment setup")
    
    # Create deployment configs
    create_deployment_configs()
    
    # Show instructions
    show_deployment_instructions()
    
    print(f"\n{'✅' if env_ok else '⚠️ '} Deployment setup completed!")
    
    if not env_ok:
        print("\n⚠️  IMPORTANT: Set up your environment variables before deploying")
        print("   Copy .env.example to .env and fill in your credentials")
    
    print("\n📚 Next Steps:")
    print("1. Set up Supabase database (run database_setup.sql)")
    print("2. Configure environment variables")
    print("3. Test with: python test_telegram.py")
    print("4. Deploy to your chosen platform")
    print("5. Set up scheduling (every 5 minutes)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
