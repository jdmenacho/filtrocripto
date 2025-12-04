#!/usr/bin/env python3
"""
Test script to verify Bitvavo API connectivity
"""
import requests
import time

def test_bitvavo_api():
    print("Testing Bitvavo API connectivity...")
    
    # Test markets endpoint
    url = "https://api.bitvavo.com/v2/markets"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total markets: {len(data)}")
            
            # Print the first market to understand the structure
            if data:
                print(f"First market structure: {data[0]}")
                
            # Check what quote assets are available
            quote_assets = set()
            for market in data:
                # Check all keys in the market dict
                if isinstance(market, dict):
                    for key, value in market.items():
                        if 'Asset' in key or 'asset' in key:
                            print(f"Found asset key: {key} = {value}")
                        if key == 'quoteAsset' or key == 'quote':
                            quote_assets.add(value)
                            
            print(f"Available quote assets: {sorted(list(quote_assets))}")
            
            # Try to find markets with EUR as quote asset using different possible keys
            eur_markets = []
            for market in data:
                if isinstance(market, dict):
                    # Try different possible keys for quote asset
                    for key in ['quoteAsset', 'quote', 'quoteSymbol', 'quoteCurrency', 'target', 'targetCurrency']:
                        if market.get(key) == 'EUR':
                            eur_markets.append(market)
                            break
            
            print(f"EUR markets: {len(eur_markets)}")
            
            # Show first few EUR markets
            if eur_markets:
                print("First 5 EUR markets:")
                for market in eur_markets[:5]:
                    print(f"  - {market.get('market', 'N/A')}: {market.get('baseAsset', 'N/A')}/{market.get('quoteAsset', 'N/A')}")
            else:
                print("No EUR markets found. Let's check other common quote assets:")
                for quote_asset in ['USDT', 'BTC', 'ETH']:
                    quote_markets = []
                    for market in data:
                        if isinstance(market, dict):
                            for key in ['quoteAsset', 'quote', 'quoteSymbol', 'quoteCurrency', 'target', 'targetCurrency']:
                                if market.get(key) == quote_asset:
                                    quote_markets.append(market)
                                    break
                    print(f"  {quote_asset} markets: {len(quote_markets)}")
                    if quote_markets:
                        print(f"    First 3 {quote_asset} markets: {[m.get('market', 'N/A') for m in quote_markets[:3]]}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to Bitvavo API: {e}")

if __name__ == "__main__":
    test_bitvavo_api()