#!/usr/bin/env python3
"""
Main entry point for the Bitvavo Trading Algorithm
This script coordinates all components of the trading system
"""

import asyncio
import yaml
import logging
from collector import DataCollector
from signals import SignalEngine
from api import app
import uvicorn
import threading
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        logger.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise

def run_api_server():
    """Run the API server in a separate thread"""
    logger.info("Starting API server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

async def run_system():
    """Run the complete trading system"""
    logger.info("Starting Bitvavo Trading Algorithm...")
    
    # Load configuration
    config = load_config()
    
    # Initialize components
    data_collector = DataCollector(config)
    signal_engine = SignalEngine(config)
    
    try:
        # Initial data collection
        logger.info("Performing initial data collection...")
        await data_collector.collect_all_data()
        
        # Run the API server in a separate thread to avoid event loop conflicts
        api_thread = threading.Thread(target=run_api_server, daemon=True)
        api_thread.start()
        
        # Run the main data collection loop in the main thread
        logger.info("Starting data collection loop...")
        while True:
            await asyncio.sleep(config['monitor']['refresh_seconds'])
            await data_collector.collect_all_data()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Error running trading system: {e}")
        raise
    finally:
        logger.info("Trading system shutdown complete")

def main():
    """Main function to run the system"""
    try:
        # Run the async event loop
        asyncio.run(run_system())
    except KeyboardInterrupt:
        logger.info("System interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()