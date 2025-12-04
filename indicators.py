import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import math


class Indicators:
    @staticmethod
    def calculate_rsi(closes: List[float], period: int = 14) -> List[float]:
        """
        Calculate RSI (Relative Strength Index) using Wilder's EMA method
        """
        if len(closes) < period + 1:
            return [50.0] * len(closes)  # Return neutral value if not enough data
        
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Initialize with simple average for first value
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            rs = 100 if avg_gain > 0 else 50
            rsi_values = [50.0] * period + [rs]
        else:
            rs = avg_gain / avg_loss
            rsi_values = [50.0] * period + [100 - (100 / (1 + rs))]
        
        # Calculate subsequent values using EMA (Wilder's method)
        for i in range(period + 1, len(closes)):
            gain = gains[i-1] if i-1 < len(gains) else 0
            loss = losses[i-1] if i-1 < len(losses) else 0
            
            avg_gain = ((avg_gain * (period - 1)) + gain) / period
            avg_loss = ((avg_loss * (period - 1)) + loss) / period
            
            if avg_loss == 0:
                rs = 100 if avg_gain > 0 else 50
            else:
                rs = avg_gain / avg_loss
            
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        return rsi_values

    @staticmethod
    def calculate_macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """
        Calculate MACD line, signal line, and histogram
        Returns: (macd_line, signal_line, histogram)
        """
        if len(closes) < slow:
            # Return neutral values if not enough data
            return [0.0] * len(closes), [0.0] * len(closes), [0.0] * len(closes)
        
        closes_series = pd.Series(closes)
        
        # Calculate EMAs
        ema_fast = closes_series.ewm(span=fast).mean()
        ema_slow = closes_series.ewm(span=slow).mean()
        
        # Calculate MACD line
        macd_line = (ema_fast - ema_slow).tolist()
        
        # Calculate signal line
        signal_series = pd.Series(macd_line).ewm(span=signal).mean()
        signal_line = signal_series.tolist()
        
        # Calculate histogram
        histogram = (pd.Series(macd_line) - pd.Series(signal_line)).tolist()
        
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
        """
        Calculate Average True Range (ATR)
        """
        if len(closes) < period:
            return [0.0] * len(closes)
        
        tr_values = []
        for i in range(len(highs)):
            if i == 0:
                tr = highs[i] - lows[i]
            else:
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
            tr_values.append(tr)
        
        atr_values = []
        for i in range(len(tr_values)):
            if i < period - 1:
                # Use simple moving average for initial values
                atr_values.append(sum(tr_values[:i+1]) / (i+1) if i > 0 else tr_values[0])
            else:
                # Use ATR formula: ((period-1) * prev_atr + current_tr) / period
                if i == period - 1:
                    atr = sum(tr_values[:period]) / period
                else:
                    atr = ((period - 1) * atr_values[i-1] + tr_values[i]) / period
                atr_values.append(atr)
        
        return atr_values

    @staticmethod
    def calculate_bollinger_bands(closes: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
        """
        Calculate Bollinger Bands (upper, middle, lower)
        Returns: (upper_band, middle_band, lower_band)
        """
        if len(closes) < period:
            # Return neutral values if not enough data
            middle = [np.mean(closes[:i+1]) if i < len(closes) else 0 for i in range(len(closes))]
            return middle, middle, middle
        
        closes_series = pd.Series(closes)
        
        # Calculate middle band (SMA)
        middle_band = closes_series.rolling(window=period).mean().tolist()
        
        # Calculate standard deviation
        rolling_std = closes_series.rolling(window=period).std().tolist()
        
        # Calculate upper and lower bands
        upper_band = []
        lower_band = []
        
        for i in range(len(closes)):
            if i < period - 1:
                # For insufficient data, use available data
                available_data = closes[:i+1]
                ma = sum(available_data) / len(available_data)
                std = np.std(available_data) if len(available_data) > 1 else 0
                upper_band.append(ma + (std_dev * std))
                lower_band.append(ma - (std_dev * std))
            else:
                upper_band.append(middle_band[i] + (std_dev * rolling_std[i]))
                lower_band.append(middle_band[i] - (std_dev * rolling_std[i]))
        
        return upper_band, middle_band, lower_band

    @staticmethod
    def calculate_volatility(closes: List[float], period: int = 14) -> List[float]:
        """
        Calculate rolling volatility as percentage change
        """
        if len(closes) < 2:
            return [0.0] * len(closes)
        
        returns = []
        for i in range(1, len(closes)):
            ret = (closes[i] - closes[i-1]) / closes[i-1] * 100
            returns.append(ret)
        
        volatility = []
        for i in range(len(returns)):
            window_start = max(0, i - period + 1)
            window_returns = returns[window_start:i+1]
            vol = np.std(window_returns) * np.sqrt(252) if window_returns else 0  # Annualized
            volatility.append(vol)
        
        # Add initial 0 for first element
        volatility = [0.0] + volatility
        return volatility

    @staticmethod
    def calculate_volume_relative(current_volume: float, historical_volumes: List[float], period: int = 20) -> float:
        """
        Calculate relative volume (current volume vs average historical volume)
        """
        if not historical_volumes:
            return 1.0  # Neutral if no historical data
        
        # Use the last 'period' values or all if less available
        vol_period = min(period, len(historical_volumes))
        avg_volume = sum(historical_volumes[-vol_period:]) / vol_period
        
        if avg_volume == 0:
            return 1.0  # Neutral if average volume is 0
        
        return current_volume / avg_volume

    @staticmethod
    def find_support_resistance(closes: List[float], period: int = 40) -> Tuple[float, float]:
        """
        Find recent support and resistance levels based on last 'period' candles
        Returns: (support_level, resistance_level)
        """
        if len(closes) < 2:
            if len(closes) == 1:
                return closes[0], closes[0]
            return 0.0, 0.0
        
        # Use the last 'period' closes or all if less available
        recent_closes = closes[-period:] if len(closes) >= period else closes
        
        support = min(recent_closes)
        resistance = max(recent_closes)
        
        return support, resistance

    @staticmethod
    def calculate_pullback(current_price: float, recent_high: float) -> float:
        """
        Calculate pullback percentage from recent high
        """
        if recent_high == 0:
            return 0.0
        return (recent_high - current_price) / recent_high * 100

    @staticmethod
    def calculate_volatility_pct(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
        """
        Calculate volatility as percentage of price range over period
        """
        if len(closes) < period:
            return [0.0] * len(closes)
        
        volatilities = []
        for i in range(len(closes)):
            if i < period - 1:
                # For insufficient data, calculate with available data
                start_idx = 0
                end_idx = i + 1
                period_highs = highs[start_idx:end_idx]
                period_lows = lows[start_idx:end_idx]
                
                if period_highs and period_lows:
                    max_high = max(period_highs)
                    min_low = min(period_lows)
                    min_price = min(closes[start_idx:end_idx])
                    
                    if min_price != 0:
                        vol_pct = (max_high - min_low) / min_price * 100
                    else:
                        vol_pct = 0.0
                else:
                    vol_pct = 0.0
            else:
                # Calculate for full period
                start_idx = i - period + 1
                end_idx = i + 1
                period_highs = highs[start_idx:end_idx]
                period_lows = lows[start_idx:end_idx]
                
                max_high = max(period_highs)
                min_low = min(period_lows)
                min_price = min(closes[start_idx:end_idx])
                
                if min_price != 0:
                    vol_pct = (max_high - min_low) / min_price * 100
                else:
                    vol_pct = 0.0
            
            volatilities.append(vol_pct)
        
        return volatilities