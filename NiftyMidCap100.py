import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timezone
import asyncio
import json
import logging
from telegram import Bot

# ================= CONFIG =================
TOKEN = os.getenv("") or ""

CHAT_IDS = ["", ""]
CHAT_IDS = [c for c in CHAT_IDS if c.strip()]

TRADES_FILE = "active_trades_midcap.json"
HISTORY_FILE = "trade_history_midcap.json"
SIGNAL_FILE = "signal_memory_midcap.json"
DAILY_COUNT_FILE = "daily_trade_count_midcap.json"

# ================= UNIVERSE =================
NIFTY_MIDCAP_100 = [
    "ABCAPITAL.NS","ABFRL.NS","ACC.NS","ALKEM.NS","APLAPOLLO.NS",
    "APLLTD.NS","ASHOKLEY.NS","ASTRAL.NS","ATGL.NS","AUBANK.NS",
    "AUROPHARMA.NS","BALKRISIND.NS","BALRAMCHIN.NS","BANDHANBNK.NS","BANKBARODA.NS",
    "BERGEPAINT.NS","BHARATFORG.NS","BHEL.NS","BIOCON.NS","BSE.NS",
    "CANBK.NS","CHOLAFIN.NS","COFORGE.NS","CROMPTON.NS","CUMMINSIND.NS",
    "DABUR.NS","DALBHARAT.NS","DEEPAKNTR.NS","DELHIVERY.NS","DIXON.NS",
    "DLF.NS","ESCORTS.NS","EXIDEIND.NS","FEDERALBNK.NS","FORTIS.NS",
    "GAIL.NS","GLAND.NS","GLENMARK.NS","GMRAIRPORT.NS","GODREJCP.NS",
    "GODREJPROP.NS","GROWW.NS","HAL.NS","HAVELLS.NS","HEROMOTOCO.NS",
    "HINDPETRO.NS","ICICIAMC.NS","ICICIGI.NS","IDEA.NS","IDFCFIRSTB.NS",
    "IGL.NS","INDIANB.NS","INDHOTEL.NS","INDIAMART.NS","INDUSINDBK.NS",
    "INDUSTOWER.NS","IRCTC.NS","JINDALSTEL.NS","JSL.NS","JSWENERGY.NS",
    "KEI.NS","LALPATHLAB.NS","LAURUSLABS.NS","LENSKART.NS","LGEINDIA.NS",
    "LICHSGFIN.NS","LUPIN.NS","MANKIND.NS","MARICO.NS","MCX.NS",
    "METROPOLIS.NS","MFSL.NS","MPHASIS.NS","MUTHOOTFIN.NS","NAM-INDIA.NS",
    "NAUKRI.NS","NHPC.NS","NMDC.NS","OBEROIRLTY.NS","OFSS.NS",
    "POLICYBZR.NS","PERSISTENT.NS","PETRONET.NS","PIDILITIND.NS","PIRAMALFIN.NS",
    "POLYCAB.NS","POWERINDIA.NS","RAMCOCEM.NS","SAIL.NS","SRF.NS",
    "SUNTV.NS","SUZLON.NS","SYNGENE.NS","TATACHEM.NS","TATACOMM.NS",
    "TATAPOWER.NS","TORNTPHARM.NS","TORNTPOWER.NS","TRENT.NS","TVSMOTOR.NS",
    "UBL.NS","UNIONBANK.NS","VEDL.NS","VOLTAS.NS","WAAREEENER.NS"
]

INDEX = "^NSEI"

MAX_DAILY_ENTRIES = 5

logging.basicConfig(level=logging.INFO)

# ================= SAFE ACCESS =================
def get_df(data, symbol):
    try:
        if symbol in data:
            return data[symbol]
        if symbol + ".NS" in data:
            return data[symbol + ".NS"]
        return None
    except:
        return None

# ================= JSON =================
def load_json(file, default):
    if os.path.exists(file):
        try:
            return json.load(open(file))
        except:
            return default
    return default

def save_json(data, file):
    try:
        tmp_file = file + ".tmp"
        with open(tmp_file, "w") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_file, file)
    except Exception as e:
        logging.error(f"MIDCAP100 SAVE ERROR ({file}): {e}")

# ================= DAILY TRADE COUNT =================
def get_daily_entry_count():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily = load_json(DAILY_COUNT_FILE, {})
    if daily.get("date") != today:
        daily = {"date": today, "count": 0}
        save_json(daily, DAILY_COUNT_FILE)
    return daily

def increment_daily_entry_count():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily = load_json(DAILY_COUNT_FILE, {})
    if daily.get("date") != today:
        daily = {"date": today, "count": 0}
    daily["count"] += 1
    save_json(daily, DAILY_COUNT_FILE)

# ================= TELEGRAM =================
async def send_msg(msg):
    bot = Bot(token=TOKEN)
    async with bot:
        for chat_id in CHAT_IDS:
            try:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")
            except:
                pass

# ================= TELEGRAM ALERT HELPERS =================
async def send_target_hit_alert(sym, price, target, entry, pnl):
    msg = (
        f"🎯 <b>TARGET HIT — {sym}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"✅ Target Price: ₹{round(target, 2)}\n"
        f"💰 Exit Price: ₹{round(price, 2)}\n"
        f"📥 Entry Price: ₹{round(entry, 2)}\n"
        f"📈 PnL: <b>{pnl}%</b>\n"
        f"🕐 Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    await send_msg(msg)

async def send_stoploss_hit_alert(sym, price, sl, entry, pnl):
    msg = (
        f"⛔ <b>STOPLOSS HIT — {sym}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🛑 SL Price: ₹{round(sl, 2)}\n"
        f"💸 Exit Price: ₹{round(price, 2)}\n"
        f"📥 Entry Price: ₹{round(entry, 2)}\n"
        f"📉 PnL: <b>{pnl}%</b>\n"
        f"🕐 Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    await send_msg(msg)

async def send_trailing_sl_alert(sym, old_sl, new_sl, price):
    msg = (
        f"🔁 <b>TRAILING SL UPDATED — {sym}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📍 CMP: ₹{round(price, 2)}\n"
        f"⛔ Old SL: ₹{round(old_sl, 2)}\n"
        f"✅ New SL: ₹{round(new_sl, 2)}\n"
        f"🕐 Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    await send_msg(msg)

async def send_trailing_target_alert(sym, old_target, new_target, price):
    msg = (
        f"🚀 <b>TRAILING TARGET UPDATED — {sym}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📍 CMP: ₹{round(price, 2)}\n"
        f"🎯 Old Target: ₹{round(old_target, 2)}\n"
        f"✅ New Target: ₹{round(new_target, 2)}\n"
        f"🕐 Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    await send_msg(msg)

async def send_trade_closed_alert(sym, price, entry, pnl, reason):
    emoji = "✅" if pnl > 0 else "❌"
    msg = (
        f"{emoji} <b>TRADE CLOSED — {sym}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📌 Reason: {reason}\n"
        f"💸 Exit Price: ₹{round(price, 2)}\n"
        f"📥 Entry Price: ₹{round(entry, 2)}\n"
        f"📊 PnL: <b>{pnl}%</b>\n"
        f"🕐 Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    await send_msg(msg)

# ================= DATA =================
def fetch_all_data():
    try:
        return yf.download(
            NIFTY_MIDCAP_100 + [INDEX],
            period="10d",
            interval="1h",
            group_by="ticker",
            threads=True
        )
    except:
        return None

# ================= TREND FILTER =================
def get_market_trend(data):
    try:
        df = data.get("^NSEI")
        if df is None or df.empty:
            return "NEUTRAL"

        df = df.dropna()
        if len(df) < 60:
            return "NEUTRAL"

        df["EMA20"] = ta.ema(df["Close"], 20)
        df["EMA50"] = ta.ema(df["Close"], 50)
        df = df.dropna()

        if len(df) == 0:
            return "NEUTRAL"

        ema20 = df["EMA20"].iloc[-1]
        ema50 = df["EMA50"].iloc[-1]

        if pd.isna(ema20) or pd.isna(ema50):
            return "NEUTRAL"

        if ema20 > ema50:
            return "BULLISH"
        elif ema20 < ema50:
            return "BEARISH"
        else:
            return "NEUTRAL"
    except:
        return "NEUTRAL"

# ================= VIX =================
def get_vix():
    try:
        ticker = yf.Ticker("^INDIAVIX")
        v = ticker.history(period="1d", interval="1m")

        if v is None or v.empty:
            print("⚠️ VIX fallback used = 15")
            return 15

        return round(float(v["Close"].iloc[-1]), 2)

    except Exception as e:
        print(f"❌ VIX error: {e} | fallback = 15")
        return 15

# ================= 1H MACD FILTER =================
def check_1h_macd_ok(df_1h):
    """
    Returns True only if the 1H MACD is:
      1. NOT in a bearish cross → MACD line must be >= Signal line on last closed candle
    Histogram shrink condition removed — too strict for swing trading in trending markets.
    """
    try:
        df = df_1h.dropna()
        if len(df) < 30:
            return False

        macd_1h = ta.macd(df["Close"])
        if macd_1h is None or macd_1h.empty or len(macd_1h) < 3:
            return False

        # Use last fully closed candle (iloc[-2])
        macd_cur  = macd_1h["MACD_12_26_9"].iloc[-2]
        sig_cur   = macd_1h["MACDs_12_26_9"].iloc[-2]

        # FIX 3: Only check for bearish cross — drop histogram shrink condition.
        # In a bullish trend the histogram pulses up/down even as trend continues,
        # so requiring hist_cur >= hist_prev blocks too many valid setups.
        no_bearish_cross = macd_cur >= sig_cur

        return no_bearish_cross

    except:
        return False

# ================= STRATEGY =================
def analyze_stock(df, symbol, data_4h, trend):
    try:
        # FIX 5: Block entries outright when market is BEARISH
        if trend == "BEARISH":
            return None

        df = df.dropna()

        # MACD 4H
        df4h = get_df(data_4h, symbol)
        if df4h is None or df4h.empty:
            return None

        # FIX (RSI change): Use 4H RSI >= 50 instead of 1H RSI
        df4h_rsi = df4h.copy().dropna()
        df4h_rsi["RSI"] = ta.rsi(df4h_rsi["Close"], 14)
        df4h_rsi["ATR"] = ta.atr(df4h_rsi["High"], df4h_rsi["Low"], df4h_rsi["Close"], 14)

        # RSI >= 50
        rsi = df4h_rsi["RSI"].iloc[-1]
        if rsi < 50:
            return None

        # ATR still taken from 1H for SL/target sizing
        df["ATR"] = ta.atr(df["High"], df["Low"], df["Close"], 14)

        # ✅ NEW: 1H MACD FILTER
        # Block entry if 1H MACD has a bearish cross.
        # df here is already the 1H dataframe passed from main scan loop.
        if not check_1h_macd_ok(df):
            print(f"{symbol} | 1H MACD FILTER FAILED | bearish cross")
            return None

        macd = ta.macd(df4h["Close"])

        if macd is None or macd.empty or len(macd) < 4:
            return None

        # ✅ FIX 1: 4H CANDLE TIMESTAMP CHECK
        # Verify the last candle in 4H data is truly closed
        # by checking if current time is at least 4 hours past its open
        now_utc = datetime.now(timezone.utc)
        last_candle_time = df4h.index[-1]
        if last_candle_time.tzinfo is None:
            last_candle_time = last_candle_time.replace(tzinfo=timezone.utc)
        candle_age_seconds = (now_utc - last_candle_time).total_seconds()

        # If last candle is less than 4 hours old, it's still live
        # Shift all references back by 1 to ensure we only use closed candles
        if candle_age_seconds < 4 * 3600:
            # Last candle is still forming — shift all references back by 1
            vol_start_idx  = -28
            vol_end_idx    = -7
        else:
            # Last candle is closed — use standard references
            vol_start_idx  = -27
            vol_end_idx    = -6

        # FIX 1: Allow entry within 3 candles after bullish cross (was strictly 1 candle).
        # Scan backward through last 3 closed candles to find a valid bullish cross.
        # This catches crosses that happened 1, 2, or 3 candles ago — still actionable.
        cross_confirmed = False
        vol_cross_idx = -3  # default
        for lookback in range(0, 3):
            try:
                cur_macd   = macd.iloc[-(2 + lookback)]["MACD_12_26_9"]
                cur_signal = macd.iloc[-(2 + lookback)]["MACDs_12_26_9"]
                pre_macd   = macd.iloc[-(3 + lookback)]["MACD_12_26_9"]
                pre_signal = macd.iloc[-(3 + lookback)]["MACDs_12_26_9"]
                pre2_macd  = macd.iloc[-(4 + lookback)]["MACD_12_26_9"]
                pre2_signal= macd.iloc[-(4 + lookback)]["MACDs_12_26_9"]
                if (pre2_macd < pre2_signal and   # candle before cross: MACD below Signal
                    pre_macd  > pre_signal  and   # cross candle: MACD crossed above Signal
                    cur_macd  > cur_signal):       # candle after cross: MACD holding above Signal
                    cross_confirmed = True
                    # Re-align volume index to the actual cross candle found
                    vol_cross_idx = -(3 + lookback)
                    break
            except:
                continue

        print(f"{symbol} | cross_confirmed={cross_confirmed}")

        if not cross_confirmed:
            return None

        # ✅ FIX 2: MACD OVEREXTENSION FILTER
        # Raise threshold to 2.5x std in BULLISH market (was 1.5x always).
        # In a trending market, MACD is naturally elevated — 1.5x blocked valid setups.
        macd_history = macd["MACD_12_26_9"].iloc[-50:]
        macd_std = macd_history.std()
        macd_at_cross = macd.iloc[vol_cross_idx]["MACD_12_26_9"]

        overext_threshold = 2.5 if trend == "BULLISH" else 1.5
        if macd_at_cross > overext_threshold * macd_std:
            print(f"{symbol} | MACD OVEREXTENSION FILTER FAILED | MACD@Cross={round(macd_at_cross, 2)} | {overext_threshold}*STD={round(overext_threshold * macd_std, 2)}")
            return None

        # ================= VOLUME FILTER =================
        # MACD cross candle volume must be above 20-period average.
        # vol_cross_idx is now aligned to the actual cross candle found above.
        df4h_clean = df4h.dropna(subset=["Volume"])
        if len(df4h_clean) < 21:
            return None

        vol_20_avg = df4h_clean["Volume"].iloc[vol_start_idx:vol_end_idx].mean()
        cross_candle_volume = df4h_clean["Volume"].iloc[vol_cross_idx]

        if cross_candle_volume <= vol_20_avg:
            print(f"{symbol} | VOLUME FILTER FAILED | CrossVol={cross_candle_volume:.0f} | Avg20={vol_20_avg:.0f}")
            return None

        print(f"{symbol} | VOLUME FILTER PASSED | CrossVol={cross_candle_volume:.0f} | Avg20={vol_20_avg:.0f}")
        # =================================================

        price = float(df["Close"].iloc[-1])

        # ✅ INCREASED SL to 2.5x ATR (was 1.5x) to cover pullbacks.
        # Target raised to 5.0x ATR (was 3.0x) to maintain strict 1:2 R:R.
        atr_val = float(df["ATR"].iloc[-1])
        sl_distance = 2.5 * atr_val
        target_distance = sl_distance * 2  # Enforces 1:2 R:R minimum (= 5.0x ATR)

        return {
            "Ticker": symbol.replace(".NS", ""),
            "CMP": price,
            "Target": price + target_distance,  # 5.0x ATR above entry
            "SL": price - sl_distance,           # 2.5x ATR below entry
            "EntryTime": datetime.now(timezone.utc).isoformat(),
            "HighSinceEntry": price,             # High watermark for trailing target
            "EntryATR": atr_val                  # Lock ATR at entry for consistent trailing
        }

    except Exception as e:

        print(f"❌ ERROR in {symbol}: {e}")

        return None

# ================= WIN RATE =================
def calculate_win_rate(history):
    try:
        valid_trades = []

        for t in history:
            if isinstance(t, dict) and "PnL" in t:
                try:
                    valid_trades.append(float(t["PnL"]))
                except:
                    continue

        if len(valid_trades) == 0:
            return 0

        wins = sum(1 for p in valid_trades if p > 0)
        return round((wins / len(valid_trades)) * 100, 2)

    except:
        return 0

# ================= MAIN =================
async def main():

    await send_msg("📊 <b>Swing Bot Started (MIDCAP 100)</b>")

    while True:

        data = fetch_all_data()
        data_4h = yf.download(
            NIFTY_MIDCAP_100,
            period="3mo",
            interval="4h",
            group_by="ticker",
            threads=True
        )
        print("STEP 1:", data is None)
        print("STEP 2:", data.empty)
        print("STEP 3:", len(data.columns.levels[0]))
        if data is None:
            await asyncio.sleep(1800)
            continue

        trend = get_market_trend(data)
        vix = get_vix()

        active = load_json(TRADES_FILE, {})
        history = load_json(HISTORY_FILE, [])
        signals = load_json(SIGNAL_FILE, {})

        # ================= MONITOR =================
        for sym in list(active.keys()):
            try:
                df = get_df(data, sym)
                if df is None or df.empty:
                    continue

                trade = active[sym]
                price = float(df["Close"].iloc[-1])
                entry = trade["CMP"]

                # Check all candles since trade entry — catches any missed highs/lows during sleep
                entry_time = pd.Timestamp(trade["EntryTime"]).tz_convert("UTC")
                df_since_entry = df[df.index >= entry_time]
                if df_since_entry.empty:
                    df_since_entry = df.tail(1)

                candle_high = float(df_since_entry["High"].max())
                candle_low = float(df_since_entry["Low"].min())

                atr = ta.atr(df["High"], df["Low"], df["Close"], 14).iloc[-1]

                # ✅ POINT 3: Check SL using candle LOW (catches intra-candle SL hits)
                if candle_low <= trade["SL"]:
                    exit_price = trade["SL"]
                    pnl = round(((exit_price - entry) / entry) * 100, 2)
                    await send_stoploss_hit_alert(sym, exit_price, trade["SL"], entry, pnl)
                    await send_trade_closed_alert(sym, exit_price, entry, pnl, "Stoploss Hit")
                    history.append({"Ticker": sym, "PnL": pnl})
                    # ✅ POINT 2: Safe signal delete — handles both string and dict formats
                    if sym in signals:
                        del signals[sym]
                    del active[sym]
                    continue

                # ✅ POINT 3: Check Target using candle HIGH (catches intra-candle target hits)
                elif candle_high >= trade["Target"]:
                    exit_price = trade["Target"]
                    pnl = round(((exit_price - entry) / entry) * 100, 2)
                    await send_target_hit_alert(sym, exit_price, trade["Target"], entry, pnl)
                    await send_trade_closed_alert(sym, exit_price, entry, pnl, "Target Hit")
                    history.append({"Ticker": sym, "PnL": pnl})
                    # ✅ POINT 2: Safe signal delete — handles both string and dict formats
                    if sym in signals:
                        del signals[sym]
                    del active[sym]
                    continue

                # ✅ INCREASED trailing SL to 2.5x ATR (was 1.5x) to match wider initial SL.
                # Buffer raised to 0.5x ATR (was 0.3x) to avoid excessive trailing noise.
                new_sl = price - (2.5 * atr)
                if new_sl > trade["SL"] + (0.5 * atr):
                    await send_trailing_sl_alert(sym, trade["SL"], new_sl, price)
                    trade["SL"] = new_sl

                # ✅ TRAILING TARGET: High watermark approach.
                # Track the highest price seen since entry. Trail target from that high,
                # not from current price — target only ever moves up, never oscillates.
                if price > trade.get("HighSinceEntry", trade["CMP"]):
                    trade["HighSinceEntry"] = price

                high = trade["HighSinceEntry"]
                entry_atr = trade.get("EntryATR", atr)  # Use locked ATR from entry, not live ATR
                new_target = high + (2.5 * entry_atr * 2)  # Keep same 1:2 R:R on extension
                if new_target > trade["Target"]:
                    await send_trailing_target_alert(sym, trade["Target"], new_target, price)
                    trade["Target"] = new_target

                active[sym] = trade

            except:
                pass

        save_json(active, TRADES_FILE)
        save_json(history, HISTORY_FILE)
        save_json(signals, SIGNAL_FILE)

        # ================= SCAN =================
        win_rate = calculate_win_rate(history)

        msg = (
            f"📊 <b>Swing Scan Results (MIDCAP 100)</b>\n"
            f"📈 Market: {trend}\n"
            f"🎢 Volatility Index: {vix}\n"
            f"🏆 Win Rate: {win_rate}%\n"
            f"━━━━━━━━━━━━━━\n"
        )

        setups = 0

        daily = get_daily_entry_count()

        for ticker in NIFTY_MIDCAP_100:

            if daily["count"] >= MAX_DAILY_ENTRIES:
                break

            sym = ticker.replace(".NS", "")

            if sym in active:
                continue

            df = get_df(data, ticker)
            if df is None:
                continue

            res = analyze_stock(df, ticker, data_4h, trend)

            if res:

                sym = ticker.replace(".NS", "")

                # ✅ POINT 2: Safe signal deduplication — handles both string and dict formats
                if sym in signals:
                    if isinstance(signals[sym], str) and signals[sym] == "ACTIVE":
                        continue
                    elif isinstance(signals[sym], dict) and signals[sym].get("status") == "ACTIVE":
                        continue

                active[sym] = res
                setups += 1
                signals[sym] = "ACTIVE"
                increment_daily_entry_count()
                daily = get_daily_entry_count()

                msg += (
                    f"\n📈 <b>{sym}</b>\n"
                    f"➡️ Entry: ₹{round(res['CMP'], 2)}\n"
                    f"🎯 Target: ₹{round(res['Target'], 2)}\n"
                    f"⛔ SL: ₹{round(res['SL'], 2)}\n"
                )

        if setups == 0:
            msg += "\nNo setups found / 5 setups/day limit reached"
        save_json(active, TRADES_FILE)
        save_json(history, HISTORY_FILE)
        save_json(signals, SIGNAL_FILE)

        await send_msg(msg)

        logging.info("Scan complete. Sleeping 30 minutes...")
        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(main())
