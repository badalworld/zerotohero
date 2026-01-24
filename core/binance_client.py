"""
Zero to Hero - Binance Client
Author: Md Moniruzzaman
"""

import time
import hmac
import hashlib
from urllib.parse import urlencode
from typing import Optional, Dict, List, Any
import requests
import pandas as pd
from binance.client import Client
from binance.enums import *
from config.settings import settings, TradingConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BinanceClient:
    """Binance Futures API Client"""
    
    def __init__(self):
        self.settings = settings
        self.trading_config = settings.trading_config
        self._client: Optional[Client] = None
        self._session = requests.Session()
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to Binance API"""
        try:
            valid, msg = self.settings.validate()
            if not valid:
                logger.error(f"Validation failed: {msg}")
                return False
            
            # Initialize Binance client
            self._client = Client(
                api_key=self.settings.api_key,
                api_secret=self.settings.api_secret,
                testnet=self.settings.is_testnet
            )
            
            # Test connection
            self._client.futures_ping()
            self.connected = True
            logger.info(f"Connected to Binance {self.settings.get_mode_string()}")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            return False
    
    def _sign_request(self, params: dict) -> dict:
        """Sign request with API secret"""
        params['timestamp'] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.settings.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        params['signature'] = signature
        return params
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False) -> dict:
        """Make HTTP request to Binance API"""
        url = f"{self.settings.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.settings.api_key}
        
        if params is None:
            params = {}
        
        if signed:
            params = self._sign_request(params)
        
        try:
            if method == "GET":
                response = self._session.get(url, params=params, headers=headers)
            elif method == "POST":
                response = self._session.post(url, params=params, headers=headers)
            elif method == "DELETE":
                response = self._session.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_all_usdt_futures_symbols(self) -> List[str]:
        """Get all USDT-M futures trading pairs"""
        try:
            exchange_info = self._client.futures_exchange_info()
            symbols = [
                s['symbol'] for s in exchange_info['symbols']
                if s['quoteAsset'] == 'USDT' 
                and s['status'] == 'TRADING'
                and s['contractType'] == 'PERPETUAL'
            ]
            logger.info(f"Found {len(symbols)} USDT-M futures pairs")
            return symbols
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []
    
    def get_klines(self, symbol: str, interval: str = "5m", limit: int = 100) -> pd.DataFrame:
        """Get candlestick data"""
        try:
            klines = self._client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_symbol_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            ticker = self._client.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """Get symbol trading rules"""
        try:
            exchange_info = self._client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    return s
            return None
        except Exception as e:
            logger.error(f"Failed to get symbol info: {e}")
            return None
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol"""
        try:
            self._client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            logger.info(f"Set leverage {leverage}x for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to set leverage for {symbol}: {e}")
            return False
    
    def set_margin_type(self, symbol: str, margin_type: str = "ISOLATED") -> bool:
        """Set margin type for a symbol"""
        try:
            self._client.futures_change_margin_type(
                symbol=symbol,
                marginType=margin_type
            )
            logger.info(f"Set margin type {margin_type} for {symbol}")
            return True
        except Exception as e:
            # Ignore if already set
            if "No need to change margin type" in str(e):
                return True
            logger.error(f"Failed to set margin type: {e}")
            return False
    
    def get_account_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            account = self._client.futures_account()
            balances = {}
            for asset in account['assets']:
                if float(asset['walletBalance']) > 0:
                    balances[asset['asset']] = {
                        'wallet_balance': float(asset['walletBalance']),
                        'available_balance': float(asset['availableBalance']),
                        'unrealized_pnl': float(asset['unrealizedProfit'])
                    }
            return balances
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return {}
    
    def get_open_positions(self) -> List[dict]:
        """Get all open positions"""
        try:
            positions = self._client.futures_position_information()
            open_positions = [
                {
                    'symbol': p['symbol'],
                    'side': 'LONG' if float(p['positionAmt']) > 0 else 'SHORT',
                    'size': abs(float(p['positionAmt'])),
                    'entry_price': float(p['entryPrice']),
                    'mark_price': float(p['markPrice']),
                    'unrealized_pnl': float(p['unRealizedProfit']),
                    'leverage': int(p['leverage']),
                    'liquidation_price': float(p['liquidationPrice']) if p['liquidationPrice'] else 0
                }
                for p in positions
                if float(p['positionAmt']) != 0
            ]
            return open_positions
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_open_orders(self, symbol: str = None) -> List[dict]:
        """Get open orders"""
        try:
            if symbol:
                orders = self._client.futures_get_open_orders(symbol=symbol)
            else:
                orders = self._client.futures_get_open_orders()
            return orders
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool = False
    ) -> Optional[dict]:
        """Place a market order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity
            }
            
            if reduce_only:
                params['reduceOnly'] = 'true'
            
            order = self._client.futures_create_order(**params)
            logger.info(f"Market order placed: {symbol} {side} {quantity}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            return None
    
    def place_stop_loss(
        self,
        symbol: str,
        side: str,
        stop_price: float,
        quantity: float
    ) -> Optional[dict]:
        """Place a stop loss order"""
        try:
            order = self._client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP_MARKET',
                stopPrice=round(stop_price, self._get_price_precision(symbol)),
                quantity=quantity,
                reduceOnly='true'
            )
            logger.info(f"Stop loss placed: {symbol} {side} @ {stop_price}")
            return order
        except Exception as e:
            logger.error(f"Failed to place stop loss: {e}")
            return None
    
    def place_take_profit(
        self,
        symbol: str,
        side: str,
        stop_price: float,
        quantity: float
    ) -> Optional[dict]:
        """Place a take profit order"""
        try:
            order = self._client.futures_create_order(
                symbol=symbol,
                side=side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=round(stop_price, self._get_price_precision(symbol)),
                quantity=quantity,
                reduceOnly='true'
            )
            logger.info(f"Take profit placed: {symbol} {side} @ {stop_price}")
            return order
        except Exception as e:
            logger.error(f"Failed to place take profit: {e}")
            return None
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol"""
        try:
            self._client.futures_cancel_all_open_orders(symbol=symbol)
            logger.info(f"Cancelled all orders for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            return False
    
    def close_position(self, symbol: str) -> bool:
        """Close an open position"""
        try:
            positions = self._client.futures_position_information(symbol=symbol)
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    quantity = abs(float(pos['positionAmt']))
                    side = 'SELL' if float(pos['positionAmt']) > 0 else 'BUY'
                    
                    self._client.futures_create_order(
                        symbol=symbol,
                        side=side,
                        type='MARKET',
                        quantity=quantity,
                        reduceOnly='true'
                    )
                    logger.info(f"Closed position for {symbol}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return False
    
    def _get_price_precision(self, symbol: str) -> int:
        """Get price precision for a symbol"""
        try:
            info = self.get_symbol_info(symbol)
            if info:
                for f in info['filters']:
                    if f['filterType'] == 'PRICE_FILTER':
                        tick_size = float(f['tickSize'])
                        precision = len(str(tick_size).rstrip('0').split('.')[-1])
                        return precision
            return 2
        except:
            return 2
    
    def _get_quantity_precision(self, symbol: str) -> int:
        """Get quantity precision for a symbol"""
        try:
            info = self.get_symbol_info(symbol)
            if info:
                for f in info['filters']:
                    if f['filterType'] == 'LOT_SIZE':
                        step_size = float(f['stepSize'])
                        precision = len(str(step_size).rstrip('0').split('.')[-1])
                        return precision
            return 3
        except:
            return 3
    
    def calculate_quantity(self, symbol: str, usdt_amount: float, leverage: int) -> float:
        """Calculate quantity based on USDT amount and leverage"""
        try:
            price = self.get_symbol_price(symbol)
            if price == 0:
                return 0
            
            # Calculate quantity with leverage
            quantity = (usdt_amount * leverage) / price
            
            # Round to proper precision
            precision = self._get_quantity_precision(symbol)
            quantity = round(quantity, precision)
            
            # Check minimum quantity
            info = self.get_symbol_info(symbol)
            if info:
                for f in info['filters']:
                    if f['filterType'] == 'LOT_SIZE':
                        min_qty = float(f['minQty'])
                        if quantity < min_qty:
                            logger.warning(f"{symbol}: Quantity {quantity} below minimum {min_qty}")
                            return 0
            
            return quantity
            
        except Exception as e:
            logger.error(f"Failed to calculate quantity: {e}")
            return 0


# Singleton instance
binance_client = BinanceClient()
