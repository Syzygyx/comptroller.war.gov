#!/usr/bin/env python3
"""
Debug GitHub Pages deployment using Playwright
"""

import asyncio
import json
from playwright.async_api import async_playwright
import sys

async def debug_pages():
    """Debug the GitHub Pages deployment"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for CI
        page = await browser.new_page()
        
        # Enable console logging
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))
        
        # Enable network logging
        network_requests = []
        page.on("request", lambda req: network_requests.append({
            "url": req.url,
            "method": req.method,
            "status": "pending"
        }))
        
        page.on("response", lambda res: network_requests.append({
            "url": res.url,
            "method": res.request.method,
            "status": res.status,
            "headers": dict(res.headers)
        }))
        
        # Enable error logging
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append({
            "message": str(error),
            "stack": error.stack
        }))
        
        try:
            print("🌐 Loading GitHub Pages site...")
            await page.goto("https://syzygyx.github.io/DD1414/", wait_until="networkidle")
            
            print("📄 Page loaded, checking for errors...")
            
            # Wait a bit for any async operations
            await page.wait_for_timeout(3000)
            
            # Check if the page loaded successfully
            title = await page.title()
            print(f"📋 Page title: {title}")
            
            # Check for specific elements
            elements_to_check = [
                "h1",
                ".rc-widget",
                "#gantt-chart",
                ".progress-overview",
                "script[src*='client-rag.js']",
                "script[src*='rocket-chat-widget.js']",
                "script[src*='progress-tracker.js']"
            ]
            
            print("\n🔍 Checking for key elements:")
            for selector in elements_to_check:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"  ✅ {selector}")
                    else:
                        print(f"  ❌ {selector} - NOT FOUND")
                except Exception as e:
                    print(f"  ⚠️  {selector} - ERROR: {e}")
            
            # Check for JavaScript errors
            print(f"\n🚨 JavaScript Errors ({len(page_errors)}):")
            for error in page_errors:
                print(f"  ❌ {error['message']}")
                if error['stack']:
                    print(f"     Stack: {error['stack'][:200]}...")
            
            # Check for console messages
            print(f"\n📝 Console Messages ({len(console_messages)}):")
            for msg in console_messages:
                if msg['type'] in ['error', 'warning']:
                    print(f"  {msg['type'].upper()}: {msg['text']}")
                    print(f"     Location: {msg['location']}")
            
            # Check for failed network requests
            print(f"\n🌐 Network Requests ({len(network_requests)}):")
            failed_requests = [req for req in network_requests if isinstance(req.get('status'), int) and req['status'] >= 400]
            for req in failed_requests:
                print(f"  ❌ {req['method']} {req['url']} - Status: {req['status']}")
            
            # Check for missing resources
            missing_resources = [req for req in network_requests if isinstance(req.get('status'), int) and req['status'] == 404]
            if missing_resources:
                print(f"\n📦 Missing Resources ({len(missing_resources)}):")
                for req in missing_resources:
                    print(f"  ❌ {req['url']}")
            
            # Test the chat widget specifically
            print("\n💬 Testing chat widget...")
            try:
                # Check if widget button exists
                widget_button = await page.query_selector(".rc-toggle-button")
                if widget_button:
                    print("  ✅ Chat widget button found")
                    
                    # Try to click it
                    await widget_button.click()
                    await page.wait_for_timeout(1000)
                    
                    # Check if chat interface opened
                    chat_interface = await page.query_selector(".rc-widget")
                    if chat_interface:
                        print("  ✅ Chat interface opened")
                    else:
                        print("  ❌ Chat interface did not open")
                else:
                    print("  ❌ Chat widget button not found")
                    
                # Also check for the widget container
                widget_container = await page.query_selector("#rocket-chat-widget")
                if widget_container:
                    print("  ✅ Chat widget container found")
                else:
                    print("  ❌ Chat widget container not found")
            except Exception as e:
                print(f"  ❌ Error testing chat widget: {e}")
            
            # Test the progress tracker
            print("\n📊 Testing progress tracker...")
            try:
                # Check if progress elements exist
                progress_elements = await page.query_selector_all(".progress-overview > div")
                print(f"  📈 Found {len(progress_elements)} progress elements")
                
                # Check if Gantt chart exists
                gantt_chart = await page.query_selector("#gantt-chart")
                if gantt_chart:
                    print("  ✅ Gantt chart container found")
                    
                    # Check if it has content
                    gantt_content = await gantt_chart.inner_html()
                    if gantt_content.strip():
                        print("  ✅ Gantt chart has content")
                    else:
                        print("  ❌ Gantt chart is empty")
                else:
                    print("  ❌ Gantt chart container not found")
            except Exception as e:
                print(f"  ❌ Error testing progress tracker: {e}")
            
            # Take a screenshot for debugging
            print("\n📸 Taking screenshot...")
            await page.screenshot(path="debug_screenshot.png")
            print("  ✅ Screenshot saved as debug_screenshot.png")
            
            # Save detailed logs
            debug_data = {
                "url": "https://syzygyx.github.io/DD1414/",
                "title": title,
                "console_messages": console_messages,
                "page_errors": page_errors,
                "network_requests": network_requests,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            with open("debug_log.json", "w") as f:
                json.dump(debug_data, f, indent=2)
            print("  ✅ Debug log saved as debug_log.json")
            
        except Exception as e:
            print(f"❌ Error loading page: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    print("🔍 Starting GitHub Pages debug session...")
    asyncio.run(debug_pages())
    print("✅ Debug session complete!")