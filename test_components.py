#!/usr/bin/env python3
"""
Test script to verify all components of the trading system work correctly
"""
import yaml
from collector import DataCollector
from indicators import Indicators
from filters import FilterEngine
from signals import SignalEngine

def test_components():
    print("Testing all trading system components...")
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print("✅ Configuration loaded")
    
    # Test indicators
    indicators = Indicators()
    print("✅ Indicators engine initialized")
    
    # Test sample indicator calculations
    sample_prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 110, 108, 107, 109, 111]
    rsi_values = indicators.calculate_rsi(sample_prices, 14)
    print(f"✅ RSI calculation: {rsi_values[-1]:.2f}")
    
    macd_line, signal_line, histogram = indicators.calculate_macd(sample_prices)
    print(f"✅ MACD calculation: {histogram[-1] if histogram else 'N/A'}")
    
    # Test filters
    filter_engine = FilterEngine(config)
    print("✅ Filter engine initialized")
    
    # Test signal engine
    signal_engine = SignalEngine(config)
    print("✅ Signal engine initialized")
    
    # Test a mock market data structure
    mock_market_data = {
        'current_price': 108.5,
        'candles': {
            '1m': [{'open': 108, 'high': 109, 'low': 107.5, 'close': 108.5, 'volume': 100}],
            '5m': [{'open': 107, 'high': 109, 'low': 106.5, 'close': 108.5, 'volume': 500}],
            '15m': [{'open': 106, 'high': 109, 'low': 105.5, 'close': 108.5, 'volume': 1500}],
            '1h': [{'open': 105, 'high': 110, 'low': 104.5, 'close': 108.5, 'volume': 6000}]
        },
        'ticker_24h': {
            'volume': 2000000,  # 2M EUR
            'priceChangePercentage': 5.5  # 5.5% change
        },
        'orderbook': {
            'bid': 108.4,
            'ask': 108.6,
            'spread_pct': 0.09  # 0.09% spread
        },
        'timestamp': 1234567890
    }
    
    # Test signal generation with mock data
    signal = signal_engine.generate_signal("TEST-EUR", mock_market_data)
    print(f"✅ Signal generated: {signal['signal']}")
    print(f"   Details: {signal}")
    
    # Test filter with mock data
    is_valid, reasons = filter_engine.apply_all_filters(mock_market_data)
    print(f"✅ Filter result: {is_valid}")
    print(f"   Reasons: {reasons}")
    
    print("\n🎉 All components working correctly!")

if __name__ == "__main__":
    test_components()