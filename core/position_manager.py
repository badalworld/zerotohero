"""
Zero to Hero - Position Manager
Author: Md Moniruzzaman
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class PositionStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    STOPPED = "STOPPED"
    TAKE_PROFIT = "TAKE_PROFIT"


@dataclass
class Position:
    """Trading position"""
    id: str
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    leverage: int
    stop_loss_price: float
    take_profit_price: float
    entry_time: datetime
    status: PositionStatus = PositionStatus.OPEN
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    order_ids: Dict = field(default_factory=dict)
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate current PnL"""
        if self.side == PositionSide.LONG:
            pnl = (current_price - self.entry_price) * self.quantity
        else:
            pnl = (self.entry_price - current_price) * self.quantity
        return round(pnl, 4)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'leverage': self.leverage,
            'stop_loss_price': self.stop_loss_price,
            'take_profit_price': self.take_profit_price,
            'entry_time': self.entry_time.isoformat(),
            'status': self.status.value,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'pnl': self.pnl
        }


class PositionManager:
    """Manage trading positions"""
    
    def __init__(self, max_positions: int = 3):
        self.max_positions = max_positions
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.position_counter = 0
        logger.info(f"Position Manager initialized (max: {max_positions})")
    
    def can_open_position(self) -> bool:
        """Check if can open new position"""
        open_count = len([p for p in self.positions.values() if p.status == PositionStatus.OPEN])
        return open_count < self.max_positions
    
    def has_position(self, symbol: str) -> bool:
        """Check if symbol has open position"""
        return symbol in self.positions and self.positions[symbol].status == PositionStatus.OPEN
    
    def open_position(
        self,
        symbol: str,
        side: PositionSide,
        entry_price: float,
        quantity: float,
        leverage: int,
        stop_loss_price: float,
        take_profit_price: float,
        order_ids: Dict = None
    ) -> Optional[Position]:
        """Open a new position"""
        
        if not self.can_open_position():
            logger.warning("Maximum positions reached")
            return None
        
        if self.has_position(symbol):
            logger.warning(f"Position already exists for {symbol}")
            return None
        
        self.position_counter += 1
        position_id = f"POS_{self.position_counter}_{int(datetime.now().timestamp())}"
        
        position = Position(
            id=position_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            leverage=leverage,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            entry_time=datetime.now(),
            order_ids=order_ids or {}
        )
        
        self.positions[symbol] = position
        logger.info(f"✅ Position opened: {symbol} {side.value} @ {entry_price}")
        return position
    
    def close_position(
        self,
        symbol: str,
        exit_price: float,
        status: PositionStatus = PositionStatus.CLOSED
    ) -> Optional[Position]:
        """Close a position"""
        
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return None
        
        position = self.positions[symbol]
        position.exit_price = exit_price
        position.exit_time = datetime.now()
        position.status = status
        position.pnl = position.calculate_pnl(exit_price)
        
        self.closed_positions.append(position)
        del self.positions[symbol]
        
        logger.info(f"❌ Position closed: {symbol} @ {exit_price}, PnL: ${position.pnl:.4f}")
        return position
    
    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return [p for p in self.positions.values() if p.status == PositionStatus.OPEN]
    
    def get_open_positions_count(self) -> int:
        """Get number of open positions"""
        return len(self.get_open_positions())
    
    def get_symbols_with_positions(self) -> List[str]:
        """Get list of symbols with open positions"""
        return list(self.positions.keys())
    
    def get_total_pnl(self) -> float:
        """Get total PnL from closed positions"""
        return sum(p.pnl for p in self.closed_positions)
    
    def get_statistics(self) -> dict:
        """Get trading statistics"""
        total_trades = len(self.closed_positions)
        winning_trades = [p for p in self.closed_positions if p.pnl > 0]
        losing_trades = [p for p in self.closed_positions if p.pnl < 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'total_pnl': round(self.get_total_pnl(), 4),
            'open_positions': self.get_open_positions_count(),
            'max_positions': self.max_positions
        }
    
    def update_position_orders(self, symbol: str, order_type: str, order_id: str):
        """Update position with order IDs"""
        if symbol in self.positions:
            self.positions[symbol].order_ids[order_type] = order_id
