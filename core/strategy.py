"""
Zero to Hero - EMA Crossover Strategy
Author: Md Moniruzzaman
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Signal(Enum):
    """Trading signals"""
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


@dataclass
class SignalResult:
    """Signal analysis result"""
    symbol: str
    signal: Signal
    ema_fast: float
    ema_slow: float
    current_price: float
    crossover_detected: bool
    timestamp: str


class EMAStrategy:
    """
    EMA 9/21 Crossover Strategy
    
    - LONG: EMA 9 crosses above EMA 21 (bullish crossover)
    - SHORT: EMA 9 crosses below EMA 21 (bearish crossover)
    """
    
    def __init__(self, fast_period: int = 9, slow_period: int = 21):
        self.fast_period = fast_period
        self.slow_period = slow_period
        logger.info(f"EMA Strategy initialized: {fast_period}/{slow_period}")
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add EMA indicators to dataframe"""
        if df.empty or len(df) < self.slow_period:
            return df
        
        df = df.copy()
        df['ema_fast'] = self.calculate_ema(df['close'], self.fast_period)
        df['ema_slow'] = self.calculate_ema(df['close'], self.slow_period)
        
        # Calculate crossover signals
        df['ema_diff'] = df['ema_fast'] - df['ema_slow']
        df['ema_diff_prev'] = df['ema_diff'].shift(1)
        
        # Bullish crossover: Fast EMA crosses above Slow EMA
        df['bullish_cross'] = (df['ema_diff'] > 0) & (df['ema_diff_prev'] <= 0)
        
        # Bearish crossover: Fast EMA crosses below Slow EMA
        df['bearish_cross'] = (df['ema_diff'] < 0) & (df['ema_diff_prev'] >= 0)
        
        return df
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> SignalResult:
        """Analyze data and generate trading signal"""
        
        if df.empty or len(df) < self.slow_period + 2:
            return SignalResult(
                symbol=symbol,
                signal=Signal.NONE,
                ema_fast=0,
                ema_slow=0,
                current_price=0,
                crossover_detected=False,
                timestamp=""
            )
        
        # Add indicators
        df = self.add_indicators(df)
        
        # Get latest values
        latest = df.iloc[-1]
        current_price = latest['close']
        ema_fast = latest['ema_fast']
        ema_slow = latest['ema_slow']
        timestamp = str(latest['timestamp'])
        
        # Check for crossover in last candle
        signal = Signal.NONE
        crossover_detected = False
        
        if latest['bullish_cross']:
            signal = Signal.LONG
            crossover_detected = True
            logger.info(f"🟢 BULLISH crossover on {symbol} - EMA{self.fast_period}: {ema_fast:.6f}, EMA{self.slow_period}: {ema_slow:.6f}")
        
        elif latest['bearish_cross']:
            signal = Signal.SHORT
            crossover_detected = True
            logger.info(f"🔴 BEARISH crossover on {symbol} - EMA{self.fast_period}: {ema_fast:.6f}, EMA{self.slow_period}: {ema_slow:.6f}")
        
        return SignalResult(
            symbol=symbol,
            signal=signal,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            current_price=current_price,
            crossover_detected=crossover_detected,
            timestamp=timestamp
        )
    
    def get_trend(self, df: pd.DataFrame) -> str:
        """Get current trend based on EMA position"""
        if df.empty or len(df) < self.slow_period:
            return "NEUTRAL"
        
        df = self.add_indicators(df)
        latest = df.iloc[-1]
        
        if latest['ema_fast'] > latest['ema_slow']:
            return "BULLISH"
        elif latest['ema_fast'] < latest['ema_slow']:
            return "BEARISH"
        else:
            return "NEUTRAL"
