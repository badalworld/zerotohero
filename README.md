# 🚀 Zero to Hero - Binance Trading Bot

**Author:** Md Moniruzzaman  
**Strategy:** EMA 9/21 Crossover  
**Platform:** Binance Futures (USD-M)

## 📋 Overview

Zero to Hero is an automated trading bot that runs on your Android device using Termux. It trades on Binance Futures using an EMA crossover strategy.

### Strategy Details

- **LONG Signal:** EMA 9 crosses above EMA 21 (Bullish Crossover)
- **SHORT Signal:** EMA 9 crosses below EMA 21 (Bearish Crossover)

### Trading Parameters

| Parameter | Value |
|-----------|-------|
| Position Size | $4.00 |
| Leverage | 5x |
| Stop Loss | $1.00 |
| Take Profit | $0.20 |
| Max Open Trades | 3 |
| Timeframe | 5 minutes |

---

## 📱 Step-by-Step Setup Guide for Termux

### Step 1: Install Termux

1. Download Termux from [F-Droid](https://f-droid.org/packages/com.termux/) (recommended) or Play Store
2. Open Termux and grant storage permissions:
   ```bash
   termux-setup-storage
