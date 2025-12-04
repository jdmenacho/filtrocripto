import asyncio
import aiohttp
import websockets
import json
import time
import logging
from typing import Dict, List, Optional, Deque
from collections import deque
import pandas as pd
from datetime import datetime

class DataCollector:
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config['bitvavo']['base_url']
        self.api_key = config['bitvavo']['api_key']
        self.api_secret = config['bitvavo']['api_secret']
        
        # Memory cache structures
        self.markets_cache: Dict = {}
        self.candles_cache: Dict[tuple, Deque] = {}  # {(market, timeframe): deque}
        self.ticker_cache: Dict = {}
        self.book_cache: Dict = {}
        
        # WebSocket connection
        self.ws_url = "wss://ws.bitvavo.com/v2/"
        self.ws_connection = None
        self.running = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def fetch_markets(self) -> List[Dict]:
        """A1. Fetch all markets from Bitvavo API"""
        url = f"{self.base_url}/markets"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        markets = await response.json()
                        # Filter markets with quoteAsset = EUR
                        eur_markets = [m for m in markets if m.get('quoteAsset') == 'EUR']
                        self.markets_cache = {m['market']: m for m in eur_markets}
                        self.logger.info(f"Fetched {len(eur_markets)} EUR markets")
                        return eur_markets
                    else:
                        self.logger.error(f"Failed to fetch markets: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Error fetching markets: {e}")
            return []

    async def fetch_candles(self, market: str, interval: str, limit: int = 100) -> List[Dict]:
        """A3. Fetch OHLCV candles for a given market and interval"""
        url = f"{self.base_url}/markets/{market}/candles"
        params = {
            'interval': interval,
            'limit': limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        candles_data = await response.json()
                        # Convert to structured format: [{'open': ..., 'high': ..., 'low': ..., 'close': ..., 'volume': ..., 'timestamp': ...}]
                        candles = []
                        for candle in candles_data:
                            candles.append({
                                'timestamp': candle[0],
                                'open': float(candle[1]),
                                'high': float(candle[2]),
                                'low': float(candle[3]),
                                'close': float(candle[4]),
                                'volume': float(candle[5])
                            })
                        
                        # Store in cache
                        cache_key = (market, interval)
                        self.candles_cache[cache_key] = deque(candles, maxlen=limit)
                        return candles
                    else:
                        self.logger.error(f"Failed to fetch candles for {market} {interval}: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Error fetching candles for {market} {interval}: {e}")
            return []

    async def fetch_ticker_24h(self, market: str) -> Optional[Dict]:
        """A4. Fetch 24h ticker data for a specific market"""
        url = f"{self.base_url}/markets/{market}/ticker/24h"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        ticker_data = await response.json()
                        self.ticker_cache[market] = ticker_data
                        return ticker_data
                    else:
                        self.logger.error(f"Failed to fetch 24h ticker for {market}: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Error fetching 24h ticker for {market}: {e}")
            return None

    async def connect_websocket(self):
        """Connect to Bitvavo WebSocket for real-time data"""
        try:
            self.ws_connection = await websockets.connect(self.ws_url)
            self.running = True
            self.logger.info("Connected to Bitvavo WebSocket")
            
            # Subscribe to orderbook updates for important markets
            # For now, we'll just listen for all updates
            subscribe_msg = {
                "action": "subscribe",
                "channels": [
                    {"name": "book", "markets": list(self.markets_cache.keys())[:10]}  # Limit to first 10 markets
                ]
            }
            
            await self.ws_connection.send(json.dumps(subscribe_msg))
            
            while self.running:
                try:
                    message = await asyncio.wait_for(self.ws_connection.recv(), timeout=1.0)
                    await self.handle_websocket_message(message)
                except asyncio.TimeoutError:
                    continue  # Continue loop, check if still running
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("WebSocket connection closed, reconnecting...")
                    await self.reconnect_websocket()
                    break
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
            await self.reconnect_websocket()

    async def reconnect_websocket(self):
        """Reconnect to WebSocket if connection is lost"""
        self.logger.info("Attempting to reconnect to WebSocket...")
        await asyncio.sleep(5)  # Wait before reconnecting
        await self.connect_websocket()

    async def handle_websocket_message(self, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            if data.get('type') == 'book':
                # A2. Handle orderbook updates
                market = data.get('market')
                bids = data.get('bids', [])
                asks = data.get('asks', [])
                
                if bids and asks:
                    highest_bid = float(bids[0][0])
                    lowest_ask = float(asks[0][0])
                    
                    # Calculate spread percentage
                    spread_pct = (lowest_ask - highest_bid) / lowest_ask * 100
                    
                    # Store in cache
                    self.book_cache[market] = {
                        'bid': highest_bid,
                        'ask': lowest_ask,
                        'spread_pct': spread_pct
                    }
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")

    def get_cached_candles(self, market: str, timeframe: str) -> List[Dict]:
        """Get cached candles for a specific market and timeframe"""
        cache_key = (market, timeframe)
        if cache_key in self.candles_cache:
            return list(self.candles_cache[cache_key])
        return []

    def get_cached_ticker(self, market: str) -> Optional[Dict]:
        """Get cached ticker for a specific market"""
        return self.ticker_cache.get(market)

    def get_cached_book(self, market: str) -> Optional[Dict]:
        """Get cached orderbook for a specific market"""
        return self.book_cache.get(market)

    async def collect_all_data(self):
        """Main method to collect all necessary data"""
        self.logger.info("Starting data collection...")
        
        # Fetch markets first
        markets = await self.fetch_markets()
        
        if not markets:
            self.logger.error("No markets found, cannot continue")
            return
        
        # Fetch data for each market
        for market in list(self.markets_cache.keys())[:5]:  # Limit to first 5 markets for testing
            # Fetch 24h ticker
            await self.fetch_ticker_24h(market)
            
            # Fetch candles for different timeframes
            for interval in ['1m', '5m', '15m', '1h']:
                await self.fetch_candles(market, interval)
        
        self.logger.info("Data collection completed")

    async def run(self):
        """Main run loop"""
        await self.collect_all_data()
        
        # Start WebSocket connection in background
        ws_task = asyncio.create_task(self.connect_websocket())
        
        try:
            while True:
                await asyncio.sleep(self.config['monitor']['refresh_seconds'])
                await self.collect_all_data()
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.running = False
            if self.ws_connection:
                await self.ws_connection.close()
            ws_task.cancel()