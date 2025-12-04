#!/usr/bin/env python3
"""
Test script to check ticker 24h data format
"""
import requests

def test_ticker_24h():
    print("Testing Bitvavo ticker/24h data format...")
    
    # Test with a known market
    market = "BTC-EUR"
    url = f"https://api.bitvavo.com/v2/markets/{market}/ticker/24h"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Ticker data structure: {data}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to Bitvavo API: {e}")

if __name__ == "__main__":
    test_ticker_24h()