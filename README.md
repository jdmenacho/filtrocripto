# Bitvavo Trading Algorithm

Professional intraday trading algorithm that monitors Bitvavo markets and generates trading signals based on technical analysis and market conditions.

## Features

- **Real-time Data**: Fetches market data from Bitvavo API (REST & WebSocket)
- **Multi-timeframe Analysis**: Analyzes 1m, 5m, 15m, and 1h timeframes
- **Three-stage Filtering**: Basic, volatility, and technical filters
- **Signal Generation**: BUY, SELL, or OBSERVE signals with entry/exit prices
- **Dashboard**: Real-time web dashboard with Bootstrap UI

## Architecture

- `collector.py`: Data collection from Bitvavo API and WebSocket
- `indicators.py`: Technical indicator calculations (RSI, MACD, Bollinger Bands, etc.)
- `filters.py`: Three-stage filtering system for market selection
- `signals.py`: Signal generation based on technical conditions
- `api.py`: FastAPI server with REST endpoints
- `dashboard/index.html`: Web dashboard to display signals
- `main.py`: Main entry point to run the complete system

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your Bitvavo API keys in `config.yaml`
4. Run the system:
   ```bash
   python main.py
   ```

## Usage

1. Start the system: `python main.py`
2. Access the dashboard at: `http://localhost:8000/dashboard/index.html`
3. Monitor the API endpoints:
   - `/api/scan` - Get top trading signals
   - `/api/markets` - Get all EUR markets
   - `/api/market/{market}` - Get specific market details
   - `/api/signals` - Get all current signals

## Signal Logic

### BUY Signal Conditions
A BUY signal is generated when all these conditions are met:
1. **Pullback**: Price has pulled back 0.8% to 1.5% from recent high
2. **Candle Confirmation**: Last 1-2 candles are bullish (close > open)
3. **Support**: Price is within 0.4% of recent support level
4. **Volume**: Current volume is >110% of average volume
5. **MACD Momentum**: Positive momentum in MACD histogram

### SELL Signal Conditions
A SELL signal is generated when:
- Target price is reached
- Price drops more than -0.7% from entry
- RSI 15m exceeds 70 (overbought)
- MACD shows negative momentum

### Risk Management
- Default target: 1.25% profit
- Default stop loss: 1.5% loss
- Position sizing based on risk parameters

## Configuration

Edit `config.yaml` to adjust:
- API endpoints and keys
- Refresh intervals
- Filter thresholds
- Risk parameters

## Dashboard

The dashboard provides:
- Real-time top 10 trading signals
- Signal details (entry price, target, stop loss)
- Market conditions and reasons
- Auto-refresh every 60 seconds