#!/usr/bin/env python3
"""
Test script for Rocket.Chat widget integration
"""

import requests
import json
import time
from pathlib import Path

def test_chat_api():
    """Test the chat API with context"""
    print("🧪 Testing Rocket.Chat API integration...")
    
    # Test data
    test_contexts = [
        {
            "page": "index.html",
            "type": "dashboard",
            "description": "Main dashboard with processing statistics"
        },
        {
            "page": "browse.html", 
            "type": "data_browser",
            "description": "Browse extracted budget data",
            "filters": {
                "branch": "Army",
                "category": "Operation and Maintenance"
            }
        },
        {
            "page": "sankey.html",
            "type": "budget_visualization", 
            "description": "Interactive budget flow diagram",
            "visualization": {
                "fiscalYear": "2025",
                "minAmount": "10000",
                "flowType": "category-branch"
            }
        }
    ]
    
    # Test messages
    test_messages = [
        "What data is available?",
        "Tell me about Army budget data",
        "What does this visualization show?",
        "How much funding is there for Operation and Maintenance?"
    ]
    
    try:
        # Test basic API connectivity
        response = requests.get('http://localhost:5000/api/stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ API is running - {stats.get('total_chunks', 0)} chunks loaded")
        else:
            print(f"❌ API stats failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not running. Start with: python src/chat_api.py")
        return False
    except Exception as e:
        print(f"❌ API error: {e}")
        return False
    
    # Test chat with context
    for i, context in enumerate(test_contexts):
        print(f"\n📄 Testing context {i+1}: {context['description']}")
        
        for message in test_messages:
            try:
                payload = {
                    "message": message,
                    "context": context,
                    "history": []
                }
                
                response = requests.post(
                    'http://localhost:5000/api/chat',
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ '{message}' -> {len(data.get('answer', ''))} chars")
                    if data.get('sources'):
                        print(f"     Sources: {len(data['sources'])} documents")
                else:
                    print(f"  ❌ '{message}' -> HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ '{message}' -> Error: {e}")
    
    return True

def test_widget_files():
    """Test that widget files exist and are properly formatted"""
    print("\n🔍 Testing widget files...")
    
    # Check widget JS file
    widget_file = Path('docs/rocket-chat-widget.js')
    if widget_file.exists():
        content = widget_file.read_text()
        if 'RocketChatWidget' in content and 'detectContext' in content:
            print("✅ rocket-chat-widget.js exists and looks correct")
        else:
            print("❌ rocket-chat-widget.js missing key functions")
            return False
    else:
        print("❌ rocket-chat-widget.js not found")
        return False
    
    # Check HTML files have widget included
    html_files = [
        'docs/index.html',
        'docs/browse.html', 
        'docs/chat.html',
        'docs/progress.html',
        'docs/sankey.html'
    ]
    
    for html_file in html_files:
        file_path = Path(html_file)
        if file_path.exists():
            content = file_path.read_text()
            if 'rocket-chat-widget.js' in content:
                print(f"✅ {html_file} includes widget")
            else:
                print(f"❌ {html_file} missing widget include")
                return False
        else:
            print(f"❌ {html_file} not found")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Rocket.Chat Widget Integration\n")
    
    # Test files
    files_ok = test_widget_files()
    
    # Test API (if running)
    api_ok = test_chat_api()
    
    print(f"\n📊 Test Results:")
    print(f"  Files: {'✅ PASS' if files_ok else '❌ FAIL'}")
    print(f"  API: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if files_ok and api_ok:
        print("\n🎉 All tests passed! Rocket.Chat widget is ready.")
        print("\nTo use:")
        print("1. Start the API: python src/chat_api.py")
        print("2. Open any page in browser")
        print("3. Click the chat button in bottom-right corner")
        print("4. Ask questions about the data!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return files_ok and api_ok

if __name__ == '__main__':
    main()