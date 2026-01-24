"""
Zero to Hero - Flask Web Application
Author: Md Moniruzzaman
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import os
import logging
from datetime import datetime

from config.settings import settings
from core.trader import trader
from database.local_db import local_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")


# ============== Web Routes ==============

@app.route('/')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')


@app.route('/trades')
def trades():
    """Trades history page"""
    return render_template('trades.html')


@app.route('/settings')
def settings_page():
    """Settings page"""
    return render_template('settings.html')


# ============== API Routes ==============

@app.route('/api/dashboard')
def api_dashboard():
    """Get dashboard data"""
    try:
        data = trader.get_dashboard_data()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Dashboard API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status')
def api_status():
    """Get bot status"""
    try:
        status = trader.get_status()
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/start', methods=['POST'])
def api_start():
    """Start the trading bot"""
    try:
        if trader.start():
            return jsonify({'success': True, 'message': 'Bot started successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to start bot'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop the trading bot"""
    try:
        trader.stop()
        return jsonify({'success': True, 'message': 'Bot stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/toggle-trading', methods=['POST'])
def api_toggle_trading():
    """Toggle trading on/off"""
    try:
        data = request.json
        settings.trading_enabled = data.get('enabled', False)
        status = "enabled" if settings.trading_enabled else "disabled"
        return jsonify({'success': True, 'message': f'Trading {status}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/switch-mode', methods=['POST'])
def api_switch_mode():
    """Switch between testnet and mainnet"""
    try:
        settings.is_testnet = not settings.is_testnet
        mode = "Testnet" if settings.is_testnet else "Mainnet"
        
        # Reconnect with new settings
        if trader.running:
            trader.stop()
        
        return jsonify({
            'success': True, 
            'message': f'Switched to {mode}. Please restart the bot.',
            'is_testnet': settings.is_testnet
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """Trigger manual market scan"""
    try:
        if not trader.client.connected:
            if not trader.initialize():
                return jsonify({'success': False, 'message': 'Failed to connect'}), 400
        
        signals = trader.scan_markets()
        return jsonify({
            'success': True, 
            'message': f'Scan complete. Found {len(signals)} signals.',
            'signals': signals
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/close-position', methods=['POST'])
def api_close_position():
    """Close a specific position"""
    try:
        data = request.json
        symbol = data.get('symbol')
        if not symbol:
            return jsonify({'success': False, 'message': 'Symbol required'}), 400
        
        if trader.close_trade(symbol):
            return jsonify({'success': True, 'message': f'Position closed for {symbol}'})
        else:
            return jsonify({'success': False, 'message': 'Failed to close position'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/close-all', methods=['POST'])
def api_close_all():
    """Close all open positions"""
    try:
        positions = trader.position_manager.get_open_positions()
        closed = 0
        for pos in positions:
            if trader.close_trade(pos.symbol):
                closed += 1
        
        return jsonify({
            'success': True, 
            'message': f'Closed {closed} positions'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/api', methods=['POST'])
def api_settings_api():
    """Update API settings"""
    try:
        data = request.json
        
        if data.get('testnet_api_key'):
            settings.testnet_api_key = data['testnet_api_key']
            os.environ['BINANCE_TESTNET_API_KEY'] = data['testnet_api_key']
        
        if data.get('testnet_api_secret'):
            settings.testnet_api_secret = data['testnet_api_secret']
            os.environ['BINANCE_TESTNET_API_SECRET'] = data['testnet_api_secret']
        
        if data.get('mainnet_api_key'):
            settings.mainnet_api_key = data['mainnet_api_key']
            os.environ['BINANCE_MAINNET_API_KEY'] = data['mainnet_api_key']
        
        if data.get('mainnet_api_secret'):
            settings.mainnet_api_secret = data['mainnet_api_secret']
            os.environ['BINANCE_MAINNET_API_SECRET'] = data['mainnet_api_secret']
        
        # Save to local db
        local_db.save_setting('api_configured', 'true')
        
        return jsonify({'success': True, 'message': 'API settings saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/trading', methods=['POST'])
def api_settings_trading():
    """Update trading settings"""
    try:
        data = request.json
        config = settings.trading_config
        
        if 'ema_fast' in data:
            config.ema_fast = data['ema_fast']
        if 'ema_slow' in data:
            config.ema_slow = data['ema_slow']
        if 'position_size' in data:
            config.position_size_usd = data['position_size']
        if 'leverage' in data:
            config.leverage = data['leverage']
        if 'stop_loss' in data:
            config.stop_loss_usd = data['stop_loss']
        if 'take_profit' in data:
            config.take_profit_usd = data['take_profit']
        if 'max_trades' in data:
            config.max_open_trades = data['max_trades']
        if 'timeframe' in data:
            config.timeframe = data['timeframe']
        
        # Update strategy
        trader.strategy.fast_period = config.ema_fast
        trader.strategy.slow_period = config.ema_slow
        trader.position_manager.max_positions = config.max_open_trades
        
        return jsonify({'success': True, 'message': 'Trading settings saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/supabase', methods=['POST'])
def api_settings_supabase():
    """Update Supabase settings"""
    try:
        data = request.json
        
        if data.get('supabase_url'):
            settings.supabase_url = data['supabase_url']
            os.environ['SUPABASE_URL'] = data['supabase_url']
        
        if data.get('supabase_key'):
            settings.supabase_key = data['supabase_key']
            os.environ['SUPABASE_KEY'] = data['supabase_key']
        
        settings.use_supabase = data.get('use_supabase', False)
        
        return jsonify({'success': True, 'message': 'Supabase settings saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============== Error Handlers ==============

@app.errorhandler(404)
def not_found(e):
    return render_template('dashboard.html'), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ============== Main Entry ==============

def create_app():
    """Create and configure the Flask app"""
    return app


if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════╗
    ║         ZERO TO HERO Trading Bot          ║
    ║         Author: Md Moniruzzaman           ║
    ║         EMA 9/21 Crossover Strategy       ║
    ╚═══════════════════════════════════════════╝
    """)
    
    socketio.run(
        app,
        host=settings.host,
        port=settings.port,
        debug=settings.debug
)
