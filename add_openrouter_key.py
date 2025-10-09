#!/usr/bin/env python3
"""
Add OpenRouter API key to .env file
"""

import os
import sys

def add_openrouter_key():
    """Add OpenRouter API key to .env file"""
    
    print("🔑 OpenRouter API Key Setup")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Please create a .env file first")
        return False
    
    # Read current .env file
    with open('.env', 'r') as f:
        content = f.read()
    
    # Check if OPENROUTER_API_KEY is already set
    if 'OPENROUTER_API_KEY=' in content and 'your_openrouter_api_key_here' not in content:
        print("✅ OPENROUTER_API_KEY is already set in .env")
        return True
    
    # Get API key from user
    print("\n📝 Please enter your OpenRouter API key:")
    print("   Get it from: https://openrouter.ai")
    print("   (The key will be hidden as you type)")
    
    api_key = input("OpenRouter API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    # Update .env file
    if 'OPENROUTER_API_KEY=your_openrouter_api_key_here' in content:
        # Replace placeholder
        updated_content = content.replace(
            'OPENROUTER_API_KEY=your_openrouter_api_key_here',
            f'OPENROUTER_API_KEY={api_key}'
        )
    else:
        # Add new line
        updated_content = content.rstrip() + f'\nOPENROUTER_API_KEY={api_key}\n'
    
    # Write updated content
    with open('.env', 'w') as f:
        f.write(updated_content)
    
    print("✅ OpenRouter API key added to .env file")
    
    # Verify the key was added
    with open('.env', 'r') as f:
        if f'OPENROUTER_API_KEY={api_key}' in f.read():
            print("✅ Verification successful")
            return True
        else:
            print("❌ Verification failed")
            return False

if __name__ == "__main__":
    if add_openrouter_key():
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Run: python setup_github_secrets.py")
        print("2. Or manually add the key to GitHub Secrets")
        print("3. Push your changes to trigger deployment")
    else:
        print("\n❌ Setup failed")
        sys.exit(1)