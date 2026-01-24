/**
 * Zero to Hero - Dashboard JavaScript
 * Author: Md Moniruzzaman
 */

// API Base URL
const API_BASE = '';

// Dashboard state
let dashboardData = {};
let isTestnet = true;

// Refresh dashboard data
function refreshDashboard() {
    fetch(`${API_BASE}/api/dashboard`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                dashboardData = data.data;
                updateDashboard(data.data);
            }
        })
        .catch(error => console.error('Error fetching dashboard:', error));
}

// Update dashboard UI
function updateDashboard(data) {
    // Update status
    const status = data.status;
    isTestnet = status.is_testnet;
    
    // Mode badge
    const modeBadge = document.getElementById('mode-badge');
    if (modeBadge) {
        modeBadge.className = `badge ${status.is_testnet ? 'badge-testnet' : 'badge-mainnet'}`;
        modeBadge.textContent = status.mode;
    }
    
    // Switch mode text
    const switchModeText = document.getElementById('switch-mode-text');
    if (switchModeText) {
        switchModeText.textContent = status.is_testnet ? 'Mainnet' : 'Testnet';
    }
    
    // Status indicator
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.getElementById('status-text');
    if (statusIndicator && statusText) {
        if (status.running) {
            statusIndicator.className = 'status-indicator status-active';
            statusText.textContent = 'Running';
        } else if (status.connected) {
            statusIndicator.className = 'status-indicator status-inactive';
            statusText.textContent = 'Connected';
        } else {
            statusIndicator.className = 'status-indicator status-inactive';
            statusText.textContent = 'Disconnected';
        }
    }
    
    // Start/Stop buttons
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    if (startBtn && stopBtn) {
        startBtn.disabled = status.running;
        stopBtn.disabled = !status.running;
    }
    
    // Trading toggle
    const tradingToggle = document.getElementById('trading-toggle');
    const tradingStatus = document.getElementById('trading-status');
    if (tradingToggle && tradingStatus) {
        tradingToggle.checked = status.trading_enabled;
        tradingStatus.textContent = status.trading_enabled ? 'Trading Enabled' : 'Trading Disabled';
    }
    
    // Statistics
    const stats = data.statistics;
    document.getElementById('total-pnl').textContent = `$${stats.total_pnl.toFixed(4)}`;
    document.getElementById('total-pnl').className = `stat-value ${stats.total_pnl >= 0 ? 'text-success' : 'text-danger'}`;
    document.getElementById('open-positions').textContent = stats.open_positions;
    document.getElementById('total-trades').textContent = stats.total_trades;
    document.getElementById('win-rate').textContent = `${stats.win_rate}%`;
    document.getElementById('positions-count').textContent = stats.open_positions;
    document.getElementById('signals-count').textContent = data.recent_signals.length;
    
    // Strategy config
    const config = status.config;
    document.getElementById('cfg-ema-fast').textContent = config.ema_fast;
    document.getElementById('cfg-ema-slow').textContent = config.ema_slow;
    document.getElementById('cfg-position-size').textContent = `$${config.position_size.toFixed(2)}`;
    document.getElementById('cfg-leverage').textContent = `${config.leverage}x`;
    document.getElementById('cfg-stop-loss').textContent = `$${config.stop_loss.toFixed(2)}`;
    document.getElementById('cfg-take-profit').textContent = `$${config.take_profit.toFixed(2)}`;
    
    // Balance
    updateBalance(data.balance);
    
    // Positions table
    updatePositionsTable(data.open_positions);
    
    // Signals table
    updateSignalsTable(data.recent_signals);
    
    // Logs
    updateLogs(data.logs);
}

// Update balance display
function updateBalance(balance) {
    const balanceInfo = document.getElementById('balance-info');
    if (!balanceInfo) return;
    
    if (Object.keys(balance).length === 0) {
        balanceInfo.innerHTML = '<div class="text-secondary">No balance data</div>';
        return;
    }
    
    let html = '';
    for (const [asset, info] of Object.entries(balance)) {
        html += `
            <div class="d-flex justify-content-between mb-2">
                <span>${asset}</span>
                <span class="fw-bold">$${info.wallet_balance.toFixed(2)}</span>
            </div>
            <div class="d-flex justify-content-between mb-2 small">
                <span class="text-secondary">Available</span>
                <span>$${info.available_balance.toFixed(2)}</span>
            </div>
            <div class="d-flex justify-content-between small">
                <span class="text-secondary">Unrealized PnL</span>
                <span class="${info.unrealized_pnl >= 0 ? 'profit' : 'loss'}">
                    $${info.unrealized_pnl.toFixed(4)}
                </span>
            </div>
        `;
    }
    balanceInfo.innerHTML = html;
}

// Update positions table
function updatePositionsTable(positions) {
    const table = document.getElementById('positions-table');
    if (!table) return;
    
    if (positions.length === 0) {
        table.innerHTML = '<tr><td colspan="6" class="text-center text-secondary">No open positions</td></tr>';
        return;
    }
    
    let html = '';
    positions.forEach(p => {
        const pnlClass = p.pnl >= 0 ? 'profit' : 'loss';
        html += `
            <tr>
                <td>${p.symbol}</td>
                <td><span class="badge badge-${p.side.toLowerCase()}">${p.side}</span></td>
                <td>${parseFloat(p.entry_price).toFixed(4)}</td>
                <td>${p.quantity}</td>
                <td class="${pnlClass}">$${p.pnl.toFixed(4)}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="closePosition('${p.symbol}')">
                        Close
                    </button>
                </td>
            </tr>
        `;
    });
    table.innerHTML = html;
}

// Update signals table
function updateSignalsTable(signals) {
    const table = document.getElementById('signals-table');
    if (!table) return;
    
    if (signals.length === 0) {
        table.innerHTML = '<tr><td colspan="5" class="text-center text-secondary">No signals yet</td></tr>';
        return;
    }
    
    let html = '';
    signals.slice(-10).reverse().forEach(s => {
        html += `
            <tr>
                <td>${s.symbol}</td>
                <td><span class="badge badge-${s.signal.toLowerCase()}">${s.signal}</span></td>
                <td>${parseFloat(s.price).toFixed(4)}</td>
                <td>${parseFloat(s.ema_fast).toFixed(4)}</td>
                <td>${parseFloat(s.ema_slow).toFixed(4)}</td>
            </tr>
        `;
    });
    table.innerHTML = html;
}

// Update logs
function updateLogs(logs) {
    const container = document.getElementById('logs-container');
    if (!container) return;
    
    if (logs.length === 0) {
        container.innerHTML = '<div class="text-secondary">No logs yet</div>';
        return;
    }
    
    let html = '';
    logs.slice(-50).reverse().forEach(log => {
        const levelClass = log.level.toLowerCase();
        const time = new Date(log.timestamp).toLocaleTimeString();
        html += `
            <div class="log-entry log-${levelClass}">
                <span class="text-secondary">[${time}]</span>
                <span class="text-${levelClass === 'error' ? 'danger' : levelClass === 'warning' ? 'warning' : 'info'}">
                    [${log.level}]
                </span>
                ${log.message}
            </div>
        `;
    });
    container.innerHTML = html;
}

// Start bot
function startBot() {
    fetch(`${API_BASE}/api/start`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            alert(data.message);
            refreshDashboard();
        });
}

// Stop bot
function stopBot() {
    fetch(`${API_BASE}/api/stop`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            alert(data.message);
            refreshDashboard();
        });
}

// Toggle trading
function toggleTrading() {
    const enabled = document.getElementById('trading-toggle').checked;
    fetch(`${API_BASE}/api/toggle-trading`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: enabled })
    })
        .then(r => r.json())
        .then(data => {
            refreshDashboard();
        });
}

// Switch mode
function switchMode() {
    fetch(`${API_BASE}/api/switch-mode`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            alert(data.message);
            refreshDashboard();
        });
}

// Scan now
function scanNow() {
    fetch(`${API_BASE}/api/scan`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            alert(data.message);
            refreshDashboard();
        });
}

// Close all positions
function closeAllPositions() {
    if (!confirm('Are you sure you want to close all positions?')) return;
    
    fetch(`${API_BASE}/api/close-all`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            alert(data.message);
            refreshDashboard();
        });
}

// Close single position
function closePosition(symbol) {
    if (!confirm(`Close position for ${symbol}?`)) return;
    
    fetch(`${API_BASE}/api/close-position`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: symbol })
    })
        .then(r => r.json())
        .then(data => {
            alert(data.message);
            refreshDashboard();
        });
}

// Clear logs
function clearLogs() {
    document.getElementById('logs-container').innerHTML = '<div class="text-secondary">Logs cleared</div>';
}

// Initial load
document.addEventListener('DOMContentLoaded', refreshDashboard);
