from typing import Dict, List, Tuple, Optional
from filters import FilterEngine
from indicators import Indicators
import logging


class SignalEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.filter_engine = FilterEngine(config)
        self.indicators = Indicators()
        self.logger = logging.getLogger(__name__)

    def generate_signal(self, market: str, market_data: Dict) -> Dict:
        """
        Generate a trading signal for a given market
        Returns: signal dictionary with entry price, target, stop loss, etc.
        """
        # Apply all filters first
        is_valid, filter_reasons = self.filter_engine.apply_all_filters(market_data)
        
        if not is_valid:
            return {
                'market': market,
                'signal': 'OBSERVE',
                'reason': 'Did not pass all filters',
                'filter_reasons': filter_reasons,
                'current_price': market_data.get('current_price', 0),
                'timestamp': market_data.get('timestamp', 0)
            }
        
        # If it passes all filters, check for specific entry conditions
        signal_details = self.check_entry_conditions(market, market_data)
        
        return signal_details

    def check_entry_conditions(self, market: str, market_data: Dict) -> Dict:
        """
        Check specific entry conditions to determine if BUY signal is appropriate
        """
        current_price = market_data.get('current_price', 0)
        candles_1m = market_data.get('candles', {}).get('1m', [])
        candles_5m = market_data.get('candles', {}).get('5m', [])
        candles_15m = market_data.get('candles', {}).get('15m', [])
        
        # Get all closes for calculations
        all_closes = [c['close'] for c in candles_1m if c] if candles_1m else [c['close'] for c in candles_5m if c] if candles_5m else [c['close'] for c in candles_15m]
        
        if not all_closes or current_price <= 0:
            return {
                'market': market,
                'signal': 'OBSERVE',
                'reason': 'Insufficient price data',
                'current_price': current_price,
                'timestamp': market_data.get('timestamp', 0)
            }
        
        # Condition 1: Perfect pullback (0.8% to 1.5%)
        recent_high = max(all_closes[-40:]) if len(all_closes) >= 40 else max(all_closes)
        pullback_pct = self.indicators.calculate_pullback(current_price, recent_high)
        
        min_pullback = self.config['filters']['min_pullback_pct']
        max_pullback = self.config['filters']['max_pullback_pct']
        
        pullback_ok = min_pullback <= pullback_pct <= max_pullback
        
        # Condition 2: Candle confirmation (1m or 5m)
        candle_confirmation = False
        if len(candles_1m) >= 2:
            # Check if last 2 candles are bullish (close > open)
            last_candle = candles_1m[-1]
            prev_candle = candles_1m[-2]
            candle_confirmation = (last_candle['close'] > last_candle['open'] and 
                                 prev_candle['close'] > prev_candle['open'])
        elif len(candles_5m) >= 2:
            # Check if last 2 5m candles are bullish
            last_candle = candles_5m[-1]
            prev_candle = candles_5m[-2]
            candle_confirmation = (last_candle['close'] > last_candle['open'] and 
                                 prev_candle['close'] > prev_candle['open'])
        
        # Condition 3: Near support
        support, resistance = self.indicators.find_support_resistance(all_closes, 40)
        if support > 0:
            support_distance_pct = abs((current_price - support) / support * 100)
            near_support = support_distance_pct <= 0.4  # Within 0.4% of support
        else:
            near_support = False
        
        # Condition 4: Volume above average
        volume_above_average = False
        if candles_1m and len(candles_1m) >= 100:
            current_volume = sum([c['volume'] for c in candles_1m[-5:]])
            avg_volume = sum([c['volume'] for c in candles_1m[-100:-5]]) / 95
            if avg_volume > 0:
                vol_ratio = current_volume / avg_volume
                volume_above_average = vol_ratio >= 1.10  # 110% of average
        elif candles_5m and len(candles_5m) >= 20:
            current_volume = sum([c['volume'] for c in candles_5m[-3:]])
            avg_volume = sum([c['volume'] for c in candles_5m[-20:-3]]) / 17
            if avg_volume > 0:
                vol_ratio = current_volume / avg_volume
                volume_above_average = vol_ratio >= 1.10
        
        # Condition 5: Positive MACD momentum
        macd_positive = False
        if len(candles_5m) >= 26:
            closes_5m = [c['close'] for c in candles_5m]
            macd_line, signal_line, histogram = self.indicators.calculate_macd(closes_5m)
            if histogram and histogram[-1] > histogram[-2] if len(histogram) >= 2 else histogram[-1] > 0:
                macd_positive = True  # MACD showing positive momentum
        elif len(candles_15m) >= 26:
            closes_15m = [c['close'] for c in candles_15m]
            macd_line, signal_line, histogram = self.indicators.calculate_macd(closes_15m)
            if histogram and histogram[-1] > histogram[-2] if len(histogram) >= 2 else histogram[-1] > 0:
                macd_positive = True

        # Determine final signal based on conditions
        conditions_met = sum([pullback_ok, candle_confirmation, near_support, volume_above_average, macd_positive])
        
        if conditions_met >= 4:  # At least 4 out of 5 conditions met
            # Calculate entry price, target, and stop loss
            entry_price = current_price * (1 - pullback_pct/100)
            target_price = entry_price * (1 + self.config['risk']['tp_pct'])  # e.g., 1.0125 for 1.25%
            stop_loss = entry_price * (1 - self.config['risk']['sl_pct'])  # e.g., 0.985 for 1.5% stop loss
            
            return {
                'market': market,
                'signal': 'BUY',
                'reason': f'All conditions met: pullback={pullback_pct:.2f}%, candle_conf={candle_confirmation}, near_support={near_support}, volume_high={volume_above_average}, macd_positive={macd_positive}',
                'current_price': current_price,
                'entry_price': round(entry_price, 6),
                'target_price': round(target_price, 6),
                'stop_loss': round(stop_loss, 6),
                'pullback_pct': round(pullback_pct, 2),
                'conditions_met': conditions_met,
                'total_conditions': 5,
                'timestamp': market_data.get('timestamp', 0)
            }
        elif conditions_met >= 2:  # Some conditions met but not enough for buy
            return {
                'market': market,
                'signal': 'OBSERVE',
                'reason': f'Some conditions met ({conditions_met}/5) but not enough for entry',
                'current_price': current_price,
                'pullback_pct': round(pullback_pct, 2),
                'conditions_met': conditions_met,
                'total_conditions': 5,
                'details': {
                    'pullback_ok': pullback_ok,
                    'candle_confirmation': candle_confirmation,
                    'near_support': near_support,
                    'volume_above_average': volume_above_average,
                    'macd_positive': macd_positive
                },
                'timestamp': market_data.get('timestamp', 0)
            }
        else:
            return {
                'market': market,
                'signal': 'OBSERVE',
                'reason': f'Few conditions met ({conditions_met}/5), not suitable for entry',
                'current_price': current_price,
                'pullback_pct': round(pullback_pct, 2),
                'conditions_met': conditions_met,
                'total_conditions': 5,
                'timestamp': market_data.get('timestamp', 0)
            }

    def check_exit_conditions(self, position: Dict, market_data: Dict) -> str:
        """
        Check if exit conditions are met for an existing position
        Returns: 'SELL', 'HOLD', or 'STOP_LOSS'
        """
        current_price = market_data.get('current_price', 0)
        entry_price = position.get('entry_price', 0)
        
        if current_price <= 0 or entry_price <= 0:
            return 'HOLD'
        
        # Check if target is reached
        target_price = position.get('target_price', entry_price * 1.0125)  # Default 1.25% target
        if current_price >= target_price:
            return 'SELL'
        
        # Check if stop loss is triggered
        stop_loss = position.get('stop_loss', entry_price * 0.985)  # Default 1.5% stop loss
        if current_price <= stop_loss:
            return 'STOP_LOSS'
        
        # Check if price moved against position by more than threshold
        price_change_pct = (current_price - entry_price) / entry_price * 100
        if price_change_pct <= -0.7:  # More than -0.7% against position
            return 'SELL'
        
        # Check RSI for overbought conditions
        candles_15m = market_data.get('candles', {}).get('15m', [])
        if len(candles_15m) >= 15:
            closes_15m = [c['close'] for c in candles_15m]
            rsi_values = self.indicators.calculate_rsi(closes_15m, 14)
            rsi_15m = rsi_values[-1] if rsi_values else 50
            
            if rsi_15m > 70:  # Overbought
                return 'SELL'
        
        # Check MACD for negative momentum
        if len(candles_5m) >= 26:
            closes_5m = [c['close'] for c in candles_5m]
            macd_line, signal_line, histogram = self.indicators.calculate_macd(closes_5m)
            if histogram and len(histogram) >= 2:
                # Check if MACD is turning negative (momentum shift)
                if histogram[-1] < 0 and histogram[-2] >= 0:
                    return 'SELL'
        
        return 'HOLD'