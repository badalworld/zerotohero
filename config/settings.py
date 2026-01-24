"""
Zero to Hero - Configuration Settings
Author: Md Moniruzzaman
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TradingConfig:
    """Trading strategy configuration"""
    # EMA Settings
    ema_fast: int = 9
    ema_slow: int = 21
    timeframe: str = "5m"
    
    # Position Settings
    position_size_usd: float = 4.0
    leverage: int = 5
    stop_loss_usd: float = 1.0
    take_profit_usd: float = 0.20
    
    # Risk Management
    max_open_trades: int = 3
    
    # Analysis Settings
    lookback_candles: int = 100


@dataclass
class Settings:
    """Application settings"""
    # App Info
    app_name: str = "Zero to Hero"
    author: str = "Md Moniruzzaman"
    version: str = "1.0.0"
    
    # Trading Mode
    is_testnet: bool = True
    trading_enabled: bool = False
    
    # Binance API - Mainnet
    mainnet_api_key: str = field(default_factory=lambda: os.getenv("BINANCE_MAINNET_API_KEY", ""))
    mainnet_api_secret: str = field(default_factory=lambda: os.getenv("BINANCE_MAINNET_API_SECRET", ""))
    
    # Binance API - Testnet
    testnet_api_key: str = field(default_factory=lambda: os.getenv("BINANCE_TESTNET_API_KEY", ""))
    testnet_api_secret: str = field(default_factory=lambda: os.getenv("BINANCE_TESTNET_API_SECRET", ""))
    
    # Supabase (Optional)
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = True
    
    # Database
    use_supabase: bool = False
    local_db_path: str = "database/trades.db"
    
    # Trading Config
    trading_config: TradingConfig = field(default_factory=TradingConfig)
    
    # API Endpoints
    mainnet_base_url: str = "https://fapi.binance.com"
    testnet_base_url: str = "https://testnet.binancefuture.com"
    
    @property
    def api_key(self) -> str:
        return self.testnet_api_key if self.is_testnet else self.mainnet_api_key
    
    @property
    def api_secret(self) -> str:
        return self.testnet_api_secret if self.is_testnet else self.mainnet_api_secret
    
    @property
    def base_url(self) -> str:
        return self.testnet_base_url if self.is_testnet else self.mainnet_base_url
    
    def get_mode_string(self) -> str:
        return "TESTNET (Demo)" if self.is_testnet else "MAINNET (Real)"
    
    def validate(self) -> tuple[bool, str]:
        """Validate settings before trading"""
        if not self.api_key or not self.api_secret:
            mode = "testnet" if self.is_testnet else "mainnet"
            return False, f"Missing {mode} API credentials"
        return True, "Settings validated successfully"


# Global settings instance
settings = Settings()
