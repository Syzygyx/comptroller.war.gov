#!/usr/bin/env python3
"""
Setup GitHub Secrets for the Comptroller War Gov project
"""

import os
import sys
from github import Github
from dotenv import load_dotenv

def setup_github_secrets():
    """Setup GitHub Secrets from local .env file"""
    
    # Load environment variables
    load_dotenv()
    
    # Get GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token or github_token == 'your_github_token_here':
        print("❌ Please set GITHUB_TOKEN in your .env file")
        print("   Get a token from: https://github.com/settings/tokens")
        print("   Required scopes: repo, workflow")
        return False
    
    # Get repository name
    repo_name = os.getenv('GITHUB_REPO', 'Syzygyx/DD1414')
    
    # Get API keys
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not any([openrouter_key, openai_key, anthropic_key]):
        print("❌ No API keys found in .env file")
        print("   Please add at least one of:")
        print("   - OPENROUTER_API_KEY")
        print("   - OPENAI_API_KEY") 
        print("   - ANTHROPIC_API_KEY")
        return False
    
    try:
        # Initialize GitHub client
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        print(f"🔐 Setting up secrets for {repo_name}...")
        
        # Set secrets
        secrets_to_set = {}
        
        if openrouter_key and openrouter_key != 'your_openrouter_api_key_here':
            secrets_to_set['OPENROUTER_API_KEY'] = openrouter_key
            print("✅ OPENROUTER_API_KEY ready")
        else:
            print("⚠️  OPENROUTER_API_KEY not set or using placeholder")
            
        if openai_key and openai_key != 'your_openai_api_key_here':
            secrets_to_set['OPENAI_API_KEY'] = openai_key
            print("✅ OPENAI_API_KEY ready")
        else:
            print("⚠️  OPENAI_API_KEY not set or using placeholder")
            
        if anthropic_key and anthropic_key != 'your_anthropic_api_key_here':
            secrets_to_set['ANTHROPIC_API_KEY'] = anthropic_key
            print("✅ ANTHROPIC_API_KEY ready")
        else:
            print("⚠️  ANTHROPIC_API_KEY not set or using placeholder")
        
        if not secrets_to_set:
            print("❌ No valid API keys found to set as secrets")
            return False
        
        # Create or update secrets
        for secret_name, secret_value in secrets_to_set.items():
            try:
                # Check if secret exists
                try:
                    existing_secret = repo.get_secret(secret_name)
                    print(f"🔄 Updating existing secret: {secret_name}")
                except:
                    print(f"➕ Creating new secret: {secret_name}")
                
                # Create/update secret
                repo.create_secret(secret_name, secret_value)
                print(f"✅ {secret_name} set successfully")
                
            except Exception as e:
                print(f"❌ Failed to set {secret_name}: {e}")
                return False
        
        print(f"\n🎉 Successfully set {len(secrets_to_set)} secrets!")
        print("🚀 Your GitHub Actions workflow can now use these secrets")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up secrets: {e}")
        return False

if __name__ == "__main__":
    print("🔐 GitHub Secrets Setup")
    print("=" * 50)
    
    if setup_github_secrets():
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Push your changes to trigger the GitHub Actions workflow")
        print("2. Check the Actions tab to see the deployment progress")
        print("3. Visit your GitHub Pages site to test the chat widget")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)