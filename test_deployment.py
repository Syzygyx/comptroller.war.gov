#!/usr/bin/env python3
"""
Test GitHub Pages deployment
"""

import requests
import json

def test_deployment():
    """Test if files are accessible on GitHub Pages"""
    
    base_url = "https://syzygyx.github.io/DD1414"
    
    files_to_test = [
        "index.html",
        "client-rag.js", 
        "rocket-chat-widget.js",
        "progress-tracker.js",
        "data/metadata.json",
        "browse.html",
        "chat.html"
    ]
    
    print("🔍 Testing GitHub Pages deployment...")
    
    for file_path in files_to_test:
        url = f"{base_url}/{file_path}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type and file_path.endswith('.js'):
                    print(f"❌ {file_path} - Returns HTML instead of JavaScript")
                elif 'text/html' in content_type and file_path.endswith('.json'):
                    print(f"❌ {file_path} - Returns HTML instead of JSON")
                else:
                    print(f"✅ {file_path} - OK ({content_type})")
            else:
                print(f"❌ {file_path} - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {file_path} - Error: {e}")
    
    # Test the main page
    print(f"\n🌐 Testing main page...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            content = response.text
            if 'client-rag.js' in content:
                print("✅ Main page includes client-rag.js")
            else:
                print("❌ Main page missing client-rag.js")
                
            if 'rocket-chat-widget.js' in content:
                print("✅ Main page includes rocket-chat-widget.js")
            else:
                print("❌ Main page missing rocket-chat-widget.js")
                
            if 'progress-tracker.js' in content:
                print("✅ Main page includes progress-tracker.js")
            else:
                print("❌ Main page missing progress-tracker.js")
        else:
            print(f"❌ Main page - HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Main page - Error: {e}")

if __name__ == "__main__":
    test_deployment()