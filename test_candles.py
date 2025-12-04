#!/usr/bin/env python3
"""
Test script to check candles data format
"""
import requests

def test_candles():
    print("Testing Bitvavo candles data format...")
    
    # Test with a known market
    market = "BTC-EUR"
    interval = "1m"
    url = f"https://api.bitvavo.com/v2/markets/{market}/candles"
    params = {
        'interval': interval,
        'limit': 5  # Just get 5 candles to see the format
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Candles data structure: {data[:2]}")  # Show first 2 candles
            if data:
                print(f"First candle format: {data[0]}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to Bitvavo API: {e}")

if __name__ == "__main__":
    test_candles()