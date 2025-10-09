#!/usr/bin/env python3
"""
Monitor DD1414 scraper progress
"""

import time
import os
from pathlib import Path

def monitor_scraper():
    """Monitor the DD1414 scraper progress"""
    output_dir = Path("data/dd1414_csv")
    enhanced_file = output_dir / "dd1414_enhanced_data.csv"
    
    print("🔍 Monitoring DD1414 Enhanced Scraper Progress...")
    print("=" * 50)
    
    start_time = time.time()
    last_size = 0
    
    while True:
        if enhanced_file.exists():
            # Get file size
            current_size = enhanced_file.stat().st_size
            
            if current_size > last_size:
                print(f"📊 Progress: {current_size:,} bytes written")
                last_size = current_size
                
                # Try to read and show current count
                try:
                    import pandas as pd
                    df = pd.read_csv(enhanced_file)
                    print(f"   Records processed: {len(df)}")
                    
                    # Show recent records
                    if len(df) > 0:
                        latest = df.iloc[-1]
                        print(f"   Latest: {latest['filename']} ({latest['extraction_method']}, {latest['confidence_score']:.1f}%)")
                        
                except Exception as e:
                    print(f"   Could not read current data: {e}")
            
            # Check if process is still running
            if current_size == last_size:
                print("⏳ Waiting for more data...")
        else:
            print("⏳ Waiting for output file...")
        
        time.sleep(10)  # Check every 10 seconds
        
        # Stop after 30 minutes
        if time.time() - start_time > 1800:
            print("⏰ Monitoring timeout reached")
            break

if __name__ == "__main__":
    monitor_scraper()