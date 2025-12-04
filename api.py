from fastapi import FastAPI, HTTPException
from typing import Dict, List
import yaml
import asyncio
import logging
from collector import DataCollector
from signals import SignalEngine
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

app = FastAPI(title="Bitvavo Trading Algorithm API", version="1.0.0")

# Global instances
data_collector = DataCollector(config)
signal_engine = SignalEngine(config)

# Global storage for market data and signals
market_data_store = {}
signals_store = {}

@app.on_event('startup')
async def startup_event():
    """Initialize the data collector on startup"""
    logger.info("Starting data collection...")
    # Run data collection in background
    asyncio.create_task(data_collector.run())

@app.get("/api/markets")
async def get_markets():
    """Get list of all EUR markets"""
    try:
        markets = await data_collector.fetch_markets()
        return {"markets": markets}
    except Exception as e:
        logger.error(f"Error fetching markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scan")
async def scan_markets(top: int = 10):
    """Scan all markets and return top opportunities"""
    try:
        # Refresh market data
        await data_collector.collect_all_data()
        
        # Get all markets
        markets = list(data_collector.markets_cache.keys())
        
        # Generate signals for each market
        signals = []
        for market in markets[:10]:  # Limit to first 10 for performance
            # Prepare market data
            market_info = {
                'current_price': 0,
                'candles': {},
                'ticker_24h': data_collector.get_cached_ticker(market) or {},
                'orderbook': data_collector.get_cached_book(market) or {},
                'timestamp': datetime.now().timestamp()
            }
            
            # Get candles for different timeframes
            for tf in ['1m', '5m', '15m', '1h']:
                candles = data_collector.get_cached_candles(market, tf)
                market_info['candles'][tf] = candles
            
            # Get current price from ticker or last candle
            ticker = market_info['ticker_24h']
            if ticker and 'last' in ticker:
                market_info['current_price'] = float(ticker['last'])
            elif market_info['candles']['1m']:
                market_info['current_price'] = market_info['candles']['1m'][-1]['close']
            
            # Generate signal
            signal = signal_engine.generate_signal(market, market_info)
            signals.append(signal)
        
        # Sort signals by quality (prioritize BUY signals, then by conditions met)
        signals.sort(key=lambda x: (
            0 if x['signal'] == 'BUY' else 
            1 if x['signal'] == 'OBSERVE' else 2,
            -x.get('conditions_met', 0) if x.get('conditions_met') else 0
        ))
        
        # Return top N signals
        top_signals = signals[:top]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "top_signals": top_signals,
            "total_markets": len(markets),
            "scanned_markets": len(signals)
        }
    except Exception as e:
        logger.error(f"Error scanning markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/{market}")
async def get_market_details(market: str):
    """Get detailed information for a specific market"""
    try:
        # Ensure market exists
        if market not in data_collector.markets_cache:
            markets = await data_collector.fetch_markets()
            if market not in data_collector.markets_cache:
                raise HTTPException(status_code=404, detail="Market not found")
        
        # Prepare market data
        market_info = {
            'current_price': 0,
            'candles': {},
            'ticker_24h': data_collector.get_cached_ticker(market) or {},
            'orderbook': data_collector.get_cached_book(market) or {},
            'timestamp': datetime.now().timestamp()
        }
        
        # Get candles for different timeframes
        for tf in ['1m', '5m', '15m', '1h']:
            candles = data_collector.get_cached_candles(market, tf)
            market_info['candles'][tf] = candles
        
        # Get current price
        ticker = market_info['ticker_24h']
        if ticker and 'last' in ticker:
            market_info['current_price'] = float(ticker['last'])
        elif market_info['candles']['1m']:
            market_info['current_price'] = market_info['candles']['1m'][-1]['close']
        
        # Generate signal
        signal = signal_engine.generate_signal(market, market_info)
        
        return {
            "market": market,
            "market_info": market_info,
            "signal": signal
        }
    except Exception as e:
        logger.error(f"Error getting market details for {market}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/signals")
async def get_all_signals():
    """Get all current signals"""
    try:
        # This would return the last calculated signals
        # For now, we'll run a quick scan
        response = await scan_markets(top=20)
        return response
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)