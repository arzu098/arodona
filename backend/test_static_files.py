#!/usr/bin/env python3
"""
Test script to verify static file serving is working
"""
import requests
import time
import sys
from pathlib import Path

def test_server_and_static_files():
    """Test if server is running and static files are accessible"""
    
    # Test if server is running
    try:
        response = requests.get("http://localhost:5858/", timeout=5)
        print(f"✅ Server is running - Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not running: {e}")
        return False
    
    # Test static file access
    test_files = [
        "/uploads/Images/gold-ring-with-diamonds 1.jpg",
        "/uploads/Images/1.png"
    ]
    
    for file_path in test_files:
        try:
            url = f"http://localhost:5858{file_path}"
            print(f"Testing: {url}")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {file_path} - Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}")
            else:
                print(f"❌ {file_path} - Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error accessing {file_path}: {e}")
    
    return True

if __name__ == "__main__":
    print("Testing static file serving...")
    test_server_and_static_files()