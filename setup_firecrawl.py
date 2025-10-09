#!/usr/bin/env python3
"""
Setup script for Firecrawl integration
"""

import os
import sys
from pathlib import Path

def setup_firecrawl():
    """Setup Firecrawl API key and test connection"""
    
    print("🔥 Firecrawl Setup")
    print("=" * 30)
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Please create a .env file first")
        return False
    
    # Read current .env file
    with open('.env', 'r') as f:
        content = f.read()
    
    # Check if FIRECRAWL_API_KEY is already set
    if 'FIRECRAWL_API_KEY=' in content and 'your_firecrawl_api_key_here' not in content:
        print("✅ FIRECRAWL_API_KEY is already set in .env")
    else:
        # Get API key from user
        print("\n📝 Please enter your Firecrawl API key:")
        print("   Get it from: https://firecrawl.dev")
        print("   (The key will be hidden as you type)")
        
        api_key = input("Firecrawl API Key: ").strip()
        
        if not api_key:
            print("❌ No API key provided")
            return False
        
        # Update .env file
        if 'FIRECRAWL_API_KEY=your_firecrawl_api_key_here' in content:
            # Replace placeholder
            updated_content = content.replace(
                'FIRECRAWL_API_KEY=your_firecrawl_api_key_here',
                f'FIRECRAWL_API_KEY={api_key}'
            )
        else:
            # Add new line
            updated_content = content.rstrip() + f'\nFIRECRAWL_API_KEY={api_key}\n'
        
        # Write updated content
        with open('.env', 'w') as f:
            f.write(updated_content)
        
        print("✅ Firecrawl API key added to .env file")
    
    # Test the connection
    print("\n🧪 Testing Firecrawl connection...")
    try:
        from firecrawl import FirecrawlApp
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            print("❌ FIRECRAWL_API_KEY not found in environment")
            return False
        
        # Test connection
        app = FirecrawlApp(api_key=api_key)
        
        # Try a simple scrape
        result = app.scrape_url(
            url="https://comptroller.defense.gov/Budget-Execution/Reprogramming/",
            params={'formats': ['markdown'], 'onlyMainContent': True}
        )
        
        if result.get('success'):
            print("✅ Firecrawl connection successful!")
            print(f"   Scraped content length: {len(result.get('data', {}).get('markdown', ''))}")
            return True
        else:
            print(f"❌ Firecrawl test failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Firecrawl: {e}")
        return False

def setup_github_secrets():
    """Setup GitHub Secrets for Firecrawl"""
    
    print("\n🔐 GitHub Secrets Setup")
    print("=" * 30)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
    if not firecrawl_key or firecrawl_key == 'your_firecrawl_api_key_here':
        print("❌ FIRECRAWL_API_KEY not set in .env file")
        return False
    
    print("📋 Add the following to your GitHub Secrets:")
    print(f"   Name: FIRECRAWL_API_KEY")
    print(f"   Value: {firecrawl_key[:10]}...{firecrawl_key[-4:]}")
    print("\n🔗 GitHub Secrets URL:")
    print("   https://github.com/Syzygyx/DD1414/settings/secrets/actions")
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up Firecrawl for Comptroller War Gov")
    print("=" * 50)
    
    # Setup Firecrawl
    if setup_firecrawl():
        print("\n✅ Firecrawl setup complete!")
        
        # Setup GitHub Secrets
        if setup_github_secrets():
            print("\n🎉 Setup complete!")
            print("\nNext steps:")
            print("1. Add FIRECRAWL_API_KEY to GitHub Secrets")
            print("2. Push your changes to trigger the workflow")
            print("3. Check the Actions tab to see the weekly scraping")
            print("4. Test locally: python test_firecrawl.py")
        else:
            print("\n⚠️  Setup completed with warnings")
    else:
        print("\n❌ Setup failed")
        sys.exit(1)