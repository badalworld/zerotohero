"""
Zero to Hero - Local SQLite Database
Author: Md Moniruzzaman
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)


class LocalDatabase:
    """SQLite database for local storage"""
    
    def __init__(self, db_path: str = "database/trades.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        logger.info(f"Local database initialized: {db_path}")
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _init_db(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                stop_loss_price REAL,
                take_profit_price REAL,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                status TEXT NOT NULL,
                pnl REAL DEFAULT 0,
                order_ids TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                price REAL NOT NULL,
                ema_fast REAL,
                ema_slow REAL,
                timestamp TEXT NOT NULL,
                acted_on INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_trade(self, trade: dict) -> bool:
        """Save a trade to database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO trades 
                (id, symbol, side, entry_price, exit_price, quantity, leverage,
                 stop_loss_price, take_profit_price, entry_time, exit_time, 
                 status, pnl, order_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['id'],
                trade['symbol'],
                trade['side'],
                trade['entry_price'],
                trade.get('exit_price'),
                trade['quantity'],
                trade['leverage'],
                trade.get('stop_loss_price'),
                trade.get('take_profit_price'),
                trade['entry_time'],
                trade.get('exit_time'),
                trade['status'],
                trade.get('pnl', 0),
                json.dumps(trade.get('order_ids', {}))
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save trade: {e}")
            return False
    
    def get_trades(self, status: str = None, limit: int = 100) -> List[dict]:
        """Get trades from database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if status:
                cursor.execute(
                    'SELECT * FROM trades WHERE status = ? ORDER BY entry_time DESC LIMIT ?',
                    (status, limit)
                )
            else:
                cursor.execute(
                    'SELECT * FROM trades ORDER BY entry_time DESC LIMIT ?',
                    (limit,)
                )
            
            columns = [description[0] for description in cursor.description]
            trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get trades: {e}")
            return []
    
    def save_signal(self, signal: dict) -> bool:
        """Save a signal to database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signals 
                (symbol, signal_type, price, ema_fast, ema_slow, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                signal['symbol'],
                signal['signal_type'],
                signal['price'],
                signal.get('ema_fast'),
                signal.get('ema_slow'),
                signal['timestamp']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
            return False
    
    def save_log(self, level: str, message: str) -> bool:
        """Save a log entry"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO logs (level, message, timestamp)
                VALUES (?, ?, ?)
            ''', (level, message, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            return False
    
    def get_logs(self, limit: int = 100) -> List[dict]:
        """Get recent logs"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM logs ORDER BY id DESC LIMIT ?',
                (limit,)
            )
            
            columns = [description[0] for description in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []
    
    def save_setting(self, key: str, value: str) -> bool:
        """Save a setting"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save setting: {e}")
            return False
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            conn.close()
            return row[0] if row else None
            
        except Exception as e:
            logger.error(f"Failed to get setting: {e}")
            return None
    
    def get_statistics(self) -> dict:
        """Get trading statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total trades
            cursor.execute('SELECT COUNT(*) FROM trades WHERE status = "CLOSED"')
            total_trades = cursor.fetchone()[0]
            
            # Winning trades
            cursor.execute('SELECT COUNT(*) FROM trades WHERE status = "CLOSED" AND pnl > 0')
            winning_trades = cursor.fetchone()[0]
            
            # Total PnL
            cursor.execute('SELECT SUM(pnl) FROM trades WHERE status = "CLOSED"')
            total_pnl = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0,
                'total_pnl': round(total_pnl, 4)
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# Global instance
local_db = LocalDatabase()
