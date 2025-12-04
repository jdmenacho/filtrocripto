from typing import Dict, List, Tuple, Optional
from indicators import Indicators
import logging


class FilterEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.indicators = Indicators()
        self.logger = logging.getLogger(__name__)

    def apply_all_filters(self, market_data: Dict) -> Tuple[bool, List[str]]:
        """
        Apply all three filters to determine if a market is suitable for trading
        Returns: (is_valid, list_of_reasons)
        """
        reasons = []
        
        # Filter 1: Basic Filter
        basic_valid, basic_reasons = self.filter_basic(market_data)
        if not basic_valid:
            return False, basic_reasons
        
        reasons.extend(basic_reasons)
        
        # Filter 2: Volatility Filter
        vol_valid, vol_reasons = self.filter_volatility(market_data)
        if not vol_valid:
            return False, reasons + vol_reasons
        
        reasons.extend(vol_reasons)
        
        # Filter 3: Technical Filter
        tech_valid, tech_reasons = self.filter_technical(market_data)
        if not tech_valid:
            return False, reasons + tech_reasons
        
        reasons.extend(tech_reasons)
        
        return True, reasons

    def filter_basic(self, market_data: Dict) -> Tuple[bool, List[str]]:
        """
        FILTRO 1 — Filtro Básico
        - volumen_24h > 1,000,000 EUR
        - priceChangePercentage_24h abs() > 4%
        - spread_pct < 0.5%
        """
        reasons = []
        ticker = market_data.get('ticker_24h', {})
        book = market_data.get('orderbook', {})
        
        # Check 24h volume
        volume_24h = ticker.get('volume', 0)
        min_vol = self.config['filters']['min_vol_24h_eur']
        if volume_24h < min_vol:
            return False, [f"Volume too low: {volume_24h} < {min_vol} EUR"]
        
        reasons.append(f"Volume OK: {volume_24h:,.0f} EUR")
        
        # Check 24h price change percentage
        change_pct = abs(ticker.get('priceChangePercentage', 0))
        min_change = self.config['filters']['min_change_24h_pct']
        if change_pct < min_change:
            return False, [f"Price change too low: {change_pct:.2f}% < {min_change}%"]
        
        reasons.append(f"Price change OK: {change_pct:.2f}%")
        
        # Check spread percentage
        spread_pct = book.get('spread_pct', float('inf'))
        max_spread = self.config['filters']['max_spread_pct']
        if spread_pct > max_spread:
            return False, [f"Spread too high: {spread_pct:.3f}% > {max_spread}%"]
        
        reasons.append(f"Spread OK: {spread_pct:.3f}%")
        
        return True, reasons

    def filter_volatility(self, market_data: Dict) -> Tuple[bool, List[str]]:
        """
        FILTRO 2 — Filtro de Volatilidad Intradía
        - volatilidad_1h > 1.8%
        - volatilidad_15m > 0.6%
        - volumen 1h > 120% del volumen medio horario
        """
        reasons = []
        
        # Get candles for different timeframes
        candles_1h = market_data.get('candles', {}).get('1h', [])
        candles_15m = market_data.get('candles', {}).get('15m', [])
        candles_1m = market_data.get('candles', {}).get('1m', [])
        
        if len(candles_1h) < 2:
            return False, ["Not enough 1h candles for volatility calculation"]
        
        if len(candles_15m) < 2:
            return False, ["Not enough 15m candles for volatility calculation"]
        
        # Calculate 1h volatility
        closes_1h = [c['close'] for c in candles_1h]
        highs_1h = [c['high'] for c in candles_1h]
        lows_1h = [c['low'] for c in candles_1h]
        
        # Calculate volatility as percentage of price range
        max_high_1h = max(highs_1h)
        min_low_1h = min(lows_1h)
        min_price_1h = min(closes_1h)
        
        if min_price_1h == 0:
            return False, ["Invalid price for 1h volatility calculation"]
        
        vol_1h_pct = (max_high_1h - min_low_1h) / min_price_1h * 100
        min_vol_1h = self.config['filters']['min_volatility_1h_pct']
        
        if vol_1h_pct < min_vol_1h:
            return False, [f"1h volatility too low: {vol_1h_pct:.2f}% < {min_vol_1h}%"]
        
        reasons.append(f"1h volatility OK: {vol_1h_pct:.2f}%")
        
        # Calculate 15m volatility
        if len(candles_15m) >= 2:
            closes_15m = [c['close'] for c in candles_15m]
            highs_15m = [c['high'] for c in candles_15m]
            lows_15m = [c['low'] for c in candles_15m]
            
            max_high_15m = max(highs_15m)
            min_low_15m = min(lows_15m)
            min_price_15m = min(closes_15m)
            
            if min_price_15m != 0:
                vol_15m_pct = (max_high_15m - min_low_15m) / min_price_15m * 100
                min_vol_15m = self.config['filters']['min_volatility_15m_pct']
                
                if vol_15m_pct < min_vol_15m:
                    return False, [f"15m volatility too low: {vol_15m_pct:.2f}% < {min_vol_15m}%"]
                
                reasons.append(f"15m volatility OK: {vol_15m_pct:.2f}%")
            else:
                return False, ["Invalid price for 15m volatility calculation"]
        else:
            return False, ["Not enough 15m candles"]
        
        # Check 1h volume relative to average
        # Calculate average volume from recent candles
        if len(candles_1m) >= 60:  # At least 1 hour of 1m candles
            recent_volumes = [c['volume'] for c in candles_1m[-60:]]  # Last hour
            avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
            
            current_volume = sum(recent_volumes)  # Sum of last hour volumes
            if avg_volume > 0:
                vol_ratio = current_volume / avg_volume if avg_volume > 0 else float('inf')
                if vol_ratio < 1.2:  # Less than 120% of average
                    return False, [f"Volume not high enough: {vol_ratio:.2f}x < 1.2x average"]
                reasons.append(f"Volume OK: {vol_ratio:.2f}x average")
            else:
                return False, ["Average volume is zero, cannot calculate ratio"]
        else:
            # Use 1h candle volume if 1m candles not available
            if candles_1h:
                current_vol = candles_1h[-1]['volume']
                # Use a simple average of the last few 1h candles
                if len(candles_1h) >= 5:
                    avg_vol = sum([c['volume'] for c in candles_1h[-5:]]) / 5
                    if avg_vol > 0:
                        vol_ratio = current_vol / avg_vol
                        if vol_ratio < 1.2:
                            return False, [f"1h volume not high enough: {vol_ratio:.2f}x < 1.2x average"]
                        reasons.append(f"1h Volume OK: {vol_ratio:.2f}x average")
                    else:
                        return False, ["1h average volume is zero"]
                else:
                    reasons.append("Insufficient 1h candles for volume comparison, proceeding")
        
        return True, reasons

    def filter_technical(self, market_data: Dict) -> Tuple[bool, List[str]]:
        """
        FILTRO 3 — Filtro Técnico
        - RSI 15m between 35 and 55
        - MACD 5m and 15m with non-negative momentum
        - Pullback between 0.8% and 1.5%
        - Price near support (distance < 0.4%)
        - Current volume > 110% of average volume
        """
        reasons = []
        
        # Get candles
        candles_15m = market_data.get('candles', {}).get('15m', [])
        candles_5m = market_data.get('candles', {}).get('5m', [])
        candles_1m = market_data.get('candles', {}).get('1m', [])
        
        current_price = market_data.get('current_price', 0)
        if current_price <= 0:
            return False, ["Invalid current price"]
        
        # Calculate RSI 14 on 15m timeframe
        if len(candles_15m) >= 15:  # Need at least 15 candles for RSI 14
            closes_15m = [c['close'] for c in candles_15m]
            rsi_15m_values = self.indicators.calculate_rsi(closes_15m, 14)
            rsi_15m = rsi_15m_values[-1] if rsi_15m_values else 50
            
            rsi_min = self.config['filters']['rsi_min']
            rsi_max = self.config['filters']['rsi_max']
            
            if not (rsi_min <= rsi_15m <= rsi_max):
                return False, [f"RSI 15m not in range [{rsi_min}, {rsi_max}]: {rsi_15m:.2f}"]
            
            reasons.append(f"RSI 15m OK: {rsi_15m:.2f}")
        else:
            return False, ["Not enough 15m candles for RSI calculation"]
        
        # Calculate MACD on 5m timeframe
        if len(candles_5m) >= 26:  # Need at least 26 candles for MACD (26 is slow EMA period)
            closes_5m = [c['close'] for c in candles_5m]
            macd_line, signal_line, histogram = self.indicators.calculate_macd(closes_5m)
            
            if histogram:
                macd_5m_momentum = histogram[-1]  # Use histogram as momentum indicator
                # Check if momentum is non-negative (bullish)
                if macd_5m_momentum < 0:
                    return False, [f"MACD 5m momentum negative: {macd_5m_momentum:.4f}"]
                reasons.append(f"MACD 5m momentum OK: {macd_5m_momentum:.4f}")
            else:
                return False, ["Could not calculate MACD 5m"]
        else:
            return False, ["Not enough 5m candles for MACD calculation"]
        
        # Calculate MACD on 15m timeframe
        if len(candles_15m) >= 26:
            closes_15m = [c['close'] for c in candles_15m]
            macd_line, signal_line, histogram = self.indicators.calculate_macd(closes_15m)
            
            if histogram:
                macd_15m_momentum = histogram[-1]
                # Check if momentum is non-negative (bullish)
                if macd_15m_momentum < 0:
                    return False, [f"MACD 15m momentum negative: {macd_15m_momentum:.4f}"]
                reasons.append(f"MACD 15m momentum OK: {macd_15m_momentum:.4f}")
            else:
                return False, ["Could not calculate MACD 15m"]
        else:
            return False, ["Not enough 15m candles for MACD 15m calculation"]
        
        # Calculate pullback from recent high
        # Use the highest high from the last 40 candles as the recent high
        lookback_period = 40
        all_closes = [c['close'] for c in candles_1m if c] if candles_1m else [c['close'] for c in candles_5m if c] if candles_5m else [c['close'] for c in candles_15m]
        
        if len(all_closes) >= 2:
            recent_high = max(all_closes[-lookback_period:]) if len(all_closes) >= lookback_period else max(all_closes)
            pullback_pct = self.indicators.calculate_pullback(current_price, recent_high)
            
            min_pullback = self.config['filters']['min_pullback_pct']
            max_pullback = self.config['filters']['max_pullback_pct']
            
            if not (min_pullback <= pullback_pct <= max_pullback):
                return False, [f"Pullback not in range [{min_pullback}%, {max_pullback}%]: {pullback_pct:.2f}%"]
            
            reasons.append(f"Pullback OK: {pullback_pct:.2f}%")
        else:
            return False, ["Not enough price data to calculate pullback"]
        
        # Find support level (from last 40 candles)
        if len(all_closes) >= 2:
            support, resistance = self.indicators.find_support_resistance(all_closes, 40)
            if support > 0:
                support_distance_pct = (current_price - support) / support * 100
                max_support_distance = 0.4  # 0.4%
                
                if abs(support_distance_pct) > max_support_distance:
                    return False, [f"Price too far from support: {support_distance_pct:.2f}% > {max_support_distance}%"]
                
                reasons.append(f"Near support: {support_distance_pct:.2f}%")
            else:
                return False, ["Could not determine support level"]
        else:
            return False, ["Not enough data to find support level"]
        
        # Check volume relative to average
        if candles_1m:
            current_volume = sum([c['volume'] for c in candles_1m[-5:]])  # Last 5 minutes
            if len(candles_1m) >= 100:  # Need enough data for average
                avg_volume = sum([c['volume'] for c in candles_1m[-100:-5]]) / 95  # Average of previous 95 minutes
                if avg_volume > 0:
                    vol_ratio = current_volume / avg_volume
                    min_vol_ratio = 1.10  # 110% of average
                    
                    if vol_ratio < min_vol_ratio:
                        return False, [f"Volume below threshold: {vol_ratio:.2f}x < {min_vol_ratio}x average"]
                    
                    reasons.append(f"Volume OK: {vol_ratio:.2f}x average")
                else:
                    return False, ["Average volume is zero"]
            else:
                # Use 5m candles if 1m not sufficient
                if len(candles_5m) >= 20:
                    current_vol_5m = sum([c['volume'] for c in candles_5m[-3:]])  # Last 3 5m candles
                    avg_vol_5m = sum([c['volume'] for c in candles_5m[-20:-3]]) / 17  # Average of previous 17 candles
                    if avg_vol_5m > 0:
                        vol_ratio = current_vol_5m / avg_vol_5m
                        min_vol_ratio = 1.10
                        if vol_ratio < min_vol_ratio:
                            return False, [f"Volume below threshold: {vol_ratio:.2f}x < {min_vol_ratio}x average"]
                        reasons.append(f"Volume OK: {vol_ratio:.2f}x average")
                    else:
                        return False, ["Average volume is zero (5m)"]
                else:
                    reasons.append("Insufficient volume data, proceeding")
        else:
            reasons.append("No 1m candles for volume check, using 5m")
        
        return True, reasons