"""
Zero to Hero - Supabase Client
Author: Md Moniruzzaman
"""

from datetime import datetime
from typing import List, Dict, Optional
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase database client for cloud storage"""
    
    def __init__(self):
        self.url = settings.supabase_url
        self.key = settings.supabase_key
        self.client = None
        self.connected = False
        
        if self.url and self.key:
            self._connect()
    
    def _connect(self):
        """Connect to Supabase"""
        try:
            from supabase import create_client
            self.client = create_client(self.url, self.key)
            self.connected = True
            logger.info("Connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to Supabase"""
        return self.connected and self.client is not None
    
    def save_trade(self, trade: dict) -> bool:
        """Save trade to Supabase"""
        if not self.is_connected():
            return False
        
        try:
            self.client.table('trades').upsert(trade).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to save trade to Supabase: {e}")
            return False
    
    def get_trades(self, status: str = None, limit: int = 100) -> List[dict]:
        """Get trades from Supabase"""
        if not self.is_connected():
            return []
        
        try:
            query = self.client.table('trades').select('*')
            if status:
                query = query.eq('status', status)
            query = query.order('entry_time', desc=True).limit(limit)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get trades from Supabase: {e}")
            return []
    
    def save_signal(self, signal: dict) -> bool:
        """Save signal to Supabase"""
        if not self.is_connected():
            return False
        
        try:
            self.client.table('signals').insert(signal).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to save signal to Supabase: {e}")
            return False
    
    def save_log(self, level: str, message: str) -> bool:
        """Save log to Supabase"""
        if not self.is_connected():
            return False
        
        try:
            self.client.table('logs').insert({
                'level': level,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }).execute()
            return True
        except Exception as e:
            return False
    
    def get_statistics(self) -> dict:
        """Get statistics from Supabase"""
        if not self.is_connected():
            return {}
        
        try:
            # Get all closed trades
            response = self.client.table('trades').select('*').eq('status', 'CLOSED').execute()
            trades = response.data
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0,
                'total_pnl': round(total_pnl, 4)
            }
        except Exception as e:
            logger.error(f"Failed to get statistics from Supabase: {e}")
            return {}


# Global instance
supabase_client = SupabaseClient()
