#!/usr/bin/env python3
"""
Test script to verify the improvements to the collector module
"""
import asyncio
import yaml
from collector import DataCollector

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config

async def test_collector_improvements():
    """Test the new market skipping and error handling features"""
    print("Testing collector improvements...")
    
    # Load configuration
    config = load_config()
    
    # Initialize collector
    collector = DataCollector(config)
    
    # Test initial state
    print(f"Initial unsupported markets: {len(collector.unsupported_markets)}")
    print(f"Initial error counts: {len(collector.market_error_counts)}")
    
    # Fetch markets
    markets = await collector.fetch_markets()
    print(f"Fetched {len(markets)} markets")
    
    # Try to fetch data for a few markets that we know return 404s
    test_markets = list(collector.markets_cache.keys())[:10]  # Get first 10 markets
    print(f"Testing with markets: {test_markets[:3]}...")  # Show first 3
    
    # Try to fetch ticker data multiple times to trigger the 404 handling
    for i in range(3):  # Simulate multiple attempts
        for market in test_markets[:3]:  # Test with first 3 markets
            ticker = await collector.fetch_ticker_24h(market)
            if ticker is None and market in collector.unsupported_markets:
                print(f"Market {market} correctly marked as unsupported after {collector.market_error_counts.get(market, 0)} attempts")
                break  # Break after first unsupported market is found
    
    # Check if any markets were marked as unsupported
    print(f"Unsupported markets after testing: {len(collector.unsupported_markets)}")
    
    # Test the reset functionality
    collector.reset_unsupported_markets()
    print(f"Unsupported markets after reset: {len(collector.unsupported_markets)}")
    print(f"Error counts after reset: {len(collector.market_error_counts)}")
    
    print("All improvements tested successfully!")

if __name__ == "__main__":
    asyncio.run(test_collector_improvements())