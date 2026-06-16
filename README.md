# 📈 NIFTY MIDCAP 100 Swing Trading Signal Bot

An automated NIFTY Midcap 100 swing-trading signal engine that scans stocks, generates trade setups using technical indicators, tracks active trades, manages trailing stop-loss and trailing targets, and delivers alerts through Telegram.

## Strategy Overview

The bot continuously monitors the NIFTY Midcap 100 universe using:

- Market trend filtering via NIFTY 50
- 4H MACD bullish crossover confirmation
- 4H RSI strength filter
- 1H MACD bearish-cross filter
- Volume confirmation on crossover candles
- ATR-based stop-loss and target calculation
- Automated trade lifecycle management
- Telegram notifications

---

# Features

## Universe

### Stocks
- NIFTY Midcap 100 constituents

### Market Indicators
- NIFTY Index (`^NSEI`) for trend filtering
- India VIX (`^INDIAVIX`) for volatility reporting

---

# Multi-Timeframe Analysis

## 1-Hour Data

Used for:

- Trade monitoring
- ATR calculations
- Stop-loss sizing
- Target sizing
- Trailing stop management
- Bearish MACD filter

## 4-Hour Data

Used for:

- Signal generation
- RSI validation
- MACD crossover confirmation
- Volume confirmation

---

# Market Trend Filter

The overall market trend is determined from the NIFTY Index using:

- EMA 20
- EMA 50

| Condition | Market State |
|------------|-------------|
| EMA20 > EMA50 | Bullish |
| EMA20 < EMA50 | Bearish |
| Otherwise | Neutral |

### Entry Rule

No new trades are allowed when the market trend is bearish.

---

# Signal Generation Logic

A trade is generated only when all conditions are satisfied.

## 1. Market Not Bearish

```text
Trend = Bullish or Neutral
```

## 2. 4H RSI Filter

```text
RSI(14) >= 50
```

## 3. 1H MACD Filter

The latest completed 1-hour candle must not show a bearish MACD crossover.

```text
MACD >= Signal
```

## 4. 4H MACD Bullish Confirmation

The strategy confirms:

- Bullish MACD crossover
- Crossover remains valid
- Entry allowed within the last 3 completed 4H candles

## 5. MACD Overextension Filter

Rejects signals when MACD momentum is excessively stretched.

Threshold:

- Bullish market: 2.5 × MACD standard deviation
- Neutral market: 1.5 × MACD standard deviation

## 6. Volume Confirmation

The crossover candle volume must exceed the 20-period average volume.

---

# Risk Management

ATR-based dynamic risk control.

## Initial Stop Loss

```text
SL = Entry - (2.5 × ATR)
```

## Initial Target

```text
Target = Entry + (5 × ATR)
```

## Risk Reward

```text
1 : 2
```

---

# Trade Management

Open trades are monitored every scan cycle.

## Stop Loss Monitoring

Uses the LOW of the last completed 1H candle.

## Target Monitoring

Uses the HIGH of the last completed 1H candle.

## Trailing Stop Loss

```text
New SL = Current Price - (2.5 × ATR)
```

SL updates only when:

```text
New SL > Existing SL + (0.5 × ATR)
```

## Trailing Target

The bot maintains:

```text
High Since Entry
```

and calculates:

```text
Target = High Since Entry + (5 × Entry ATR)
```

Targets only move upward.

---

# Daily Trade Controls

Maximum new entries per UTC day:

```python
MAX_DAILY_ENTRIES = 5
```

Daily counts automatically reset.

---

# Telegram Notifications

The bot sends alerts for:

## Startup
- Bot started

## New Trade Signals
- Entry price
- Target
- Stop loss

## Trade Events
- Target hit
- Stop-loss hit
- Trade closed

## Dynamic Updates
- Trailing stop-loss updates
- Trailing target updates

## Scan Summaries
- Market trend
- India VIX
- Win rate
- New setups

---

# Data Sources

Market data:

```text
Yahoo Finance (yfinance)
```

Intervals:

| Purpose | Interval |
|----------|----------|
| Monitoring | 1 Hour |
| ATR | 1 Hour |
| Market Trend | 1 Hour |
| Signal Generation | 4 Hour |
| VIX | 1 Minute |

---

# Project Structure

```text
project/
│
├── niftymidcap100.py
│
├── active_trades_midcap.json
├── trade_history_midcap.json
├── signal_memory_midcap.json
├── daily_trade_count_midcap.json
│
└── logs/
```

---

# Dependencies

```bash
pip install yfinance pandas pandas-ta python-telegram-bot
```

---

# Configuration

## Telegram Token

Recommended:

```bash
export TELEGRAM_TOKEN="your_token"
```

The script currently contains a hardcoded fallback token. Moving secrets to environment variables is strongly recommended.

## Telegram Channels

```python
CHAT_IDS = [
    "-100xxxxxxxxxx"
]
```

---

# Running

```bash
python niftymidcap100.py
```

The bot:

1. Starts Telegram notifications
2. Downloads market data
3. Monitors active trades
4. Scans Midcap 100 stocks
5. Sends results
6. Sleeps 30 minutes
7. Repeats indefinitely

---

# Persistent Storage

## Active Trades

```text
active_trades_midcap.json
```

Stores:

- Open positions
- Entry price
- Current target
- Current stop loss
- Entry ATR
- High since entry

## Trade History

```text
trade_history_midcap.json
```

Stores:

- Closed trades
- Profit/Loss history

## Signal Memory

```text
signal_memory_midcap.json
```

Prevents duplicate signals.

## Daily Counter

```text
daily_trade_count_midcap.json
```

Tracks daily entry limits.

---

# Performance Metrics

## Win Rate

```text
Winning Trades / Total Closed Trades × 100
```

Reported in Telegram scan summaries.

---

# Logging

Python logging is enabled.

Tracks:

- Scan cycles
- Trade monitoring
- Errors
- Data issues

---

# Limitations

- Yahoo Finance data may be delayed.
- Data outages can affect signals.
- Indicator-based systems can generate false signals.
- Market gaps can exceed stop-loss levels.
- Backtesting is recommended before live deployment.
- Historical performance does not guarantee future results.

---

# Security Recommendations

Never commit:

- Telegram tokens
- Private chat IDs
- Trading records

Suggested `.gitignore`:

```gitignore
*.json
.env
```

---

# Disclaimer

## Educational Use Only

This software is intended for:

- Education
- Research
- Strategy development
- Market analysis

## Not Financial Advice

Signals generated by this bot are not investment recommendations or financial advice.

Trading and investing involve risk, including the loss of capital.

Use at your own risk.

---

# License

Add your preferred license before publishing:

- MIT
- Apache 2.0
- GPL
