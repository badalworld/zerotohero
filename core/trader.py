"""
Zero to Hero - Main Trader Engine
Author: Md Moniruzzaman
"""

import time
import threading
from datetime import datetime
from typing import List, Dict, Optional
import logging

from config.settings import settings, TradingConfig
from core.binance_client import BinanceClient, binance_client
from core.strategy import EMAStrategy, Signal
from core.position_manager import PositionManager, PositionSide, PositionStatus

logger = logging.getLogger(__name__)


class Trader:
    """Main trading engine"""
    
    def __init__(self):
        self.settings = settings
        self.config = settings.trading_config
        self.client = binance_client
        self.strategy = EMAStrategy(
            fast_period=self.config.ema_fast,
            slow_period=self.config.ema_slow
        )
        self.position_manager = PositionManager(max_positions=self.config.max_open_trades)
        
        self.running = False
        self.trading_thread: Optional[threading.Thread] = None
        self.symbols: List[str] = []
        self.scan_interval = 60  # seconds
        self.last_scan_time: Optional[datetime] = None
        self.scan_results: List[dict] = []
        self.logs: List[dict] = []
        
        logger.info("Trader initialized")
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add log entry"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        if len(self.logs) > 1000:
            self.logs = self.logs[-500:]
        
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    def initialize(self) -> bool:
        """Initialize trader"""
        self.add_log("Initializing trader...")
        
        # Connect to Binance
        if not self.client.connect():
            self.add_log("Failed to connect to Binance", "ERROR")
            return False
        
        # Get all trading symbols
        self.symbols = self.client.get_all_usdt_futures_symbols()
        if not self.symbols:
            self.add_log("No trading symbols found", "ERROR")
            return False
        
        self.add_log(f"Loaded {len(self.symbols)} trading pairs")
        self.add_log(f"Trading mode: {self.settings.get_mode_string()}")
        return True
    
    def calculate_sl_tp_prices(
        self,
        entry_price: float,
        side: str,
        quantity: float
    ) -> tuple:
        """Calculate stop loss and take profit prices"""
        # SL = $1 loss, TP = $0.20 profit
        sl_amount = self.config.stop_loss_usd
        tp_amount = self.config.take_profit_usd
        
        # Price change per unit for target PnL
        sl_price_change = sl_amount / quantity
        tp_price_change = tp_amount / quantity
        
        if side == "LONG":
            stop_loss_price = entry_price - sl_price_change
            take_profit_price = entry_price + tp_price_change
        else:  # SHORT
            stop_loss_price = entry_price + sl_price_change
            take_profit_price = entry_price - tp_price_change
        
        return stop_loss_price, take_profit_price
    
    def open_trade(self, symbol: str, signal: Signal) -> bool:
        """Open a new trade"""
        try:
            # Check if can open position
            if not self.position_manager.can_open_position():
                self.add_log(f"Max positions reached, skipping {symbol}", "WARNING")
                return False
            
            if self.position_manager.has_position(symbol):
                self.add_log(f"Position already exists for {symbol}", "WARNING")
                return False
            
            # Set leverage
            self.client.set_leverage(symbol, self.config.leverage)
            self.client.set_margin_type(symbol, "ISOLATED")
            
            # Calculate quantity
            quantity = self.client.calculate_quantity(
                symbol,
                self.config.position_size_usd,
                self.config.leverage
            )
            
            if quantity == 0:
                self.add_log(f"Invalid quantity for {symbol}", "ERROR")
                return False
            
            # Determine side
            if signal == Signal.LONG:
                side = "BUY"
                position_side = PositionSide.LONG
            else:
                side = "SELL"
                position_side = PositionSide.SHORT
            
            # Get current price
            entry_price = self.client.get_symbol_price(symbol)
            
            # Calculate SL/TP
            sl_price, tp_price = self.calculate_sl_tp_prices(entry_price, signal.value, quantity)
            
            # Place market order
            order = self.client.place_market_order(symbol, side, quantity)
            if not order:
                self.add_log(f"Failed to place order for {symbol}", "ERROR")
                return False
            
            # Get actual fill price
            actual_entry_price = float(order.get('avgPrice', entry_price))
            
            # Recalculate SL/TP with actual price
            sl_price, tp_price = self.calculate_sl_tp_prices(actual_entry_price, signal.value, quantity)
            
            order_ids = {'entry': order['orderId']}
            
            # Place stop loss
            sl_side = "SELL" if signal == Signal.LONG else "BUY"
            sl_order = self.client.place_stop_loss(symbol, sl_side, sl_price, quantity)
            if sl_order:
                order_ids['stop_loss'] = sl_order['orderId']
            
            # Place take profit
            tp_order = self.client.place_take_profit(symbol, sl_side, tp_price, quantity)
            if tp_order:
                order_ids['take_profit'] = tp_order['orderId']
            
            # Record position
            position = self.position_manager.open_position(
                symbol=symbol,
                side=position_side,
                entry_price=actual_entry_price,
                quantity=quantity,
                leverage=self.config.leverage,
                stop_loss_price=sl_price,
                take_profit_price=tp_price,
                order_ids=order_ids
            )
            
            if position:
                self.add_log(
                    f"🎯 Trade opened: {symbol} {signal.value} @ {actual_entry_price:.6f}, "
                    f"Qty: {quantity}, SL: {sl_price:.6f}, TP: {tp_price:.6f}"
                )
                return True
            
            return False
            
        except Exception as e:
            self.add_log(f"Error opening trade for {symbol}: {e}", "ERROR")
            return False
    
    def close_trade(self, symbol: str) -> bool:
        """Close an existing trade"""
        try:
            # Cancel all open orders
            self.client.cancel_all_orders(symbol)
            
            # Close position
            if self.client.close_position(symbol):
                current_price = self.client.get_symbol_price(symbol)
                self.position_manager.close_position(symbol, current_price)
                self.add_log(f"Trade closed: {symbol} @ {current_price}")
                return True
            return False
            
        except Exception as e:
            self.add_log(f"Error closing trade for {symbol}: {e}", "ERROR")
            return False
    
    def scan_markets(self):
        """Scan all markets for signals"""
        self.add_log("Starting market scan...")
        self.scan_results = []
        signals_found = []
        
        for symbol in self.symbols:
            try:
                # Skip if already have position
                if self.position_manager.has_position(symbol):
                    continue
                
                # Get candlestick data
                df = self.client.get_klines(
                    symbol,
                    interval=self.config.timeframe,
                    limit=self.config.lookback_candles
                )
                
                if df.empty:
                    continue
                
                # Analyze
                result = self.strategy.analyze(df, symbol)
                
                if result.crossover_detected:
                    signals_found.append({
                        'symbol': symbol,
                        'signal': result.signal.value,
                        'price': result.current_price,
                        'ema_fast': result.ema_fast,
                        'ema_slow': result.ema_slow
                    })
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        self.scan_results = signals_found
        self.last_scan_time = datetime.now()
        self.add_log(f"Scan complete: {len(signals_found)} signals found")
        
        return signals_found
    
    def check_positions(self):
        """Check and sync positions with exchange"""
        try:
            exchange_positions = self.client.get_open_positions()
            exchange_symbols = [p['symbol'] for p in exchange_positions]
            
            # Check for positions closed on exchange
            for symbol in self.position_manager.get_symbols_with_positions():
                if symbol not in exchange_symbols:
                    # Position was closed (SL/TP hit)
                    current_price = self.client.get_symbol_price(symbol)
                    self.position_manager.close_position(
                        symbol,
                        current_price,
                        PositionStatus.CLOSED
                    )
                    self.add_log(f"Position auto-closed: {symbol}")
                    
        except Exception as e:
            self.add_log(f"Error checking positions: {e}", "ERROR")
    
    def trading_loop(self):
        """Main trading loop"""
        self.add_log("Trading loop started")
        
        while self.running:
            try:
                # Check existing positions
                self.check_positions()
                
                # Only trade if enabled and can open positions
                if self.settings.trading_enabled and self.position_manager.can_open_position():
                    # Scan markets
                    signals = self.scan_markets()
                    
                    # Execute trades based on signals
                    for signal_data in signals:
                        if not self.position_manager.can_open_position():
                            break
                        
                        symbol = signal_data['symbol']
                        signal = Signal(signal_data['signal'])
                        
                        if signal in [Signal.LONG, Signal.SHORT]:
                            self.open_trade(symbol, signal)
                
                # Wait for next scan
                for _ in range(self.scan_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.add_log(f"Error in trading loop: {e}", "ERROR")
                time.sleep(5)
        
        self.add_log("Trading loop stopped")
    
    def start(self) -> bool:
        """Start the trader"""
        if self.running:
            self.add_log("Trader already running", "WARNING")
            return False
        
        if not self.initialize():
            return False
        
        self.running = True
        self.trading_thread = threading.Thread(target=self.trading_loop, daemon=True)
        self.trading_thread.start()
        
        self.add_log("🚀 Trader started successfully")
        return True
    
    def stop(self):
        """Stop the trader"""
        self.running = False
        self.add_log("Stopping trader...")
        
        if self.trading_thread:
            self.trading_thread.join(timeout=5)
        
        self.add_log("Trader stopped")
    
    def get_status(self) -> dict:
        """Get trader status"""
        return {
            'running': self.running,
            'trading_enabled': self.settings.trading_enabled,
            'mode': self.settings.get_mode_string(),
            'is_testnet': self.settings.is_testnet,
            'connected': self.client.connected,
            'symbols_count': len(self.symbols),
            'last_scan': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'signals_count': len(self.scan_results),
            'positions': self.position_manager.get_statistics(),
            'config': {
                'ema_fast': self.config.ema_fast,
                'ema_slow': self.config.ema_slow,
                'timeframe': self.config.timeframe,
                'position_size': self.config.position_size_usd,
                'leverage': self.config.leverage,
                'stop_loss': self.config.stop_loss_usd,
                'take_profit': self.config.take_profit_usd,
                'max_trades': self.config.max_open_trades
            }
        }
    
    def get_dashboard_data(self) -> dict:
        """Get data for dashboard"""
        balance = self.client.get_account_balance() if self.client.connected else {}
        open_positions = [p.to_dict() for p in self.position_manager.get_open_positions()]
        closed_positions = [p.to_dict() for p in self.position_manager.closed_positions[-50:]]
        
        return {
            'status': self.get_status(),
            'balance': balance,
            'open_positions': open_positions,
            'closed_positions': closed_positions,
            'recent_signals': self.scan_results[-20:],
            'logs': self.logs[-100:],
            'statistics': self.position_manager.get_statistics()
        }


# Global trader instance
trader = Trader()
