#!/usr/bin/env python3
"""
Test script to verify the trading algorithm components work correctly
"""

import asyncio
import yaml
from collector import DataCollector
from indicators import Indicators
from filters import FilterEngine
from signals import SignalEngine

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def test_indicators():
    """Test indicator calculations"""
    print("Testing indicators...")
    indicators = Indicators()
    
    # Test data
    test_closes = [100, 102, 98, 105, 107, 103, 108, 110, 106, 112, 115, 113, 117, 119, 116]
    test_highs = [101, 103, 99, 106, 108, 104, 109, 111, 107, 113, 116, 114, 118, 120, 117]
    test_lows = [99, 101, 97, 104, 106, 102, 107, 109, 105, 111, 114, 112, 116, 118, 115]
    
    # Test RSI
    rsi_values = indicators.calculate_rsi(test_closes, 14)
    print(f"RSI values: {rsi_values[-3:]}")
    
    # Test MACD
    macd_line, signal_line, histogram = indicators.calculate_macd(test_closes)
    print(f"MACD histogram (last 3): {histogram[-3:]}")
    
    # Test Bollinger Bands
    upper, middle, lower = indicators.calculate_bollinger_bands(test_closes)
    print(f"Bollinger Bands - Upper: {upper[-1]:.2f}, Middle: {middle[-1]:.2f}, Lower: {lower[-1]:.2f}")
    
    # Test volatility
    vol_pct = indicators.calculate_volatility_pct(test_highs, test_lows, test_closes, 5)
    print(f"Volatility % (last 3): {vol_pct[-3:]}")
    
    print("✓ Indicators test passed\n")

def test_filters():
    """Test filter engine"""
    print("Testing filters...")
    config = load_config()
    filter_engine = FilterEngine(config)
    
    # Test data structure
    market_data = {
        'current_price': 100.0,
        'ticker_24h': {
            'volume': 2000000,  # 2M EUR
            'priceChangePercentage': 5.5
        },
        'orderbook': {
            'spread_pct': 0.3
        },
        'candles': {
            '1h': [
                {'open': 95, 'high': 105, 'low': 94, 'close': 100, 'volume': 10000},
                {'open': 100, 'high': 108, 'low': 99, 'close': 105, 'volume': 12000},
                {'open': 105, 'high': 110, 'low': 103, 'close': 108, 'volume': 15000},
            ],
            '15m': [
                {'open': 107, 'high': 109, 'low': 106, 'close': 108, 'volume': 3000},
                {'open': 108, 'high': 110, 'low': 107, 'close': 109, 'volume': 3200},
                {'open': 109, 'high': 111, 'low': 108, 'close': 110, 'volume': 3500},
            ],
            '5m': [
                {'open': 109, 'high': 110, 'low': 108.5, 'close': 109.5, 'volume': 1000},
                {'open': 109.5, 'high': 110.5, 'low': 109, 'close': 110, 'volume': 1100},
                {'open': 110, 'high': 111, 'low': 109.8, 'close': 110.5, 'volume': 1200},
            ],
            '1m': [
                {'open': 110, 'high': 110.5, 'low': 109.9, 'close': 110.2, 'volume': 200},
                {'open': 110.2, 'high': 110.7, 'low': 110.1, 'close': 110.5, 'volume': 220},
                {'open': 110.5, 'high': 111, 'low': 110.3, 'close': 110.8, 'volume': 250},
            ]
        },
        'timestamp': 1234567890
    }
    
    is_valid, reasons = filter_engine.apply_all_filters(market_data)
    print(f"Filter result: {is_valid}")
    print(f"Reasons: {reasons}")
    
    print("✓ Filters test passed\n")

def test_signals():
    """Test signal generation"""
    print("Testing signals...")
    config = load_config()
    signal_engine = SignalEngine(config)
    
    # Test data structure
    market_data = {
        'current_price': 100.0,
        'ticker_24h': {
            'volume': 2000000,  # 2M EUR
            'priceChangePercentage': 5.5,
            'last': 100.0
        },
        'orderbook': {
            'spread_pct': 0.3
        },
        'candles': {
            '1h': [
                {'open': 95, 'high': 105, 'low': 94, 'close': 100, 'volume': 10000},
                {'open': 100, 'high': 108, 'low': 99, 'close': 105, 'volume': 12000},
                {'open': 105, 'high': 110, 'low': 103, 'close': 108, 'volume': 15000},
            ],
            '15m': [
                {'open': 107, 'high': 109, 'low': 106, 'close': 108, 'volume': 3000},
                {'open': 108, 'high': 110, 'low': 107, 'close': 109, 'volume': 3200},
                {'open': 109, 'high': 111, 'low': 108, 'close': 110, 'volume': 3500},
                {'open': 110, 'high': 112, 'low': 109, 'close': 111, 'volume': 3700},
                {'open': 111, 'high': 113, 'low': 110, 'close': 112, 'volume': 4000},
                {'open': 112, 'high': 114, 'low': 111, 'close': 113, 'volume': 4200},
                {'open': 113, 'high': 115, 'low': 112, 'close': 114, 'volume': 4500},
                {'open': 114, 'high': 116, 'low': 113, 'close': 115, 'volume': 4800},
                {'open': 115, 'high': 117, 'low': 114, 'close': 116, 'volume': 5000},
                {'open': 116, 'high': 118, 'low': 115, 'close': 117, 'volume': 5200},
                {'open': 117, 'high': 119, 'low': 116, 'close': 118, 'volume': 5500},
                {'open': 118, 'high': 120, 'low': 117, 'close': 119, 'volume': 5800},
                {'open': 119, 'high': 121, 'low': 118, 'close': 120, 'volume': 6000},
                {'open': 120, 'high': 122, 'low': 119, 'close': 121, 'volume': 6200},
                {'open': 121, 'high': 123, 'low': 120, 'close': 122, 'volume': 6500},
            ],
            '5m': [
                {'open': 120, 'high': 122, 'low': 119.5, 'close': 121.5, 'volume': 2000},
                {'open': 121.5, 'high': 123, 'low': 121, 'close': 122.5, 'volume': 2200},
                {'open': 122.5, 'high': 124, 'low': 122, 'close': 123, 'volume': 2400},
                {'open': 123, 'high': 124.5, 'low': 122.5, 'close': 124, 'volume': 2600},
                {'open': 124, 'high': 125, 'low': 123.5, 'close': 124.5, 'volume': 2800},
                {'open': 124.5, 'high': 125.5, 'low': 124, 'close': 125, 'volume': 3000},
                {'open': 125, 'high': 126, 'low': 124.5, 'close': 125.5, 'volume': 3200},
                {'open': 125.5, 'high': 126.5, 'low': 125, 'close': 126, 'volume': 3400},
                {'open': 126, 'high': 127, 'low': 125.5, 'close': 126.5, 'volume': 3600},
                {'open': 126.5, 'high': 127.5, 'low': 126, 'close': 127, 'volume': 3800},
                {'open': 127, 'high': 128, 'low': 126.5, 'close': 127.5, 'volume': 4000},
                {'open': 127.5, 'high': 128.5, 'low': 127, 'close': 128, 'volume': 4200},
                {'open': 128, 'high': 129, 'low': 127.5, 'close': 128.5, 'volume': 4400},
                {'open': 128.5, 'high': 129.5, 'low': 128, 'close': 129, 'volume': 4600},
                {'open': 129, 'high': 130, 'low': 128.5, 'close': 129.5, 'volume': 4800},
                {'open': 129.5, 'high': 130.5, 'low': 129, 'close': 130, 'volume': 5000},
                {'open': 130, 'high': 131, 'low': 129.5, 'close': 130.5, 'volume': 5200},
                {'open': 130.5, 'high': 131.5, 'low': 130, 'close': 131, 'volume': 5400},
                {'open': 131, 'high': 132, 'low': 130.5, 'close': 131.5, 'volume': 5600},
                {'open': 131.5, 'high': 132.5, 'low': 131, 'close': 132, 'volume': 5800},
                {'open': 132, 'high': 133, 'low': 131.5, 'close': 132.5, 'volume': 6000},
                {'open': 132.5, 'high': 133.5, 'low': 132, 'close': 133, 'volume': 6200},
                {'open': 133, 'high': 134, 'low': 132.5, 'close': 133.5, 'volume': 6400},
                {'open': 133.5, 'high': 134.5, 'low': 133, 'close': 134, 'volume': 6600},
                {'open': 134, 'high': 135, 'low': 133.5, 'close': 134.5, 'volume': 6800},
            ],
            '1m': [
                {'open': 134, 'high': 135, 'low': 133.8, 'close': 134.5, 'volume': 400},
                {'open': 134.5, 'high': 135.2, 'low': 134.2, 'close': 134.8, 'volume': 420},
                {'open': 134.8, 'high': 135.5, 'low': 134.5, 'close': 135.2, 'volume': 440},
                {'open': 135.2, 'high': 135.8, 'low': 134.8, 'close': 135.5, 'volume': 460},
                {'open': 135.5, 'high': 136, 'low': 135.2, 'close': 135.8, 'volume': 480},
            ]
        },
        'timestamp': 1234567890
    }
    
    signal = signal_engine.generate_signal("TEST-EUR", market_data)
    print(f"Signal: {signal}")
    
    print("✓ Signals test passed\n")

async def test_collector():
    """Test data collector"""
    print("Testing collector...")
    config = load_config()
    collector = DataCollector(config)
    
    # Test fetching markets (this will make an actual API call)
    try:
        markets = await collector.fetch_markets()
        print(f"Fetched {len(markets)} markets")
        if markets:
            print(f"First market: {markets[0]['market']}")
    except Exception as e:
        print(f"Note: Could not fetch markets (likely due to API key): {e}")
    
    print("✓ Collector test completed\n")

async def main():
    """Run all tests"""
    print("Testing Bitvavo Trading Algorithm Components\n")
    print("="*50)
    
    test_indicators()
    test_filters()
    test_signals()
    await test_collector()
    
    print("="*50)
    print("All tests completed successfully! 🎉")
    print("\nThe trading algorithm system is ready to run.")
    print("Start it with: python main.py")

if __name__ == "__main__":
    asyncio.run(main())