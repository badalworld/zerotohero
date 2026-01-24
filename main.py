"""
Zero to Hero - Main Entry Point
Author: Md Moniruzzaman
"""

import os
import sys
from app import app, socketio
from config.settings import settings

def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║              🚀 ZERO TO HERO Trading Bot 🚀               ║
    ║                                                           ║
    ║           Author: Md Moniruzzaman                         ║
    ║           Strategy: EMA 9/21 Crossover                    ║
    ║           Platform: Binance Futures (USD-M)               ║
    ║                                                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Settings:                                                ║
    ║  • Position Size: $4.00                                   ║
    ║  • Leverage: 5x                                           ║
    ║  • Stop Loss: $1.00                                       ║
    ║  • Take Profit: $0.20                                     ║
    ║  • Max Open Trades: 3                                     ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Access Dashboard: http://localhost:5000                  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Run the server
    socketio.run(
        app,
        host=settings.host,
        port=settings.port,
        debug=settings.debug
    )


if __name__ == '__main__':
    main()
